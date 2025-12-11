import { useRef, useState } from "react";
import DetectorChat from "./DetectorChat";
import { LockIcon, ShieldIcon } from "./icons/SecurityIcons";
import { apiBase } from "../config";

/**
 * Format verdict text for display by replacing underscores with spaces.
 * Example: "TOO_SHORT" becomes "TOO SHORT"
 */
const formatVerdict = (verdict) => {
  if (!verdict) return "";
  return verdict.replace(/_/g, " ");
};

const SENSOR_HELP = {
  "Bandwidth Type": "Synthetic voices often collapse into narrowband telephone ranges.",
  "Dynamic Range (Crest Factor)": "Human speech contains natural peaks that clones struggle to recreate.",
  "Breath Sensor (Max Phonation)": "Extended single-breath phrases can signal concatenated or spliced speech.",
  "Phase Coherence": "Phase drift and entropy analysis exposes vocoder artifacts.",
  "Glottal Inertia": "Detects impossible amplitude rise velocities that violate vocal fold physics.",
  "Global Formants": "Analyzes long-term spectral envelope statistics for robotic consistency.",
  "Digital Silence": "Detects perfect zeros or unnatural noise floor changes indicating splicing.",
  "Coarticulation": "Authentic speech blends phonemes; rigid transitions hint at synthesis.",
  "Huggingface Detector": "Neural network analysis using wav2vec2 transformer models for deepfake detection.",
};

const Demo = () => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [uploadProgress, setUploadProgress] = useState("");
  const verdictExplainers = {
    REAL: "Natural microphone variance detected across bandwidth, breath, and crest-factor sensors.",
    SYNTHETIC: "Multiple sensors flagged mechanically even dynamics indicative of cloned or concatenated speech.",
    UNKNOWN: "Audio lacked enough signal-to-noise to make a determination; try a longer clip if available.",
  };

  const triggerFileDialog = () => inputRef.current?.click();

  const handleFiles = (files) => {
    const file = files?.[0];
    if (!file) {
      return;
    }

    // Validate file type
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/m4a', 'audio/x-m4a', 'audio/ogg', 'audio/flac'];
    const fileType = file.type || '';
    const fileName = file.name.toLowerCase();
    const isValidType = validTypes.some(type => fileType.includes(type)) || 
                       fileName.endsWith('.wav') || fileName.endsWith('.mp3') || 
                       fileName.endsWith('.m4a') || fileName.endsWith('.ogg') || fileName.endsWith('.flac');
    
    if (!isValidType) {
      setError("Invalid file type. Please upload a WAV, MP3, M4A, OGG, or FLAC audio file.");
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError(`File size exceeds 10MB limit. Your file is ${(file.size / 1024 / 1024).toFixed(2)}MB.`);
      return;
    }

    setUploading(true);
    setResult(null);
    setError("");
    setUploadProgress("Uploading file...");

    const formData = new FormData();
    formData.append("file", file);

    fetch(`${apiBase}/api/v2/detect/quick`, { method: "POST", body: formData })
      .then(async (response) => {
        setUploadProgress("Analyzing audio...");
        const contentType = response.headers.get("content-type");
        const isJson = contentType && contentType.includes("application/json");
        const payload = isJson ? await response.json() : await response.text();
        if (!response.ok) {
          throw new Error(isJson && payload?.detail ? payload.detail : payload);
        }
        return payload;
      })
      .then((payload) => {
        setResult(payload);
        setUploadProgress("");
      })
      .catch((err) => {
        setError(err.message || "Unexpected error during analysis.");
        setUploadProgress("");
      })
      .finally(() => setUploading(false));
  };

  const verdictClass = result?.verdict ? `verdict-${result.verdict}` : "";
  const evidence = result?.evidence ?? {};

  return (
    <section id="demo" className="demo" aria-labelledby="demo-title">
      <div className="section-container">
        <h2 id="demo-title" className="section-title">Physics-Based Explainability</h2>
        <p className="section-text">Upload an audio file to analyze it using our forensic detection suite.</p>
        
        {/* ARIA live region for status announcements */}
        <div 
          role="status" 
          aria-live="polite" 
          aria-atomic="true" 
          className="sr-only"
          id="demo-status"
        >
          {uploading && uploadProgress}
          {error && `Error: ${error}`}
          {result && `Analysis complete. Verdict: ${formatVerdict(result.verdict)}`}
        </div>

        <div className="demo-disclaimer-box">
          <p><strong>Demo Note:</strong> This public demo uses 3 core sensors to demonstrate our approach. Enterprise deployments include 10+ specialized analyzers, real-time API integration, and compliance features.</p>
        </div>

        <div className="privacy-assurance">
          <div className="privacy-icon" aria-hidden="true">
            <ShieldIcon size={20} />
          </div>
          <div className="privacy-text">
            <strong>Your privacy is protected</strong>
            <span>Audio files are analyzed in memory and immediately discarded. We do not store, share, or retain any uploaded content.</span>
          </div>
        </div>

        <div className="demo-container">
          {!uploading && !result && !error && (
            <div
              className={`upload-area ${isDragging ? "dragging" : ""}`}
              onClick={triggerFileDialog}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  triggerFileDialog();
                }
              }}
              role="button"
              tabIndex={0}
              aria-label="Upload voice sample"
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                handleFiles(e.dataTransfer.files);
              }}
            >
              <div className="upload-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 16H15V10H19L12 3L5 10H9V16ZM5 18H19V20H5V18Z" fill="currentColor" opacity="0.6" />
                </svg>
              </div>
              <div className="upload-instructions">
                <p>Upload Audio File</p>
                <span>Drop file or click to browse</span>
              </div>
              <ul className="upload-hints">
                <li>Supports WAV, MP3, or M4A (max 10 MB)</li>
                <li>Best results: 5–45 second clips
                  <br />
                  <em>Shorter clips work with our real-time API</em>
                </li>
              </ul>
              <div className="upload-security-note">
                <LockIcon size={12} aria-hidden="true" />
                Secure connection • Files analyzed in memory only
              </div>

              <div className="sample-buttons">
                <button
                  className="reset-button sample-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    fetch("/samples/sample_real.wav")
                      .then(res => res.blob())
                      .then(blob => {
                        const file = new File([blob], "sample_real.wav", { type: "audio/wav" });
                        handleFiles([file]);
                      });
                  }}
                  aria-label="Load and test authentic voice sample"
                >
                  Load Authentic Sample
                </button>
                <button
                  className="reset-button sample-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    fetch("/samples/sample_fake.wav")
                      .then(res => res.blob())
                      .then(blob => {
                        const file = new File([blob], "sample_fake.wav", { type: "audio/wav" });
                        handleFiles([file]);
                      });
                  }}
                  aria-label="Load and test synthetic voice sample"
                >
                  Load Synthetic Sample
                </button>
              </div>

              <input
                ref={inputRef}
                type="file"
                accept="audio/*"
                hidden
                onChange={(event) => handleFiles(event.target.files)}
              />
            </div>
          )}

          {(uploading || result || error) && (
            <div className="results-area">
              {uploading && (
                <div className="analyzing-state">
                  <div className="spinner" aria-label="Uploading audio for analysis" aria-busy="true" />
                  <p className="analyzing-text" aria-live="polite">
                    {uploadProgress || "Analyzing audio securely..."}
                  </p>
                  <p className="analyzing-subtext">Your file will be deleted after analysis</p>
                </div>
              )}

              {error && (
                <div className="error-text" role="alert" aria-live="assertive">
                  <p>
                    <strong>Error:</strong> {error}
                  </p>
                  <button 
                    className="reset-button" 
                    onClick={() => {
                      setError("");
                      setResult(null);
                    }}
                    aria-label="Clear error and try again"
                  >
                    Try Again
                  </button>
                </div>
              )}

              {result && (
                <>
                  <div className={`verdict-section ${verdictClass}`} role="region" aria-labelledby="verdict-label">
                    <p id="verdict-label" className="verdict-label">Verdict</p>
                    <p className="verdict-text" aria-live="polite">
                      {formatVerdict(result.verdict)}
                    </p>
                    <p className="verdict-explainer">
                      {verdictExplainers[result.verdict] || "Sensors are comparing physical cues from the upload against human baselines."}
                    </p>
                  </div>
                  <div className="evidence-section" role="region" aria-labelledby="evidence-title">
                    <p id="evidence-title" className="evidence-title">Forensic Evidence</p>
                    <div className="evidence-grid" role="list">
                      {renderEvidenceRows(evidence)}
                    </div>
                    {result.detail && (
                      <p className="detail-text" aria-label="Additional analysis details">
                        {result.detail}
                      </p>
                    )}
                  </div>
                  <DetectorChat detectionResult={result} />
                  <button
                    className="reset-button"
                    onClick={() => {
                      setResult(null);
                      setError("");
                      setUploadProgress("");
                    }}
                    aria-label="Clear results and analyze another audio file"
                  >
                    Analyze Another File
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

function renderEvidenceRows(evidence) {
  const dynamicRange = evidence.check_dynamic_range_sensor;
  const breath = evidence.check_breath_sensor;
  const bandwidth = evidence.check_bandwidth_sensor;

  const rows = [];

  if (bandwidth) {
    rows.push({
      label: "Bandwidth Type",
      value: `${bandwidth.type || "UNKNOWN"}${bandwidth.value ? ` (Rolloff: ${bandwidth.value} Hz)` : ""}`,
      status: bandwidth.type === "NARROWBAND" ? "fail" : "pass",
      help: SENSOR_HELP["Bandwidth Type"],
    });
  }

  if (dynamicRange) {
    rows.push({
      label: "Dynamic Range (Crest Factor)",
      value: `${dynamicRange.value} (Thresh: >${dynamicRange.threshold})`,
      status: dynamicRange.passed ? "pass" : "fail",
      help: SENSOR_HELP["Dynamic Range (Crest Factor)"],
    });
  }

  if (breath) {
    rows.push({
      label: "Breath Sensor (Max Phonation)",
      value: `${breath.value}s (Limit: ${breath.threshold}s)`,
      status: breath.passed ? "pass" : "fail",
      help: SENSOR_HELP["Breath Sensor (Max Phonation)"],
    });
  }

  // Include new sensors when available
  ["phase_coherence", "glottal_inertia", "global_formants", "digital_silence", "coarticulation"].forEach((key) => {
    const sensor = evidence[key];
    if (sensor) {
      const formattedLabel = key.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
      rows.push({
        label: formattedLabel,
        value: sensor.detail || JSON.stringify(sensor),
        status: sensor.passed === false ? "fail" : "pass",
        help:
          SENSOR_HELP[formattedLabel] ||
          SENSOR_HELP[key.replace("_", "").replace(/\b\w/g, (c) => c.toUpperCase())] ||
          "Additional spectral and articulation cues for forensic review.",
      });
    }
  });

  // Include HuggingFace neural network detector if available
  const hfDetector = evidence.huggingface_detector;
  if (hfDetector) {
    const syntheticProb = hfDetector.synthetic_probability || hfDetector.value || 0;
    const confidence = ((1 - syntheticProb) * 100).toFixed(1);
    rows.push({
      label: "Neural Network (HuggingFace)",
      value: `${hfDetector.passed ? "Authentic" : "Synthetic"} (${confidence}% confidence)`,
      status: hfDetector.passed === false ? "fail" : "pass",
      help: SENSOR_HELP["Huggingface Detector"],
    });
  }

  return rows.map((row) => (
    <div key={row.label} className="grid-row" role="listitem">
      <div className="grid-item label" aria-label={`Sensor: ${row.label}`}>
        {row.label}
      </div>
      <div 
        className={`grid-item value ${row.status}`}
        aria-label={`${row.label} result: ${row.value}, Status: ${row.status === 'pass' ? 'passed' : 'failed'}`}
      >
        {row.value}
      </div>
      {row.help && (
        <div className="grid-item help" aria-label={`Explanation for ${row.label}`}>
          {row.help}
        </div>
      )}
    </div>
  ));
}

export default Demo;

