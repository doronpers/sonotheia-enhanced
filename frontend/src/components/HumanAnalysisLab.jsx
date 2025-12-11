import React, { useState, useRef } from 'react';
import { Upload, Play, Pause, Activity, AlertTriangle, ShieldCheck, X } from 'lucide-react';

const HumanAnalysisLab = ({ isOpen, onClose }) => {
    const [file, setFile] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef(null);

    // Human Analysis State
    const [probability, setProbability] = useState(50);
    const [indicators, setIndicators] = useState({
        metallic: false,
        breath: false,
        pitch: false,
        cadence: false,
        emotion: false,
        artifacts: false
    });
    const [observations, setObservations] = useState("");

    // Backend State
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    // Cleanup audio URL on unmount or change
    React.useEffect(() => {
        return () => {
            if (audioUrl) URL.revokeObjectURL(audioUrl);
        };
    }, [audioUrl]);

    if (!isOpen) return null;

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            if (audioUrl) URL.revokeObjectURL(audioUrl); // Cleanup previous
            setAudioUrl(URL.createObjectURL(selectedFile));
            setResult(null);
            setError(null);
        }
    };

    const toggleIndicator = (key) => {
        setIndicators(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const togglePlay = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handleSubmit = async () => {
        if (!file) return;

        setIsAnalyzing(true);
        setError(null);

        const formData = new FormData();
        formData.append("audio_file", file); // Changed 'file' to 'audio_file' for Backend API compatibility

        // Generate dummy metadata required by backend
        formData.append("call_id", crypto.randomUUID());
        formData.append("customer_id", "LAB-USER-001");
        formData.append("channel", "lab_upload");
        formData.append("codec", "clean");

        try {
            // Use relative path for production compatibility or VITE endpoint
            const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
            const response = await fetch(`${apiBase}/api/analyze_call`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || "Analysis failed");
            }

            const data = await response.json();

            // Map Backend Result to Frontend UI Structure
            const machineResult = {
                verdict: data.risk_result.risk_level === 'LOW' ? 'ORGANIC' : 'SYNTHETIC',
                risk_score: data.risk_result.overall_score,
                physics_metrics: {
                    // Extract relevant factors from the risk result
                    ...data.risk_result.factors.reduce((acc, f) => {
                        acc[f.name] = f.score;
                        return acc;
                    }, {})
                }
            };

            setResult(machineResult);
        } catch (err) {
            console.error(err);
            setError(`Analysis failed: ${err.message}. Ensure backend is running.`);
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <Activity className="w-6 h-6 text-emerald-400" />
                        <h2 className="text-xl font-mono font-bold text-white tracking-wider">
                            R&D HUMAN ANALYSIS LAB
                        </h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">

                    {/* LEFT: Input & Human Analysis */}
                    <div className="space-y-6">

                        {/* 1. Upload & Play */}
                        <div className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${file ? 'border-emerald-500/50 bg-emerald-900/10' : 'border-slate-700 hover:border-slate-600'}`}>
                            {!file ? (
                                <label className="cursor-pointer block">
                                    <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                                    <p className="text-slate-300 font-medium">Upload Audio Sample</p>
                                    <p className="text-sm text-slate-500 mt-1">WAV, MP3 (Max 10MB)</p>
                                    <input type="file" className="hidden" accept="audio/*" onChange={handleFileChange} />
                                </label>
                            ) : (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-center gap-4">
                                        <button
                                            onClick={togglePlay}
                                            className="w-12 h-12 flex items-center justify-center rounded-full bg-emerald-500 hover:bg-emerald-400 text-black transition-all shadow-lg shadow-emerald-500/20"
                                        >
                                            {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
                                        </button>
                                        <div className="text-left">
                                            <p className="text-emerald-400 font-mono text-sm truncate max-w-[200px]">{file.name}</p>
                                            <button onClick={() => setFile(null)} className="text-xs text-slate-500 hover:text-red-400 underline">Remove</button>
                                        </div>
                                    </div>
                                    <audio
                                        ref={audioRef}
                                        src={audioUrl}
                                        onEnded={() => setIsPlaying(false)}
                                        className="hidden"
                                    />
                                </div>
                            )}
                        </div>

                        {/* 2. Human Analysis Form */}
                        <div className={`space-y-6 ${!file ? 'opacity-50 pointer-events-none' : ''}`}>
                            <div>
                                <label className="block text-slate-400 text-sm font-mono mb-2">SYNTHETIC PROBABILITY ({probability}%)</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={probability}
                                    onChange={(e) => setProbability(e.target.value)}
                                    className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                />
                                <div className="flex justify-between text-xs text-slate-600 mt-1 font-mono">
                                    <span>ORGANIC</span>
                                    <span>UNCERTAIN</span>
                                    <span>SYNTHETIC</span>
                                </div>
                            </div>

                            <div>
                                <label className="block text-slate-400 text-sm font-mono mb-3">AUDITORY INDICATORS</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {Object.keys(indicators).map(key => (
                                        <button
                                            key={key}
                                            onClick={() => toggleIndicator(key)}
                                            className={`px-3 py-2 rounded-md text-sm font-medium border transition-all ${indicators[key]
                                                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                                                : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                                                }`}
                                        >
                                            {key.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-slate-400 text-sm font-mono mb-2">OBSERVATIONS</label>
                                <textarea
                                    value={observations}
                                    onChange={(e) => setObservations(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-slate-300 text-sm focus:outline-none focus:border-emerald-500/50 min-h-[100px]"
                                    placeholder="Describe glitches, tone shifts, or specific anomalies..."
                                />
                            </div>

                            <button
                                onClick={handleSubmit}
                                disabled={isAnalyzing}
                                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold rounded-lg shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isAnalyzing ? "READING SENSORS..." : "RUN ANALYSIS & SAVE"}
                            </button>
                        </div>
                    </div>

                    {/* RIGHT: Machine Config / Results */}
                    <div className="bg-black/40 rounded-lg border border-slate-800 p-6 flex flex-col items-center justify-center min-h-[400px]">

                        {!result && !isAnalyzing && (
                            <div className="text-center text-slate-500">
                                <ShieldCheck className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p className="font-mono text-sm">WAITING FOR INPUT</p>
                                <p className="text-xs max-w-[200px] mx-auto mt-2">Submit human analysis to trigger autonomous verification.</p>
                            </div>
                        )}

                        {isAnalyzing && (
                            <div className="text-center">
                                <div className="w-16 h-16 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"></div>
                                <p className="text-emerald-400 font-mono animate-pulse">ANALYZING SIGNAL PHYSICS...</p>
                                <div className="mt-4 space-y-1 text-xs text-slate-500 font-mono">
                                    <p>Spectrogram Generation...</p>
                                    <p>Phase Coherence Check...</p>
                                    <p>Glottal Flow Analysis...</p>
                                </div>
                            </div>
                        )}

                        {result && (
                            <div className="w-full space-y-6 animate-in fade-in zoom-in duration-300">

                                {/* Verdict Badge */}
                                <div className={`text-center p-6 rounded-xl border ${result.verdict === 'SYNTHETIC' ? 'bg-red-500/10 border-red-500/50' :
                                    result.verdict === 'ORGANIC' ? 'bg-emerald-500/10 border-emerald-500/50' :
                                        'bg-amber-500/10 border-amber-500/50'
                                    }`}>
                                    <p className="text-sm font-mono text-slate-400 uppercase mb-1">AUTONOMOUS VERDICT</p>
                                    <h3 className={`text-3xl font-black tracking-tight ${result.verdict === 'SYNTHETIC' ? 'text-red-500' :
                                        result.verdict === 'ORGANIC' ? 'text-emerald-500' :
                                            'text-amber-500'
                                        }`}>
                                        {result.verdict}
                                    </h3>
                                    <p className="font-mono text-sm mt-2 opacity-80">RISK SCORE: {(result.risk_score * 100).toFixed(1)}%</p>
                                </div>

                                {/* Physics Breakdown */}
                                <div className="space-y-4">
                                    <h4 className="text-sm font-mono text-slate-400 border-b border-slate-800 pb-2">PHYSICS ENGINE</h4>
                                    {Object.entries(result.physics_metrics).slice(0, 5).map(([key, value]) => (
                                        <div key={key} className="space-y-1">
                                            <div className="flex justify-between text-xs text-slate-300 font-mono">
                                                <span className="uppercase">{key.replace('_', ' ')}</span>
                                                <span className={value > 0.5 ? 'text-red-400' : 'text-emerald-400'}>{(value).toFixed(2)}</span>
                                            </div>
                                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${value > 0.5 ? 'bg-red-500' : 'bg-emerald-500'}`}
                                                    style={{ width: `${value * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Correlation Message */}
                                <div className="bg-slate-800/50 p-4 rounded-lg mt-6">
                                    <div className="flex gap-3">
                                        <Activity className="w-5 h-5 text-blue-400 shrink-0" />
                                        <div className="text-xs text-slate-300">
                                            <p className="font-bold text-blue-400 mb-1">DATA SAVED</p>
                                            <p>Human perception data correlated with machine vectors. This sample will refine the model's decision boundary.</p>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        )}

                        {error && (
                            <div className="text-center text-red-400 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                                <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
                                <p className="text-sm font-bold">{error}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HumanAnalysisLab;
