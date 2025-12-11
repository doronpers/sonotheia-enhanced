import React, { useState } from 'react';
import ForensicDisplay from './ForensicDisplay';
import AISentinel from './AISentinel';
import DashboardTopBar from './DashboardTopBar';


const ForensicButler = () => {
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState(null);

    // Mode: 'quick' for simple upload, 'advanced' for simulation builder
    const [demoMode, setDemoMode] = useState('advanced');

    // State for Quick Detection
    const [uploadedFile, setUploadedFile] = useState(null);
    const [isDragOver, setIsDragOver] = useState(false);

    // State for Simulation Building
    const [selectedScenario, setSelectedScenario] = useState(null);
    const [vectorMessages, setVectorMessages] = useState([]); // Chat history for Right Panel
    const [vectorInput, setVectorInput] = useState("");
    const [customPrompt, setCustomPrompt] = useState(""); // The actual prompt being built



    const SCENARIOS = [
        {
            id: 'deepfake_injection',
            label: 'Voice Cloning Injection',
            basePrompt: "Simulate a sophisticated high-risk AI voice cloning attack (Deepfake Injection). High likelyhood of synthetic origin.",
            sysMsg: "Voice Cloning Vector detected. AI signatures often visible. Configure specific constraints?"
        },
        {
            id: 'replay_attack',
            label: 'Biometric Spoof (Replay)',
            basePrompt: "Simulate a detected Replay Attack. Low jitter but high background noise floor anomalies and lack of liveness signatures.",
            sysMsg: "Replay Attack Vector loaded. Room impulse artifacts anticipated. Add specific environmental constraints?"
        },
        {
            id: 'zero_day_exploit',
            label: 'Zero-Day Exploit',
            basePrompt: "Simulate a Zero-Day audio exploit. Standard AI models should FAIL detection, but Physics Engine must detect erratic quantization noise and impossible formant shifts.",
            sysMsg: "CRITICAL: Zero-Day Protocol initiated. Standard AI detection disabled. Physics Engine active. Describe the threat anomaly..."
        },
        {
            id: 'poor_connection',
            label: 'Authentic (Poor Signal)',
            basePrompt: "Simulate a messy but AUTHENTIC signal with poor connection. High packet loss and jitter, but organic liveness signatures are intact.",
            sysMsg: "High-Latency connection simulated. Jitter thresholds adapted. Any specific network artifacts?"
        }
    ];

    const handleScenarioSelect = (scenario) => {
        setSelectedScenario(scenario);
        setCustomPrompt(scenario.basePrompt);
        setVectorMessages([
            { role: 'system', text: `PROTOCOL INITIALIZED: ${scenario.label}` },
            { role: 'system', text: scenario.sysMsg }
        ]);
        setVectorInput("");
    };

    const handleVectorSubmit = (e) => {
        e.preventDefault();
        if (!vectorInput.trim()) return;

        // Add user message to UI
        const newMsgs = [...vectorMessages, { role: 'user', text: vectorInput }];
        setVectorMessages(newMsgs);

        // Update the prompt
        setCustomPrompt(prev => prev + " " + vectorInput);

        // Add System acknowledgement
        setTimeout(() => {
            setVectorMessages(prev => [...prev, { role: 'system', text: `Parameter updated: "${vectorInput}" added to simulation topology.` }]);
        }, 500);

        setVectorInput("");
    };

    const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://sonotheia-backend.onrender.com');

    // Quick Detection handlers
    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('audio/')) {
            setUploadedFile(file);
            setError(null);
        } else {
            setError('Please upload an audio file (MP3, WAV, etc.)');
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setUploadedFile(file);
            setError(null);
        }
    };

    const [uploadProgress, setUploadProgress] = useState("");

    const handleQuickAnalyze = async () => {
        if (!uploadedFile) return;

        setIsAnalyzing(true);
        setAnalysisResult(null);
        setError(null);
        setUploadProgress("Uploading file...");

        try {
            const formData = new FormData();
            formData.append('file', uploadedFile);

            const response = await fetch(`${API_URL}/api/v2/detect/quick`, {
                method: 'POST',
                body: formData,
            });

            setUploadProgress("Analyzing audio signatures...");

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errData.detail || 'Analysis failed');
            }

            const data = await response.json();
            setAnalysisResult(data);
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setIsAnalyzing(false);
            setUploadProgress("");
        }
    };

    const handleRunSimulation = async () => {
        if (!selectedScenario) return;

        setIsAnalyzing(true);
        setAnalysisResult(null);
        setError(null);

        // Simulate "Processing" delay
        setTimeout(async () => {
            try {
                const response = await fetch(`${API_URL}/simulate/scenario`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        scenario_type: customScenarioText || customPrompt, // Fallback logic
                        provider: "auto"
                    }),
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({ detail: response.statusText }));
                    throw new Error(errData.detail || 'Simulation failed');
                }

                const data = await response.json();
                setAnalysisResult(data);
            } catch (error) {
                console.error(error);
                setError(error.message);
            } finally {
                setIsAnalyzing(false);
            }
        }, 1500);
    };

    // Correct variable for API call
    const customScenarioText = customPrompt;

    return (
        <>

            <h2 id="demo-title" className="section-title">Forensic Demo</h2>
            <section id="demo" className="butler-container">
                {/* Top Bar */}
                <DashboardTopBar />

                {/* Main Content Area */}
                <div className="butler-main-content">
                    {/* Initial State */}
                    {!analysisResult && !isAnalyzing && (
                        <div className="butler-init-container" style={{ flexDirection: 'column', alignItems: 'center' }}>

                            {/* Mode Selector Tabs */}
                            <div className="butler-mode-tabs">
                                <button
                                    className={`butler-mode-tab ${demoMode === 'quick' ? 'butler-mode-tab-active' : ''}`}
                                    onClick={() => setDemoMode('quick')}
                                >
                                    Quick Detection
                                </button>
                                <button
                                    className={`butler-mode-tab ${demoMode === 'advanced' ? 'butler-mode-tab-active' : ''}`}
                                    onClick={() => setDemoMode('advanced')}
                                >
                                    Simulated Threat Event
                                </button>
                            </div>

                            {/* Quick Detection Mode */}
                            {demoMode === 'quick' && (
                                <div className="butler-quick-mode">
                                    <div className="butler-quick-header">
                                        <h3>Upload Audio for Analysis</h3>
                                        <p>Drop an audio file to detect synthetic speech in seconds</p>
                                    </div>

                                    <div
                                        className={`butler-upload-zone ${isDragOver ? 'butler-upload-zone-active' : ''} ${uploadedFile ? 'butler-upload-zone-ready' : ''}`}
                                        onDragOver={handleDragOver}
                                        onDragLeave={handleDragLeave}
                                        onDrop={handleDrop}
                                        onClick={() => document.getElementById('audio-upload').click()}
                                    >
                                        <input
                                            id="audio-upload"
                                            type="file"
                                            accept="audio/*"
                                            onChange={handleFileSelect}
                                            style={{ display: 'none' }}
                                        />
                                        {uploadedFile ? (
                                            <div className="butler-file-ready">
                                                <div className="butler-file-icon">&#128266;</div>
                                                <div className="butler-file-name">{uploadedFile.name}</div>
                                                <div className="butler-file-size">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</div>
                                            </div>
                                        ) : (
                                            <div className="butler-upload-prompt">
                                                <div className="butler-upload-icon">&#127908;</div>
                                                <div className="butler-upload-text">
                                                    Drag and drop audio file here<br />
                                                    <span>or click to browse</span>
                                                </div>
                                                <div className="butler-upload-formats">MP3, WAV, M4A, FLAC, OGG</div>
                                            </div>
                                        )}
                                    </div>

                                    {error && (
                                        <div className="butler-error-message">{error}</div>
                                    )}

                                    <button
                                        className="butler-analyze-button"
                                        onClick={handleQuickAnalyze}
                                        disabled={!uploadedFile}
                                    >
                                        Analyze Audio
                                    </button>

                                    <p className="butler-quick-note">
                                        Audio is processed in-memory and never stored. Analysis typically completes in under 200ms.
                                    </p>
                                </div>
                            )}

                            {/* Advanced Simulation Mode */}
                            {demoMode === 'advanced' && (
                                <div className="butler-advanced-mode">
                                    {/* Left Panel: AIETHIA Command (Selection) */}
                                    <div className="butler-left-panel">
                                        <div className="butler-panel-header">
                                            <span style={{ color: '#34D399' }}>&#9679;</span>
                                            <span className="butler-panel-title">AIETHIA COMMAND</span>
                                        </div>
                                        <div className="butler-chat-area">
                                            {/* Greetings */}
                                            <div className="butler-message-row">
                                                <div className="butler-system-bubble">
                                                    <strong>AIETHIA CHAT v1.0</strong><br />
                                                    System Ready. Select a threat scenario to begin simulation..<span style={{ animation: 'blink 1s infinite' }}>.</span>
                                                </div>
                                            </div>

                                            {/* Selection Chips */}
                                            <div className="butler-message-row" style={{ marginTop: '2rem' }}>
                                                <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', marginBottom: '0.5rem', marginLeft: '0.5rem' }}>SELECT SCENARIO</div>
                                                <div className="butler-chip-container">
                                                    {SCENARIOS.map(sc => (
                                                        <button
                                                            key={sc.id}
                                                            className={`butler-chip ${selectedScenario?.id === sc.id ? 'butler-chip-active' : ''}`}
                                                            onClick={() => handleScenarioSelect(sc)}
                                                        >
                                                            {selectedScenario?.id === sc.id && <span>&#10003;</span>}
                                                            {sc.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right Panel: Vector Intelligence (Configuration) */}
                                    <div className="butler-right-panel" style={{
                                        opacity: selectedScenario ? 1 : 0.5,
                                        pointerEvents: selectedScenario ? 'all' : 'none',
                                        filter: selectedScenario ? 'none' : 'grayscale(100%)'
                                    }}>
                                        <div className="butler-panel-header" style={{ borderBottomColor: 'rgba(229, 185, 86, 0.15)' }}>
                                            <span style={{ color: '#E5B956' }}>&#9889;</span>
                                            <span className="butler-panel-title" style={{ color: '#E5B956' }}>Scenario Specifications</span>
                                        </div>

                                        {/* Chat Area for Customizing */}
                                        <div className="butler-chat-area">
                                            {vectorMessages.length === 0 ? (
                                                <div className="butler-empty-state butler-empty-message">
                                                    <div className="butler-empty-icon">&#9881;&#xFE0E;</div>
                                                    <div className="butler-empty-text">Select a scenario from the left to configure simulation parameters.</div>
                                                </div>
                                            ) : (
                                                vectorMessages.map((msg, idx) => (
                                                    <div key={idx} className="butler-message-row">
                                                        <div className={msg.role === 'system' ? 'butler-system-bubble' : 'butler-user-bubble'}>
                                                            {msg.text}
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                        </div>

                                        {/* Input Area */}
                                        <form className="butler-input-area" onSubmit={handleVectorSubmit}>
                                            <span style={{ color: '#E5B956', fontFamily: 'monospace' }}>&gt;</span>
                                            <input
                                                type="text"
                                                placeholder="Adjust simulation parameters..."
                                                className="butler-input-field"
                                                value={vectorInput}
                                                onChange={(e) => setVectorInput(e.target.value)}
                                                disabled={!selectedScenario}
                                            />
                                            <button type="button" onClick={handleRunSimulation} className="butler-run-button">
                                                RUN SIMULATION &#9654;
                                            </button>
                                        </form>
                                    </div>
                                </div>
                            )}

                        </div>
                    )}

                    {/* Loading State */}
                    {isAnalyzing && (
                        <div className="butler-loading-container">
                            <div className="butler-spinner"></div>
                            <div className="butler-loading-text">{uploadProgress || "Analyzing audio..."}</div>
                        </div>
                    )}

                    {/* Dashboard View */}
                    {analysisResult && (
                        <div className="butler-dashboard-container">
                            <div className="butler-reset-bar">
                                <button
                                    onClick={() => setAnalysisResult(null)}
                                    className="butler-reset-button"
                                    onMouseOver={(e) => e.target.style.color = '#F0F0F2'}
                                    onMouseOut={(e) => e.target.style.color = 'rgba(240, 240, 242, 0.5)'}
                                >
                                    ↺ New Analysis
                                </button>
                            </div>

                            <div className="butler-panels-container">
                                <div className="butler-panels-row">
                                    <div className="butler-main-left-panel">
                                        <AISentinel result={analysisResult} onSimulationUpdate={setAnalysisResult} provider="auto" />
                                    </div>
                                    <div className="butler-main-right-panel">
                                        <ForensicDisplay result={analysisResult} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </>
    );
};

export default ForensicButler;
