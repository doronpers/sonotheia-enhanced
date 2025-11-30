# Sonotheia MVP - Voice Deepfake Detection

## Overview

This is the minimal viable product (MVP) for Sonotheia - a telephony-aware voice deepfake detection system. The MVP implements:

- **Telephony codec simulation** (landline, mobile, VoIP)
- **Physics-based acoustic features** (LFCC, CQCC, log-spectrogram)
- **Baseline spoof detection** (GMM-based classifier)
- **Factor-level risk scoring** (physics + placeholders for ASV/liveness)
- **SAR-style narrative generation**
- **Simple web UI** (Streamlit)
- **Benchmark harness** for evaluation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI                          │
│           (Audio Upload & Visualization)                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend                            │
│          /api/analyze_call Endpoint                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Analysis Pipeline                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Audio Load   │→ │ Telephony    │→ │ Feature      │  │
│  │ (WAV)        │  │ Codec        │  │ Extraction   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                            ↓                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Spoof        │→ │ Risk Engine  │→ │ SAR          │  │
│  │ Detection    │  │ (Factors)    │  │ Generation   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
backend/
├── data_ingest/           # Audio loading and metadata
│   └── loader.py
├── telephony/             # Codec simulation
│   └── pipeline.py
├── features/              # Feature extraction
│   └── extraction.py
├── models/                # Spoof detection models
│   └── baseline.py
├── evaluation/            # Metrics and experiments
│   ├── codec_experiments.py
│   └── metrics.py
├── risk_engine/           # Factor-level risk scoring
│   └── factors.py
├── api/                   # FastAPI endpoints
│   ├── main.py
│   └── analyze_call.py
├── ui/                    # Streamlit UI
│   └── streamlit_app.py
└── scripts/               # Training and benchmarking
    ├── train_baseline.py
    ├── run_benchmark.py
    └── benchmark_config.yaml
```

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import librosa, soundfile, torch, numpy, scipy; print('All dependencies installed!')"
```

## Quick Start

### 1. Start the FastAPI Backend

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 2. Start the Streamlit UI

In a separate terminal:

```bash
cd backend
streamlit run ui/streamlit_app.py
```

The UI will open in your browser at http://localhost:8501

### 3. Analyze a Call

1. Upload a WAV file in the Streamlit UI
2. Enter call metadata (call ID, customer ID, etc.)
3. Select codec type (landline, mobile, voip, clean)
4. Click "Analyze Call"
5. View results:
   - Risk score and level
   - Factor breakdown
   - Waveform and spectrogram
   - SAR narrative (if high risk)

## API Usage

### Analyze Call Endpoint

**POST** `/api/analyze_call`

Upload an audio file and get complete analysis.

**Example using curl:**

```bash
curl -X POST "http://localhost:8000/api/analyze_call" \
  -F "audio_file=@call.wav" \
  -F "call_id=CALL-001" \
  -F "customer_id=CUST-12345" \
  -F "transaction_id=TXN-001" \
  -F "amount_usd=50000" \
  -F "destination_country=US" \
  -F "channel=phone" \
  -F "codec=landline"
```

**Example using Python:**

```python
import requests

files = {'audio_file': open('call.wav', 'rb')}
data = {
    'call_id': 'CALL-001',
    'customer_id': 'CUST-12345',
    'codec': 'landline'
}

response = requests.post('http://localhost:8000/api/analyze_call', files=files, data=data)
result = response.json()

print(f"Risk Score: {result['risk_result']['overall_score']}")
print(f"Risk Level: {result['risk_result']['risk_level']}")
print(f"Decision: {result['risk_result']['decision']}")
```

## Training a Model

To train the baseline GMM spoof detector on your own data:

### 1. Prepare Dataset

Create a directory with:
- Audio files (WAV format, 16kHz recommended)
- `metadata.csv` with columns: `file_path`, `label`
  - `label`: 0 = genuine, 1 = spoof

Example `metadata.csv`:
```csv
file_path,label
genuine/sample1.wav,0
genuine/sample2.wav,0
spoof/sample1.wav,1
spoof/sample2.wav,1
```

### 2. Train Model

```bash
python scripts/train_baseline.py \
  --dataset-dir ./data \
  --metadata-file metadata.csv \
  --codec landline \
  --output ./models/gmm_spoof_detector.pkl \
  --n-components 32
```

### 3. Use Trained Model

The `/api/analyze_call` endpoint will automatically use the trained model if you update the `CallAnalyzer` initialization with the model path.

## Running Benchmarks

### 1. Prepare Config

Edit `scripts/benchmark_config.yaml`:

```yaml
dataset_dir: "./data"
metadata_file: "metadata.csv"
output_dir: "./benchmark_results"
model_path: "./models/gmm_spoof_detector.pkl"

feature_types:
  - "lfcc"
  - "logspec"

codecs:
  - "landline"
  - "mobile"
  - "voip"
  - "clean"
```

### 2. Run Codec Experiments

```bash
python scripts/run_benchmark.py scripts/benchmark_config.yaml --codec-experiments
```

This will:
- Test spoof detection under different codec conditions
- Generate EER and AUC metrics for each codec
- Save results to JSON

### 3. Run Full Evaluation

```bash
python scripts/run_benchmark.py scripts/benchmark_config.yaml --full-eval
```

This will:
- Compute all metrics (accuracy, precision, recall, F1, AUC, EER)
- Generate ROC curves
- Generate score distribution plots
- Save everything to the output directory

## Components

### Telephony Codec Simulation

```python
from telephony.pipeline import TelephonyPipeline

pipeline = TelephonyPipeline()

# Apply different codecs
audio_landline = pipeline.apply_landline_chain(audio, sr)
audio_mobile = pipeline.apply_mobile_chain(audio, sr)
audio_voip = pipeline.apply_voip_chain(audio, sr)
```

### Feature Extraction

```python
from features.extraction import FeatureExtractor

extractor = FeatureExtractor(sr=16000)

# Extract individual features
lfcc = extractor.extract_lfcc(audio)
cqcc = extractor.extract_cqcc(audio)
logspec = extractor.extract_logspec(audio)

# Extract stacked features
features = extractor.extract_feature_stack(audio, feature_types=['lfcc', 'logspec'])
```

### Spoof Detection

```python
from models.baseline import GMMSpoofDetector

# Create detector
detector = GMMSpoofDetector(n_components=32)

# Train
detector.train(genuine_features, spoof_features)

# Predict
spoof_score = detector.predict_score(features)  # 0-1, higher = more likely spoof
```

### Risk Engine

```python
from risk_engine.factors import RiskEngine, FactorScore

# Create factors
physics_factor = RiskEngine.create_physics_factor(
    spoof_score=0.25,
    codec_name='landline',
    threshold=0.30
)

asv_factor = RiskEngine.create_asv_factor(score=0.15)
liveness_factor = RiskEngine.create_liveness_factor(score=0.10)

# Compute overall risk
factors = [physics_factor, asv_factor, liveness_factor]
risk_result = RiskEngine.compute_overall_risk(factors)

print(f"Overall Risk: {risk_result.overall_score}")
print(f"Risk Level: {risk_result.risk_level}")
print(f"Decision: {risk_result.decision}")
```

## Codec Details

### Landline (PSTN)
- Bandpass filter: 300-3400 Hz
- A-law quantization (8-bit)
- Simulates traditional telephone network

### Mobile (Cellular)
- Bandpass filter: 200-3800 Hz
- μ-law quantization (8-bit)
- Slightly wider bandwidth than landline

### VoIP
- Bandpass filter: 50-7000 Hz (wideband)
- μ-law quantization
- Packet loss simulation (2% default)
- Better quality than PSTN

### Clean
- No codec effects applied
- Original audio preserved

## Feature Types

### LFCC (Linear Frequency Cepstral Coefficients)
- Linear frequency scale (vs. mel scale in MFCC)
- Better for spoof detection
- Default: 20 coefficients

### CQCC (Constant-Q Cepstral Coefficients)
- Uses Constant-Q Transform
- Good for music and tonal features
- Default: 20 coefficients

### Log-Spectrogram
- Log-magnitude STFT
- Full spectral information
- High dimensional

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the `backend` directory:

```bash
cd backend
python -m scripts.train_baseline --help
```

Or add the backend directory to PYTHONPATH:

```bash
export PYTHONPATH=/path/to/sonotheia-enhanced/backend:$PYTHONPATH
```

### Model Not Found

If the API returns placeholder scores, it means no trained model is loaded. Either:
1. Train a model using `train_baseline.py`
2. The system will use heuristic placeholder scores (for demo purposes)

### Memory Issues

If you run out of memory with large datasets:
- Use `--max-samples` flag in training script
- Process files in smaller batches
- Use fewer GMM components (`--n-components 16`)

## Future Enhancements

This MVP provides the foundation. Future enhancements include:

1. **Real ASV (Speaker Verification)** - Replace placeholder with actual speaker verification
2. **Real Liveness Detection** - Implement active liveness challenges
3. **Deep Learning Models** - Add CNN/ResNet for better performance
4. **Model Ensemble** - Combine multiple detection approaches
5. **Real-time Processing** - Streaming audio analysis
6. **Database Integration** - Store results and audit logs
7. **Advanced SAR Templates** - More sophisticated narrative generation

## Citation

If you use this system, please cite:

```
Sonotheia MVP - Telephony-Aware Voice Deepfake Detection
https://github.com/doronpers/sonotheia-enhanced
```

## License

Proprietary - See LICENSE file for details
