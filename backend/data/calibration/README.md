# Human Calibration Dataset

This directory contains human-labeled audio samples for calibrating deepfake detection thresholds.

## Directory Structure

```
calibration/
├── real/           # Audio confirmed as genuine human speech
├── synthetic/      # Audio confirmed as AI-generated
├── unsure/         # Ambiguous cases for review
└── README.md       # This file
```

## Listening Workflow

### Step 1: Collect Samples

```bash
# Copy samples you want to evaluate
cp /path/to/audio/*.wav backend/data/calibration/
```

### Step 2: Run Interactive Annotation

```bash
cd backend
python scripts/human_annotate.py --audio-dir data/calibration --interactive
```

### Step 3: Listen and Label

For each sample, the tool will:
1. Run the detection algorithm
2. Show sensor results
3. Play the audio (if player available)
4. Ask for your verdict (REAL/SYNTHETIC/UNSURE)
5. Ask which artifacts you heard

### Step 4: Review Results

```bash
# View your annotations
cat human_annotations.jsonl | python -m json.tool

# Count by verdict
grep -c '"human_verdict": "REAL"' human_annotations.jsonl
grep -c '"human_verdict": "SYNTHETIC"' human_annotations.jsonl
```

### Step 5: Optimize Thresholds

```bash
# Run threshold optimizer on your labeled data
python calibration/optimizer.py --dataset data/calibration --output new_thresholds.json
```

### Step 6: Evaluate Changes

```bash
# Create metadata file
echo "file,label" > data/calibration/metadata.csv
for f in data/calibration/real/*.wav; do echo "$(basename $f),bonafide" >> data/calibration/metadata.csv; done
for f in data/calibration/synthetic/*.wav; do echo "$(basename $f),spoof" >> data/calibration/metadata.csv; done

# Run evaluation
python scripts/eval_liveness.py \
  --dataset-dir data/calibration \
  --metadata-file data/calibration/metadata.csv \
  --output-dir eval_results
```

## Artifact Types to Listen For

| Artifact | What to Hear | Sensor |
|----------|--------------|--------|
| **Two-Mouth** | Two voices overlapping, morphing quality | TwoMouthSensor |
| **Hard Attack** | Words start too fast, no breath burst | GlottalInertiaSensor |
| **Hard Decay** | Words end abruptly, no room reverb | GlottalInertiaSensor |
| **Infinite Lung** | Speech >15s without breathing | BreathSensor |
| **Robotic Transitions** | Choppy phonemes, concatenated feel | CoarticulationSensor |
| **Metallic Phase** | Hollow, vocoder-like quality | PhaseCoherenceSensor |
| **Spliced Silence** | Perfect digital silence between words | DigitalSilenceSensor |
| **Formant Jump** | Sudden pitch changes, frequency glitches | FormantTrajectorySensor |

## Tips for Effective Listening

1. **Use headphones** - Small artifacts are easier to hear
2. **Listen multiple times** - First pass for overall impression, second for artifacts
3. **Focus on word boundaries** - Attack/decay artifacts are most obvious here
4. **Note timestamps** - Record when you hear specific artifacts
5. **Trust your ears** - If something sounds "off", it probably is

## Annotation File Format

Each annotation in `human_annotations.jsonl` contains:

```json
{
  "audio_file": "path/to/file.wav",
  "timestamp": "2025-12-09T10:30:00",
  "human_verdict": "SYNTHETIC",
  "confidence": "HIGH",
  "artifacts_heard": ["hard_attack", "two_mouth"],
  "artifact_timestamps": {
    "hard_attack": "0:02-0:03",
    "two_mouth": "throughout"
  },
  "algorithm_verdict": "REAL",
  "algorithm_score": 0.25,
  "agrees_with_algorithm": false,
  "disagreement_notes": "Heard clear onset artifacts algorithm missed",
  "notes": "Very subtle but audible morphing quality"
}
```

## Feedback Loop

```
Listen → Annotate → Optimize → Evaluate → Repeat
   ↑                                    |
   +------------------------------------+
```

Your annotations improve the algorithm over time!
