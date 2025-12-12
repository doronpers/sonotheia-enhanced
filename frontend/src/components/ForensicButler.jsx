import React, { useState } from 'react';
import ForensicDisplay from './ForensicDisplay';
import AISentinel from './AISentinel';
import DashboardTopBar from './DashboardTopBar';

const ForensicButler = () => {
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState(null);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadProgress, setUploadProgress] = useState("");

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

    const handleQuickAnalyze = async () => {
        if (!uploadedFile) return;

        setIsAnalyzing(true);
        setAnalysisResult(null);
        setError(null);
        setUploadProgress("Securely uploading file...");

        try {
            const formData = new FormData();
            formData.append('file', uploadedFile);

            const response = await fetch(`${API_URL}/api/detect/quick`, {
                method: 'POST',
                body: formData,
            });

            setUploadProgress("Analyzing physics signatures...");

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

    return (
        <>
            <h2 id="demo-title" className="section-title">Verification Engine</h2>
            <section id="demo" className="verification-container" style={{ maxWidth: '1000px', margin: '0 auto', padding: 'var(--space-md)' }}>
                {/* Main Content Area */}
                <div className="verification-content" style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--subtle-gray)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--space-lg)',
                    textAlign: 'center'
                }}>

                    {/* Initial State */}
                    {!analysisResult && !isAnalyzing && (
                        <div className="upload-state">
                            <div style={{ marginBottom: 'var(--space-md)' }}>
                                <h3 style={{ fontSize: '1.25rem', fontWeight: '500', color: 'var(--acoustic-silver)' }}>Audio Analysis Protocol</h3>
                                <p style={{ color: 'var(--medium-gray)', fontSize: '0.9rem', maxWidth: '600px', margin: '0 auto' }}>
                                    Upload an audio file to initiate the 6-stage physics detection pipeline.
                                </p>
                            </div>

                            <div
                                className={`upload-zone ${isDragOver ? 'active' : ''}`}
                                style={{
                                    border: '1px dashed var(--subtle-gray)',
                                    borderRadius: 'var(--radius-md)',
                                    padding: 'var(--space-xl)',
                                    marginTop: 'var(--space-lg)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    background: isDragOver ? 'rgba(255,255,255,0.05)' : 'transparent'
                                }}
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
                                    <div className="file-ready">
                                        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>&#128266;</div>
                                        <div style={{ fontWeight: '600', color: 'var(--acoustic-silver)' }}>{uploadedFile.name}</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--medium-gray)' }}>{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</div>
                                    </div>
                                ) : (
                                    <div className="upload-prompt">
                                        <div style={{ fontSize: '2rem', marginBottom: '1rem', color: 'var(--medium-gray)' }}>&#127908;</div>
                                        <div style={{ color: 'var(--acoustic-silver)', fontWeight: '500' }}>
                                            Click or Drag audio file here
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--medium-gray)', marginTop: '0.5rem' }}>MP3, WAV, M4A, FLAC, OGG</div>
                                    </div>
                                )}
                            </div>

                            {error && (
                                <div style={{ color: 'var(--alert-red)', marginTop: '1rem', fontSize: '0.9rem' }}>{error}</div>
                            )}

                            <button
                                className="btn btn-accent" // Use the Rams style button
                                onClick={handleQuickAnalyze}
                                disabled={!uploadedFile}
                                style={{ marginTop: 'var(--space-lg)', minWidth: '200px' }}
                            >
                                Run Verification
                            </button>

                            <p style={{ fontSize: '0.75rem', color: 'var(--medium-gray)', marginTop: '2rem' }}>
                                Privacy Note: Audio is processed in ephemeral memory and discarded immediately after analysis.
                            </p>
                        </div>
                    )}

                    {/* Loading State */}
                    {isAnalyzing && (
                        <div className="loading-state" style={{ padding: '4rem 0' }}>
                            <div className="spinner" style={{
                                width: '40px', height: '40px',
                                border: '3px solid rgba(255,255,255,0.1)',
                                borderTopColor: 'var(--signal-gold)',
                                borderRadius: '50%',
                                margin: '0 auto 1.5rem',
                                animation: 'spin 1s linear infinite' // Assuming spin keyframes exist, if not will add
                            }}></div>
                            <div style={{ color: 'var(--acoustic-silver)', fontSize: '0.9rem', letterSpacing: '0.05rem' }}>
                                {uploadProgress || "Analyzing signatures..."}
                            </div>
                        </div>
                    )}

                    {/* Dashboard View */}
                    {analysisResult && (
                        <div className="result-dashboard">
                            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                                <button
                                    onClick={() => setAnalysisResult(null)}
                                    className="btn btn-secondary"
                                    style={{ fontSize: '0.75rem', padding: '8px 16px' }}
                                >
                                    New Analysis
                                </button>
                            </div>

                            <div className="panels-row" style={{ display: 'flex', gap: '2rem', flexDirection: 'column' }}>
                                <div className="result-panel">
                                    <AISentinel result={analysisResult} onSimulationUpdate={setAnalysisResult} provider="auto" />
                                </div>
                                <div className="result-panel">
                                    <ForensicDisplay result={analysisResult} />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </>
    );
};

export default ForensicButler;
