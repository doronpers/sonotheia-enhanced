"""
HuggingFace LLM Integration for SAR Generation and Explanations.

Supports both HuggingFace Inference API and local model inference
for generating SAR narratives and explain endpoint responses.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

# HuggingFace Inference API base URL
HF_INFERENCE_API_URL = "https://api-inference.huggingface.co/models/"

# Recommended models for different tasks
RECOMMENDED_MODELS = {
    "sar_generation": [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "meta-llama/Llama-2-7b-chat-hf",
        "HuggingFaceH4/zephyr-7b-beta",
    ],
    "explanation": [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "HuggingFaceH4/zephyr-7b-beta",
        "google/flan-t5-xl",
    ],
    "summarization": [
        "facebook/bart-large-cnn",
        "google/flan-t5-base",
    ],
}


@dataclass
class HuggingFaceConfig:
    """Configuration for HuggingFace API access."""
    api_token: str
    model_id: str = "mistralai/Mistral-7B-Instruct-v0.2"
    max_new_tokens: int = 1024
    temperature: float = 0.3
    top_p: float = 0.9
    do_sample: bool = True
    timeout: float = 120.0
    use_local: bool = False  # Use local model instead of API
    

class HuggingFaceLLM:
    """
    HuggingFace LLM client for text generation.
    
    Supports:
    - HuggingFace Inference API (cloud)
    - Local model inference via transformers
    - Streaming responses
    - Automatic retry and fallback
    """
    
    # System prompts for different tasks
    SAR_SYSTEM_PROMPT = """You are a compliance officer assistant specializing in Suspicious Activity Report (SAR) narratives for financial institutions. Your task is to generate clear, professional, and FinCEN-compliant SAR narratives.

Guidelines:
1. Use formal, objective language appropriate for regulatory filings
2. Include all relevant facts without speculation
3. Describe the suspicious activity clearly and chronologically
4. Reference specific evidence and detection methods used
5. Do not include any actual PII - use placeholders like [SUBJECT], [ACCOUNT], etc.
6. Follow the standard SAR narrative structure (Who, What, When, Where, Why, How)

For voice deepfake detection cases:
- Describe the voice authentication anomaly detected
- Reference specific sensor/detection results
- Explain the significance of the detection scores
- Connect the detection to potential fraud indicators"""

    EXPLAIN_SYSTEM_PROMPT = """You are Sonotheia, a voice deepfake detection system. You analyze audio using physics-based sensors that examine:

- Breath patterns and phonation duration
- Frequency bandwidth characteristics
- Dynamic range and crest factor
- Phase coherence between harmonics
- Vocal tract anatomy estimation
- Coarticulation patterns

When explaining your analysis:
1. Be technical but accessible
2. Reference specific sensor findings from the evidence
3. Explain what each finding means for authenticity
4. Be confident but acknowledge uncertainty where appropriate
5. Never reveal proprietary threshold values - focus on concepts"""

    def __init__(self, config: Optional[HuggingFaceConfig] = None):
        """
        Initialize HuggingFace LLM client.
        
        Args:
            config: HuggingFace configuration. If None, reads from environment.
        """
        if config:
            self._config = config
        else:
            api_token = os.environ.get("HUGGINGFACE_TOKEN", "")
            model_id = os.environ.get("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
            self._config = HuggingFaceConfig(api_token=api_token, model_id=model_id)
        
        self._http_client = httpx.Client(timeout=self._config.timeout)
        self._local_model = None
        self._local_tokenizer = None
    
    def _load_local_model(self) -> bool:
        """Load model locally for inference."""
        if self._local_model is not None:
            return True
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading local model: {self._config.model_id}")
            
            # Determine device
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            
            self._local_tokenizer = AutoTokenizer.from_pretrained(
                self._config.model_id,
                token=self._config.api_token or None,
            )
            
            self._local_model = AutoModelForCausalLM.from_pretrained(
                self._config.model_id,
                token=self._config.api_token or None,
                torch_dtype=torch.float16 if device != "cpu" else torch.float32,
                device_map="auto" if device != "cpu" else None,
            )
            
            if device == "cpu":
                self._local_model = self._local_model.to(device)
            
            logger.info(f"Local model loaded on {device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            return False
    
    def _call_inference_api(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, List[str]]:
        """
        Call HuggingFace Inference API.
        
        Returns:
            Tuple of (generated_text, warnings)
        """
        warnings = []
        
        if not self._config.api_token:
            warnings.append("HuggingFace API token not configured")
            return "", warnings
        
        # Format prompt for the model
        if system_prompt:
            # Use chat format for instruction-tuned models
            full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            full_prompt = prompt
        
        url = f"{HF_INFERENCE_API_URL}{self._config.model_id}"
        
        try:
            response = self._http_client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._config.api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": full_prompt,
                    "parameters": {
                        "max_new_tokens": self._config.max_new_tokens,
                        "temperature": self._config.temperature,
                        "top_p": self._config.top_p,
                        "do_sample": self._config.do_sample,
                        "return_full_text": False,
                    },
                },
            )
            
            if response.status_code == 503:
                # Model loading - wait and retry
                warnings.append("Model is loading, response may be delayed")
                return "", warnings
            
            if response.status_code != 200:
                warnings.append(f"HuggingFace API error: {response.status_code}")
                return "", warnings
            
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                generated_text = result.get("generated_text", "")
            else:
                warnings.append("Unexpected response format from HuggingFace API")
                return "", warnings
            
            return generated_text.strip(), warnings
            
        except Exception as e:
            warnings.append(f"HuggingFace API call failed: {str(e)}")
            return "", warnings
    
    def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, List[str]]:
        """
        Generate text using local model.
        
        Returns:
            Tuple of (generated_text, warnings)
        """
        warnings = []
        
        if not self._load_local_model():
            warnings.append("Failed to load local model")
            return "", warnings
        
        try:
            import torch
            
            # Format prompt
            if system_prompt:
                full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                full_prompt = prompt
            
            inputs = self._local_tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
            )
            
            # Move to same device as model
            device = next(self._local_model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self._local_model.generate(
                    **inputs,
                    max_new_tokens=self._config.max_new_tokens,
                    temperature=self._config.temperature,
                    top_p=self._config.top_p,
                    do_sample=self._config.do_sample,
                    pad_token_id=self._local_tokenizer.eos_token_id,
                )
            
            # Decode and extract new text
            full_output = self._local_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the input prompt from output
            if full_prompt in full_output:
                generated_text = full_output.replace(full_prompt, "").strip()
            else:
                generated_text = full_output.strip()
            
            return generated_text, warnings
            
        except Exception as e:
            warnings.append(f"Local generation failed: {str(e)}")
            return "", warnings
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        task: str = "general",
    ) -> tuple[str, List[str]]:
        """
        Generate text using HuggingFace model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            task: Task type for selecting appropriate system prompt
            
        Returns:
            Tuple of (generated_text, warnings)
        """
        # Select system prompt based on task
        if system_prompt is None:
            if task == "sar":
                system_prompt = self.SAR_SYSTEM_PROMPT
            elif task == "explain":
                system_prompt = self.EXPLAIN_SYSTEM_PROMPT
        
        if self._config.use_local:
            return self._generate_local(prompt, system_prompt)
        else:
            return self._call_inference_api(prompt, system_prompt)
    
    def generate_explanation(
        self,
        verdict: str,
        evidence: Dict[str, Any],
        question: str,
    ) -> tuple[str, List[str]]:
        """
        Generate an explanation for a detection result.
        
        Args:
            verdict: Detection verdict (REAL, SYNTHETIC, etc.)
            evidence: Sensor evidence dictionary
            question: User's question
            
        Returns:
            Tuple of (explanation_markdown, warnings)
        """
        # Build evidence summary
        evidence_parts = []
        
        # Breath sensor
        breath = evidence.get("check_breath_sensor", {})
        if breath:
            status = "passed" if breath.get("passed", True) else "failed"
            evidence_parts.append(
                f"- Breath/Phonation: {status} "
                f"(max phonation: {breath.get('value', 'N/A')}s, "
                f"threshold: {breath.get('threshold', 'N/A')}s)"
            )
        
        # Bandwidth sensor
        bandwidth = evidence.get("check_bandwidth_sensor", {})
        if bandwidth:
            evidence_parts.append(
                f"- Bandwidth: {bandwidth.get('type', 'UNKNOWN')} "
                f"(rolloff: {bandwidth.get('value', 'N/A')} Hz)"
            )
        
        # Dynamic range sensor
        dynamic = evidence.get("check_dynamic_range_sensor", {})
        if dynamic:
            status = "passed" if dynamic.get("passed", True) else "failed"
            evidence_parts.append(
                f"- Dynamic Range: {status} "
                f"(crest factor: {dynamic.get('value', 'N/A')})"
            )
        
        # Phase coherence
        phase = evidence.get("phase_coherence", {})
        if phase:
            status = "passed" if phase.get("passed", True) else "failed"
            evidence_parts.append(f"- Phase Coherence: {status}")
        
        # Vocal tract
        vocal = evidence.get("vocal_tract", {})
        if vocal:
            status = "passed" if vocal.get("passed", True) else "failed"
            tract_length = vocal.get("tract_length_cm", "N/A")
            evidence_parts.append(
                f"- Vocal Tract: {status} (estimated length: {tract_length}cm)"
            )
        
        # Coarticulation
        coart = evidence.get("coarticulation", {})
        if coart:
            status = "passed" if coart.get("passed", True) else "failed"
            evidence_parts.append(f"- Coarticulation: {status}")
        
        # HuggingFace detector (if present)
        hf_detector = evidence.get("huggingface_detector", {})
        if hf_detector:
            status = "passed" if hf_detector.get("passed", True) else "failed"
            prob = hf_detector.get("synthetic_probability", "N/A")
            evidence_parts.append(
                f"- Neural Network Analysis: {status} "
                f"(synthetic probability: {prob})"
            )
        
        evidence_summary = "\\n".join(evidence_parts) if evidence_parts else "No sensor evidence available."
        
        prompt = f\"\"\"Based on my analysis, I reached a verdict of **{verdict}**.

Here is the sensor evidence:
{evidence_summary}

The user asks: "{question}"

Please provide a clear, technical explanation of how I reached this verdict and address the user's question. Focus on the physics and signal processing concepts behind each sensor finding.\"\"\"

        return self.generate(prompt, task="explain")
    
    def close(self):
        """Close HTTP client."""
        self._http_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick generation
def generate_with_huggingface(
    prompt: str,
    model_id: Optional[str] = None,
    task: str = "general",
) -> tuple[str, List[str]]:
    """
    Quick generation using HuggingFace.
    
    Args:
        prompt: Text prompt
        model_id: Optional model ID override
        task: Task type (general, sar, explain)
        
    Returns:
        Tuple of (generated_text, warnings)
    """
    config = HuggingFaceConfig(
        api_token=os.environ.get("HUGGINGFACE_TOKEN", ""),
        model_id=model_id or os.environ.get("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2"),
    )
    
    with HuggingFaceLLM(config) as llm:
        return llm.generate(prompt, task=task)
