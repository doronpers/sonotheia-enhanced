
import React, { useState, useEffect } from "react";
import { Upload, FileAudio, Microscope, CheckCircle, AlertTriangle, Play, Pause, ChevronDown, ChevronRight, Phone, Signal, Wifi } from "lucide-react";

/**
 * Audio Laboratory Component
 * 
 * Allows users to upload and analyze samples to build a benchmark library.
 */
const Laboratory = () => {
    const [activeTab, setActiveTab] = useState("library"); // "library" | "upload"
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploadLabel, setUploadLabel] = useState("organic");
    const [selectedFile, setSelectedFile] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [simulating, setSimulating] = useState(false);

    // Fetch files on mount
    useEffect(() => {
        fetchLibrary();
    }, []);

    const fetchLibrary = async () => {
        try {
            setLoading(true);
            const response = await fetch("http://localhost:8000/api/library/files");
            if (response.ok) {
                const data = await response.json();
                setFiles(data);
            }
        } catch (error) {
            console.error("Failed to load library:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (file) => {
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            // Use query param for label as per API definition
            const response = await fetch(`http://localhost:8000/api/library/upload?label=${uploadLabel}`, {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                fetchLibrary(); // Refresh list
                setActiveTab("library");
            }
        } catch (error) {
            console.error("Upload failed", error);
        }
    };

    const analyzeFile = async (file) => {
        try {
            setAnalyzing(true);
            const response = await fetch(`http://localhost:8000/api/library/analyze/${file.label}/${file.filename}`, {
                method: "POST"
            });

            if (response.ok) {
                // Refresh details for the selected file if it's this one
                fetchLibrary();
            }
        } catch (error) {
            console.error("Analysis failed", error);
        } finally {
            setAnalyzing(false);
        }
    };

    const simulateNetwork = async (file, codec) => {
        try {
            setSimulating(true);
            const response = await fetch(`http://localhost:8000/api/library/simulate/${file.label}/${file.filename}?codec=${codec}`, {
                method: "POST"
            });

            if (response.ok) {
                const data = await response.json();
                fetchLibrary(); // Refresh list to show new file
            }
        } catch (error) {
            console.error("Simulation failed", error);
        } finally {
            setSimulating(false);
        }
    };

    // Helper to get color for score
    const getScoreColor = (score) => {
        if (score === null || score === undefined) return "text-gray-400";
        if (score > 0.7) return "text-red-500";
        if (score < 0.3) return "text-green-500";
        return "text-yellow-500";
    };

    return (
        <div className="p-6 bg-[#0a0a0b] text-white min-h-screen font-sans">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                        Audio Laboratory
                    </h1>
                    <p className="text-gray-400 mt-1">Research & Development Environment</p>
                </div>

                <div className="flex space-x-4">
                    <button
                        onClick={() => setActiveTab("library")}
                        className={`px-4 py-2 rounded-lg transition-colors ${activeTab === "library" ? "bg-blue-600" : "bg-gray-800 hover:bg-gray-700"}`}
                    >
                        Library
                    </button>
                    <button
                        onClick={() => setActiveTab("upload")}
                        className={`px-4 py-2 rounded-lg transition-colors ${activeTab === "upload" ? "bg-blue-600" : "bg-gray-800 hover:bg-gray-700"}`}
                    >
                        Upload Sample
                    </button>
                </div>
            </div>

            {activeTab === "upload" && (
                <div className="max-w-xl mx-auto mt-12 p-8 border-2 border-dashed border-gray-700 rounded-xl bg-gray-900/50">
                    <div className="mb-6 flex justify-center space-x-6">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="radio"
                                name="label"
                                value="organic"
                                checked={uploadLabel === "organic"}
                                onChange={(e) => setUploadLabel(e.target.value)}
                                className="form-radio text-green-500"
                            />
                            <span className="text-green-400">Organic (Real)</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="radio"
                                name="label"
                                value="synthetic"
                                checked={uploadLabel === "synthetic"}
                                onChange={(e) => setUploadLabel(e.target.value)}
                                className="form-radio text-red-500"
                            />
                            <span className="text-red-400">Synthetic (Fake)</span>
                        </label>
                    </div>

                    <div className="flex flex-col items-center justify-center space-y-4">
                        <Upload className="w-16 h-16 text-gray-500 mb-2" />
                        <p className="text-lg text-gray-300">Drag and drop audio file here</p>
                        <p className="text-sm text-gray-500">or</p>
                        <input
                            type="file"
                            onChange={(e) => handleUpload(e.target.files[0])}
                            className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 bg-transparent"
                        />
                    </div>
                </div>
            )}

            {activeTab === "library" && (
                <div className="grid grid-cols-12 gap-6">
                    {/* File List */}
                    <div className="col-span-12 lg:col-span-5 bg-gray-900 rounded-xl overflow-hidden border border-gray-800">
                        <div className="p-4 border-b border-gray-800 bg-gray-900/80">
                            <h2 className="text-lg font-semibold text-gray-200">Samples Library</h2>
                        </div>
                        <div className="overflow-y-auto max-h-[600px]">
                            {loading ? (
                                <div className="p-8 text-center text-gray-500">Loading library...</div>
                            ) : files.length === 0 ? (
                                <div className="p-8 text-center text-gray-500">Library is empty. Upload some files!</div>
                            ) : (
                                <table className="w-full text-left">
                                    <thead className="bg-gray-800 text-xs uppercase text-gray-400">
                                        <tr>
                                            <th className="px-4 py-3">File</th>
                                            <th className="px-4 py-3">Type</th>
                                            <th className="px-4 py-3">Status</th>
                                            <th className="px-4 py-3">Info</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {files.map((file, i) => (
                                            <tr
                                                key={i}
                                                onClick={() => setSelectedFile(file)}
                                                className={`cursor-pointer transition-colors hover:bg-gray-800 ${selectedFile?.filename === file.filename ? "bg-gray-800/80 border-l-4 border-blue-500" : ""}`}
                                            >
                                                <td className="px-4 py-3 font-medium truncate max-w-[150px]" title={file.filename}>
                                                    {file.filename}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`px-2 py-0.5 rounded text-xs ${file.label === "organic" ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"}`}>
                                                        {file.label}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3">
                                                    {file.analyzed ? (
                                                        <span className={`font-bold ${getScoreColor(file.detection_score)}`}>
                                                            {(file.detection_score * 100).toFixed(0)}%
                                                        </span>
                                                    ) : (
                                                        <span className="text-gray-500 italic text-xs">Pending</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-gray-500">
                                                    <ChevronRight className="w-4 h-4" />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>

                    {/* Inspector Panel */}
                    <div className="col-span-12 lg:col-span-7 bg-gray-900 rounded-xl border border-gray-800 min-h-[400px]">
                        {selectedFile ? (
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-100 to-gray-400 mb-1">
                                            Micro-Inspector
                                        </h2>
                                        <p className="text-gray-400 font-mono text-sm">{selectedFile.filename}</p>
                                    </div>

                                    <div>
                                        {!selectedFile.analyzed ? (
                                            <button
                                                onClick={() => analyzeFile(selectedFile)}
                                                disabled={analyzing}
                                                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-all"
                                            >
                                                <Microscope className="w-4 h-4" />
                                                <span>{analyzing ? "Analyzing..." : "Run Analysis"}</span>
                                            </button>
                                        ) : (
                                            <div className="flex flex-col items-end">
                                                <span className="text-xs text-gray-500 uppercase tracking-widest">Risk Score</span>
                                                <span className={`text-3xl font-bold ${getScoreColor(selectedFile.detection_score)}`}>
                                                    {(selectedFile.detection_score * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {selectedFile.analyzed && selectedFile.sensor_details ? (
                                    <div className="grid grid-cols-1 gap-4">
                                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-4">Sensor Fingerprint</h3>

                                        {Object.entries(selectedFile.sensor_details).map(([sensorName, data]) => (
                                            <div key={sensorName} className="bg-gray-950/50 rounded-lg p-4 border border-gray-800 transition-all hover:border-gray-700">
                                                <div className="flex justify-between items-center mb-2">
                                                    <div className="flex items-center space-x-2">
                                                        {data.passed ? (
                                                            <CheckCircle className="w-5 h-5 text-green-500" />
                                                        ) : (
                                                            <AlertTriangle className="w-5 h-5 text-red-500" />
                                                        )}
                                                        <span className="font-medium text-gray-200">{sensorName}</span>
                                                    </div>
                                                    <span className={`text-sm px-2 py-0.5 rounded ${data.passed ? 'bg-green-900/20 text-green-400' : 'bg-red-900/20 text-red-400'}`}>
                                                        {data.passed ? "PASS" : "FAIL"}
                                                    </span>
                                                </div>

                                                {/* Details */}
                                                <div className="ml-7 text-sm space-y-1">
                                                    <p className="text-gray-400">{data.detail}</p>
                                                    {data.metadata && (
                                                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs font-mono bg-black/20 p-2 rounded">
                                                            {Object.entries(data.metadata).map(([key, val]) => (
                                                                <div key={key} className="flex justify-between">
                                                                    <span className="text-gray-500">{key}:</span>
                                                                    <span className="text-gray-300">{typeof val === 'number' ? val.toFixed(4) : String(val)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : selectedFile.analyzed ? (
                                    <div className="p-8 text-center bg-gray-800/50 rounded-lg border border-dashed border-gray-700">
                                        <p className="text-gray-400">No detailed physics metrics available for this file.</p>
                                        <p className="text-xs text-gray-600 mt-2">Try re-running analysis.</p>
                                        <button onClick={() => analyzeFile(selectedFile)} className="mt-4 text-blue-400 hover:text-blue-300 text-sm">Force Re-analyze</button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center p-12 text-center h-64 border-2 border-dashed border-gray-800 rounded-lg bg-gray-800/20">
                                        <Microscope className="w-12 h-12 text-gray-600 mb-4" />
                                        <p className="text-gray-400">Run analysis to see micro-level sensor data.</p>
                                    </div>
                                )}

                                {/* Simulation Controls */}
                                <div className="mt-6 p-4 bg-gray-950/30 rounded-lg border border-gray-800">
                                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center">
                                        <Signal className="w-3 h-3 mr-2" />
                                        Telephony Simulation
                                    </h3>
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => simulateNetwork(selectedFile, "landline")}
                                            disabled={simulating}
                                            className="flex-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium text-gray-300 transition-colors flex items-center justify-center space-x-2"
                                        >
                                            <Phone className="w-3 h-3" />
                                            <span>Landline</span>
                                        </button>
                                        <button
                                            onClick={() => simulateNetwork(selectedFile, "mobile")}
                                            disabled={simulating}
                                            className="flex-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium text-gray-300 transition-colors flex items-center justify-center space-x-2"
                                        >
                                            <Signal className="w-3 h-3" />
                                            <span>Mobile (GSM)</span>
                                        </button>
                                        <button
                                            onClick={() => simulateNetwork(selectedFile, "voip")}
                                            disabled={simulating}
                                            className="flex-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium text-gray-300 transition-colors flex items-center justify-center space-x-2"
                                        >
                                            <Wifi className="w-3 h-3" />
                                            <span>VoIP</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                <FileAudio className="w-16 h-16 mb-4 opacity-20" />
                                <p>Select a sample to inspect</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Laboratory;
