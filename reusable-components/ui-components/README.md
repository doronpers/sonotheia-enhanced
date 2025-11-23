# UI Components - Reusable React Patterns

## Overview

Reusable React component patterns for file upload, analysis, and results display.

## Core Components

### 1. Upload Area with Drag-and-Drop

**Purpose**: User-friendly file upload interface

**Features**:
- Click to upload
- Drag-and-drop support
- Visual feedback (dragging state)
- File type restrictions

**Pattern**:
```jsx
const UploadArea = ({ onFileSelect, acceptedTypes = "audio/*" }) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files) => {
    const file = files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <div
      className={`upload-area ${isDragging ? "dragging" : ""}`}
      onClick={() => inputRef.current?.click()}
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
      <div className="upload-instructions">
        <p>UPLOAD FILE</p>
        <span>Drag & Drop or Click to Select</span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes}
        hidden
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
};
```

**CSS**:
```css
.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 1.5rem;
  padding: 3rem;
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.upload-area.dragging {
  border-color: #5b8eff;
  background: rgba(91, 142, 255, 0.08);
}
```

---

### 2. API Integration Pattern

**Purpose**: Environment-aware API configuration

**Pattern**:
```jsx
const apiBase = import.meta.env.VITE_API_BASE_URL?.length > 0
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
    : "";

const fetchAnalysis = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBase}/api/v2/detect/quick`, {
    method: "POST",
    body: formData
  });

  const contentType = response.headers.get("content-type");
  const isJson = contentType?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(isJson && payload?.detail ? payload.detail : payload);
  }

  return payload;
};
```

**Advantages**:
- Works in development (relative URLs) and production (absolute URLs)
- Handles both JSON and non-JSON errors
- Environment variable configuration

---

### 3. State Management Pattern

**Purpose**: Manage upload/loading/result/error states

**Pattern**:
```jsx
const Demo = () => {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleAnalysis = async (file) => {
    setUploading(true);
    setResult(null);
    setError("");

    try {
      const data = await fetchAnalysis(file);
      setResult(data);
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {!uploading && !result && !error && (
        <UploadArea onFileSelect={handleAnalysis} />
      )}
      
      {uploading && <LoadingSpinner />}
      
      {error && (
        <ErrorDisplay error={error} onReset={() => setError("")} />
      )}
      
      {result && (
        <ResultsDisplay result={result} onReset={() => setResult(null)} />
      )}
    </div>
  );
};
```

---

### 4. Dynamic Evidence Grid

**Purpose**: Flexible display of analysis results

**Pattern**:
```jsx
function renderEvidenceRows(evidence) {
  const rows = [];
  
  // Core sensors
  if (evidence.sensor_a) {
    rows.push({
      label: "Sensor A",
      value: `${evidence.sensor_a.value} (Threshold: ${evidence.sensor_a.threshold})`,
      status: evidence.sensor_a.passed ? "pass" : "fail"
    });
  }
  
  // Optional sensors (dynamically added)
  ["sensor_b", "sensor_c", "sensor_d"].forEach((key) => {
    if (evidence[key]) {
      rows.push({
        label: formatLabel(key),
        value: evidence[key].detail || JSON.stringify(evidence[key]),
        status: evidence[key].passed === false ? "fail" : "pass"
      });
    }
  });
  
  return rows.map((row) => (
    <div key={row.label} className="grid-row">
      <div className="grid-item label">{row.label}</div>
      <div className={`grid-item value ${row.status}`}>{row.value}</div>
    </div>
  ));
}
```

**Advantages**:
- Handles variable number of sensors
- Gracefully handles missing data
- Status-based styling

---

### 5. Loading Spinner

**Pattern**:
```jsx
const LoadingSpinner = ({ message = "Analyzing..." }) => (
  <div className="spinner-container">
    <div className="spinner" />
    {message && <p>{message}</p>}
  </div>
);
```

**CSS**:
```css
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #5b8eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

### 6. Verdict Display

**Purpose**: Color-coded results

**Pattern**:
```jsx
const VerdictDisplay = ({ verdict, detail }) => (
  <div className={`verdict-section verdict-${verdict}`}>
    <p className="verdict-label">Verdict</p>
    <p className="verdict-text">{verdict}</p>
    {detail && <p className="verdict-detail">{detail}</p>}
  </div>
);
```

**CSS**:
```css
.verdict-REAL {
  background: rgba(70, 190, 125, 0.15);
  border: 1px solid rgba(70, 190, 125, 0.3);
}

.verdict-SYNTHETIC {
  background: rgba(255, 94, 94, 0.15);
  border: 1px solid rgba(255, 94, 94, 0.3);
}

.verdict-text {
  font-size: 2rem;
  font-weight: 600;
}
```

---

## Design System

### Color Tokens
```css
:root {
  --bg-primary: #05070d;
  --bg-secondary: #0a0e1b;
  --text-primary: #f4f6fb;
  --text-secondary: rgba(244, 246, 251, 0.85);
  
  --color-success: #61d5a3;
  --color-error: #ff7b7b;
  --color-warning: #ffb84d;
  
  --color-brand-blue: #5b8eff;
  --color-brand-purple: #8f6bff;
  
  --border-subtle: rgba(255, 255, 255, 0.05);
  --border-normal: rgba(255, 255, 255, 0.1);
}
```

### Glassmorphism Effect
```css
.glass-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: 1.2rem;
  padding: 1.8rem;
  backdrop-filter: blur(6px);
}
```

### Gradient Button
```css
.gradient-button {
  background: linear-gradient(120deg, var(--color-brand-blue), var(--color-brand-purple));
  box-shadow: 0 20px 40px rgba(91, 142, 255, 0.25);
  border-radius: 999px;
  padding: 0.9rem 2.5rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.gradient-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 25px 55px rgba(91, 142, 255, 0.35);
}
```

---

## Responsive Design

### Mobile-First Grid
```css
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
}
```

### Responsive Typography
```css
.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
}
```

---

## Accessibility

### ARIA Labels
```jsx
<div className="spinner" aria-label="Uploading file for analysis" />
```

### Keyboard Navigation
```jsx
<button
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  tabIndex={0}
>
```

---

## Files to Extract

From `frontend/src/`:
- ✅ `components/Demo.jsx` - Main demo component
- ✅ `styles.css` - Design system
- 📝 Individual component patterns

From `frontend/html/`:
- 📝 `index.html` - Vanilla JS alternative
- 📝 `script.js` - No-build implementation

---

## Usage Guide

### 1. Install Dependencies
```bash
npm install react react-dom
```

### 2. Copy Components
```bash
cp frontend/src/components/Demo.jsx your-project/
cp frontend/src/styles.css your-project/
```

### 3. Adapt to Your API
```jsx
// Change API endpoint
const response = await fetch(`${apiBase}/your-endpoint`, {
  method: "POST",
  body: formData
});

// Adapt evidence display
function renderYourEvidence(data) {
  // Your custom rendering logic
}
```

---

## Benefits

✅ Production-tested patterns
✅ Accessible and responsive
✅ Modern React hooks
✅ Clean, maintainable code
✅ Professional UI/UX
✅ Environment-aware configuration

## License

Reusable under project license.
