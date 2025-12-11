import React, { useState, useEffect, useRef } from "react";
import { X, Terminal, Cpu, ShieldAlert, Activity, Play, Zap, AlertTriangle, CheckCircle2, Lock } from "lucide-react";
import ForensicDisplay from "./ForensicDisplay";

/**
 * DataFactoryController (Refined UX)
 * 
 * A UI for controlling the backend Data Factory (Simulation Studio).
 * Features a "Cyberpunk/Forensic" aesthetic with CRT terminal effects.
 */

// Mock Result for Visualizer since Factory logs are text-only
const MOCK_FORENSIC_RESULT = {
    verdict: {
        risk_level: "CRITICAL",
        final_determination: "SYNTHETIC_GENERATED",
        confidence_score: 0.98
    },
    physics_engine: {
        latency_jitter: { value_ms: 245, status: "FAIL" },
        vocal_crypt: { value: 0, status: "INVALID" },
        geo_location: { value: 1, status: "MATCH" }
    },
    evidence_log: [] // Handled inside component
};

const DataFactoryController = ({ isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState("verify"); // verify, augment, generate
    const [viewMode, setViewMode] = useState("console"); // 'console' | 'visualizer'
    const [logs, setLogs] = useState("Initializing Secure Link...");
    const [status, setStatus] = useState("IDLE"); // IDLE, RUNNING, SUCCESS, ERROR
    const logContainerRef = useRef(null);

    // Settings State
    const [genCount, setGenCount] = useState(5);
    const [genService, setGenService] = useState("openai");
    const [augCount, setAugCount] = useState(10);
    const [augAll, setAugAll] = useState(false);
    const [verifyCount, setVerifyCount] = useState(50);
    const [showCostWarning, setShowCostWarning] = useState(false);

    const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

    // Polling for logs & Status Detection
    useEffect(() => {
        let interval;
        if (isOpen) {
            interval = setInterval(async () => {
                try {
                    const res = await fetch(`${API_BASE}/api/factory/logs`);
                    const data = await res.json();

                    if (data.logs) {
                        // Only update if changed to avoid jitter, but we need to auto-scroll
                        setLogs(prev => {
                            if (prev !== data.logs) {
                                // Check for completion signals
                                if (data.logs.includes("--- Job Completed ---") && status === "RUNNING") {
                                    setStatus("SUCCESS");
                                }
                                if (data.logs.includes("[ERROR]") && status === "RUNNING") {
                                    setStatus("ERROR");
                                }
                                return data.logs;
                            }
                            return prev;
                        });
                    }
                } catch (e) {
                    console.error("Log fetch error:", e);
                }
            }, 1000); // Faster polling for better UX
        }
        return () => clearInterval(interval);
    }, [isOpen, API_BASE, status]);

    // Auto-scroll effect
    useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs]);

    const runCommand = async (endpoint, payload) => {
        setStatus("RUNNING");
        setLogs("Transmitting command instructions...\n");
        try {
            await fetch(`${API_BASE}/api/factory/${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } catch (e) {
            setLogs(prev => prev + `\n[ERROR] Request failed: ${e}`);
            setStatus("ERROR");
        }
    };

    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [passcode, setPasscode] = useState("");
    const [errorMsg, setErrorMsg] = useState("");

    // ... [existing useEffects]

    if (!isOpen) return null;

    if (!isAuthenticated) {
        return (
            <div className="fixed inset-0 bg-black/95 backdrop-blur-md z-50 flex items-center justify-center p-4">
                <div className="bg-[#050505] border border-red-500/20 rounded-xl p-8 max-w-md w-full shadow-2xl ring-1 ring-red-900/20 flex flex-col items-center gap-6 animate-in zoom-in duration-300">
                    <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20">
                        <Lock className="w-8 h-8 text-red-500" />
                    </div>
                    <div className="text-center space-y-2">
                        <h2 className="text-xl font-bold text-white tracking-widest font-mono">RESTRICTED ACCESS</h2>
                        <p className="text-sm text-white/40">Secure Engineering Environment</p>
                    </div>
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            // Hardcoded for demo simplicity, can be moved to env
                            if (passcode === "admin123" || passcode === "incode") {
                                setIsAuthenticated(true);
                                setErrorMsg("");
                            } else {
                                setErrorMsg("ACCESS DENIED");
                                setPasscode("");
                            }
                        }}
                        className="w-full space-y-4"
                    >
                        <input
                            type="password"
                            placeholder="ENTER PASSCODE"
                            value={passcode}
                            onChange={(e) => setPasscode(e.target.value)}
                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-center text-white font-mono tracking-[0.5em] focus:border-red-500 focus:outline-none placeholder:tracking-normal placeholder:text-white/20 transition-colors"
                            autoFocus
                        />
                        {errorMsg && (
                            <div className="text-red-500 text-xs font-bold text-center animate-pulse">
                                {errorMsg}
                            </div>
                        )}
                        <button
                            type="submit"
                            className="w-full py-3 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white font-bold text-xs uppercase tracking-widest rounded-lg border border-white/5 transition-all"
                        >
                            Authenticate
                        </button>
                    </form>
                    <button onClick={onClose} className="text-white/20 hover:text-white text-xs uppercase tracking-wider mt-4">
                        Cancel Connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-[#050505] border border-white/10 rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300 ring-1 ring-white/5">

                {/* Header - Update with View Toggle */}
                <div className="border-b border-white/10 p-5 flex justify-between items-center bg-gradient-to-r from-purple-900/10 to-transparent">
                    <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg border border-purple-500/30 ${status === 'RUNNING' ? 'animate-pulse bg-purple-500/20' : 'bg-purple-500/10'}`}>
                            <Cpu className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight font-mono">SIMULATION_STUDIO_v1</h2>
                            <div className="flex items-center gap-2 mt-1">
                                <span className={`w-2 h-2 rounded-full ${status === 'RUNNING' ? 'bg-amber-400 animate-pulse' : 'bg-green-500'}`}></span>
                                <p className="text-xs text-white/50 uppercase tracking-widest font-mono">
                                    {status === 'RUNNING' ? 'PROCESS_ACTIVE' : 'SYSTEM_READY'}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* View Toggle */}
                        <div className="flex bg-black/40 rounded-lg p-1 border border-white/10">
                            <button
                                onClick={() => setViewMode("console")}
                                className={`px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === "console" ? "bg-white/10 text-white" : "text-white/40 hover:text-white"
                                    }`}
                            >
                                System Console
                            </button>
                            <button
                                onClick={() => setViewMode("visualizer")}
                                className={`px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === "visualizer" ? "bg-purple-500/20 text-purple-300" : "text-white/40 hover:text-white"
                                    }`}
                            >
                                Forensic Visualizer
                            </button>
                        </div>

                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/10 rounded-full transition-colors text-white/40 hover:text-white"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 flex overflow-hidden">

                    {/* Sidebar / Controls */}
                    <div className="w-80 border-r border-white/10 bg-black/40 overflow-y-auto flex flex-col">

                        {/* Navigation Tabs - Vertical */}
                        <div className="p-4 space-y-2">
                            <button
                                onClick={() => setActiveTab('verify')}
                                className={`w-full text-left px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-widest transition-all border flex items-center gap-3 ${activeTab === 'verify'
                                    ? 'bg-purple-500/20 border-purple-500/50 text-purple-300'
                                    : 'border-transparent text-white/40 hover:bg-white/5 hover:text-white'
                                    }`}
                            >
                                <Activity className="w-4 h-4" />
                                Verification
                            </button>
                            <button
                                onClick={() => setActiveTab('augment')}
                                className={`w-full text-left px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-widest transition-all border flex items-center gap-3 ${activeTab === 'augment'
                                    ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                                    : 'border-transparent text-white/40 hover:bg-white/5 hover:text-white'
                                    }`}
                            >
                                <ShieldAlert className="w-4 h-4" />
                                Telephony Effects
                            </button>
                            <button
                                onClick={() => setActiveTab('generate')}
                                className={`w-full text-left px-4 py-3 rounded-lg text-xs font-bold uppercase tracking-widest transition-all border flex items-center gap-3 ${activeTab === 'generate'
                                    ? 'bg-red-500/20 border-red-500/50 text-red-300'
                                    : 'border-transparent text-white/40 hover:bg-white/5 hover:text-white'
                                    }`}
                            >
                                <Zap className="w-4 h-4" />
                                Red Team Generation
                            </button>
                        </div>

                        <div className="h-px bg-white/10 mx-6 my-2"></div>

                        {/* Active Control Panel */}
                        <div className="p-6 flex-1">

                            {/* Verify Controls */}
                            {activeTab === 'verify' && (
                                <div className="space-y-6 animate-in slide-in-from-left duration-300">
                                    <div className="space-y-3">
                                        <h3 className="text-white text-sm font-bold">Micro-Test Protocol</h3>
                                        <p className="text-xs text-white/50 leading-relaxed">
                                            Rapidly verify detector accuracy on a random subset of the library (50% Real / 50% Fake).
                                        </p>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-white/60 uppercase tracking-widest">Sample Count: {verifyCount}</label>
                                        <input
                                            type="range" min="10" max="200" step="10"
                                            value={verifyCount} onChange={(e) => setVerifyCount(parseInt(e.target.value))}
                                            className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-purple-500"
                                        />
                                    </div>

                                    <button
                                        onClick={() => runCommand('test', { count: verifyCount })}
                                        disabled={status === 'RUNNING'}
                                        className="w-full py-4 bg-white text-black font-bold uppercase tracking-widest rounded-sm hover:bg-purple-400 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                                    >
                                        {status === 'RUNNING'
                                            ? <Activity className="w-4 h-4 animate-spin" />
                                            : <Play className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                        }
                                        Execute Test
                                    </button>
                                </div>
                            )}

                            {/* Augment Controls */}
                            {activeTab === 'augment' && (
                                <div className="space-y-6 animate-in slide-in-from-left duration-300">
                                    <div className="space-y-3">
                                        <h3 className="text-white text-sm font-bold">Signal Degradation</h3>
                                        <p className="text-xs text-white/50 leading-relaxed">
                                            Applies Landline (8kHz), Mobile (GSM), and VoIP artifact chains to organic audio.
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/5">
                                        <input
                                            type="checkbox" checked={augAll} onChange={(e) => setAugAll(e.target.checked)}
                                            className="w-4 h-4 rounded border-white/20 bg-black text-blue-500 focus:ring-blue-500"
                                        />
                                        <span className="text-xs font-mono text-white/80">TARGET_ALL_FILES</span>
                                    </div>

                                    {!augAll && (
                                        <div className="space-y-2">
                                            <label className="text-xs font-bold text-white/60 uppercase tracking-widest">Batch Size</label>
                                            <input
                                                type="number" value={augCount} onChange={(e) => setAugCount(parseInt(e.target.value))}
                                                className="w-full bg-black border border-white/10 rounded px-3 py-2 text-white font-mono focus:border-blue-500 outline-none text-sm"
                                            />
                                        </div>
                                    )}

                                    <button
                                        onClick={() => runCommand('augment', { count: augCount, all_files: augAll })}
                                        disabled={status === 'RUNNING'}
                                        className="w-full py-4 bg-white text-black font-bold uppercase tracking-widest rounded-sm hover:bg-blue-400 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                                    >
                                        {status === 'RUNNING' ? <Activity className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4 group-hover:fill-current" />}
                                        Inject Telephony
                                    </button>
                                </div>
                            )}

                            {/* Generate Controls */}
                            {activeTab === 'generate' && (
                                <div className="space-y-6 animate-in slide-in-from-left duration-300">
                                    <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-lg">
                                        <div className="flex items-center gap-2 text-red-400 mb-2">
                                            <AlertTriangle className="w-4 h-4" />
                                            <span className="text-xs font-bold uppercase">External API Cost</span>
                                        </div>
                                        <p className="text-[10px] text-white/60 leading-relaxed">
                                            Generation uses paid APIs (OpenAI/ElevenLabs).
                                            Estimated cost: ~$0.01 per sample.
                                        </p>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-white/60 uppercase tracking-widest">Model Provider</label>
                                        <select
                                            value={genService} onChange={(e) => setGenService(e.target.value)}
                                            className="w-full bg-black border border-white/10 rounded px-3 py-2 text-white text-sm focus:border-red-500 outline-none"
                                        >
                                            <option value="openai">OpenAI (TTS-1-HD)</option>
                                            <option value="elevenlabs">ElevenLabs (Multilingual v2)</option>
                                            <option value="all">Combined Attack (All)</option>
                                        </select>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-white/60 uppercase tracking-widest">Sample Count</label>
                                        <input
                                            type="number" value={genCount} onChange={(e) => setGenCount(parseInt(e.target.value))}
                                            className="w-full bg-black border border-white/10 rounded px-3 py-2 text-white font-mono focus:border-red-500 outline-none text-sm"
                                        />
                                    </div>

                                    <button
                                        onClick={() => runCommand('generate', { count: genCount, service: genService })}
                                        disabled={status === 'RUNNING'}
                                        className="w-full py-4 bg-red-600 text-white font-bold uppercase tracking-widest rounded-sm hover:bg-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-red-900/20"
                                    >
                                        {status === 'RUNNING' ? <Activity className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                                        Generate Attack
                                    </button>
                                </div>
                            )}
                        </div>

                    </div>

                    {/* Output Panel */}
                    <div className="flex-1 bg-[#0a0a0a] flex flex-col min-w-0 relative">

                        {viewMode === "console" ? (
                            <>
                                {/* Existing Console Layout */}
                                {/* Header */}
                                <div className="h-10 border-b border-white/10 bg-white/5 flex items-center px-4 justify-between">
                                    <div className="flex items-center gap-2 text-white/40">
                                        <Terminal className="w-3 h-3" />
                                        <span className="text-[10px] font-mono uppercase tracking-wider">/var/log/factory_latest.log</span>
                                    </div>
                                    {status === 'SUCCESS' && (
                                        <div className="flex items-center gap-1.5 text-green-400">
                                            <CheckCircle2 className="w-3 h-3" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Complete</span>
                                        </div>
                                    )}
                                </div>

                                {/* Terminal Body */}
                                <div className="flex-1 relative overflow-hidden group">
                                    <div className="absolute inset-0 pointer-events-none z-10 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] bg-repeat"></div>
                                    <div
                                        ref={logContainerRef}
                                        className="absolute inset-0 p-4 font-mono text-xs text-green-500/80 overflow-y-auto whitespace-pre-wrap leading-relaxed scrollbar-hide"
                                        style={{ textShadow: '0 0 2px rgba(74, 222, 128, 0.2)' }}
                                    >
                                        {logs}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex-1 overflow-hidden relative">
                                {/* Overlay Scanlines for consistency */}
                                <div className="absolute inset-0 pointer-events-none z-20 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%)] bg-[length:100%_3px] bg-repeat opacity-50"></div>
                                <ForensicDisplay result={MOCK_FORENSIC_RESULT} />
                            </div>
                        )}

                        {/* Footer */}
                        {viewMode === "console" && (
                            <div className="h-8 border-t border-white/10 bg-black flex items-center px-4 justify-between text-[10px] text-white/30 font-mono">
                                <span>MEM: 14.2GB / 16GB</span>
                                <span>SECURE_SHELL_ACTIVE</span>
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
};

export default DataFactoryController;
