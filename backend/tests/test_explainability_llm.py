
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.detection.stages.explainability import ExplainabilityStage

def test_llm_integration():
    print("Initializing ExplainabilityStage with LLM enabled...")
    
    # Ensure token is present (warn if not)
    if not os.getenv("HUGGINGFACE_TOKEN"):
        print("WARNING: HUGGINGFACE_TOKEN not found in env. Test may fail or fallback.")

    stage = ExplainabilityStage(
        enable_llm=True,
        llm_model_id="mistralai/Mistral-7B-Instruct-v0.3"
    )
    
    # Mock Data: Strong Deepfake Signature
    fusion_result = {
        "fused_score": 0.92,
        "decision": "SPOOF_HIGH",
        "confidence": 0.95
    }
    
    stage_results = {
        "physics_analysis": {
            "sensor_results": {
                "Breath Sensor": {"score": 0.95, "passed": False, "metadata": {"details": "No respiration detected"}},
                "Phase Coherence": {"score": 0.1, "passed": False, "metadata": {"details": "Perfect phase alignment (Vocoder artifact)"}}
            }
        },
        "rawnet3": {
            "score": 0.98,
            "demo_mode": False
        }
    }
    
    print("\nQuerying Mixtral via Hugging Face API...")
    result = stage.process(stage_results, fusion_result)
    
    print("\n--- LLM RESULT ---")
    print(f"Summary: {result.get('summary')}")
    print("\nReasoning Chain:")
    for step in result.get("reasoning_chain", []):
        print(f"- {step}")
        
    # Validation
    summary = result.get('summary', '')
    if "expert" in summary.lower() or "detect" in summary.lower() or "fake" in summary.lower():
        print("\nSUCCESS: LLM generated a relevant summary.")
    else:
        print("\nWARNING: Summary might be heuristic fallback.")

if __name__ == "__main__":
    test_llm_integration()
