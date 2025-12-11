import React, { useState } from 'react';

const MetricBar = ({ label, value, status, detail }) => (
    <div className="mb-6">
        <div className="flex justify-between mb-1">
            <span className="font-medium text-gray-300">{label}</span>
            <span className={`font-bold ${status === 'FAIL' ? 'text-red-500' : 'text-green-500'}`}>
                {status} ({value})
            </span>
        </div>
        <p className="text-xs text-gray-500 mb-2">{detail}</p>
        <div className="w-full bg-gray-700 rounded-full h-2">
            <div
                className={`${status === 'FAIL' ? 'bg-red-500' : status === 'WARNING' ? 'bg-yellow-500' : 'bg-green-500'} h-2 rounded-full transition-all duration-1000`}
                style={{ width: '100%' }}
            ></div>
        </div>
    </div>
);

const DraftAuditReport = ({ result }) => {
    const physics = result.physics_engine;
    const compliance = result.compliance_audit;

    const handleDownloadReport = async () => {
        // ... (Download logic would need update for backend PDF generator, currently likely broken but UI stays same)
        alert("PDF Generation is pending update to new schema.");
    };

    return (
        <div className="h-full flex flex-col">
            <div className="mb-8 border-b border-gray-700 pb-4">
                <h3 className="text-2xl font-bold font-mono text-gray-100 flex items-center">
                    <span className="text-blue-400 mr-2">📄</span> Forensic Audit
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                    ID: {result.report_id} | Ref: {compliance.nist_800_63b.reference}
                </p>
            </div>

            <div className="flex-grow overflow-y-auto pr-2">
                {/* Physics Engine Analysis */}
                <div className="mb-10">
                    <h4 className="text-sm font-semibold text-gray-400 uppercase mb-6 tracking-wide border-l-2 border-blue-500 pl-3">
                        Physics Engine Telemetry
                    </h4>

                    <MetricBar
                        label="Spectral Flatness"
                        value={physics.spectral_flatness.value}
                        status={physics.spectral_flatness.status}
                        detail={physics.spectral_flatness.analysis}
                    />
                    <MetricBar
                        label="Breath Cadence"
                        value={`${physics.breath_cadence.detected_breaths_per_min} bpm`}
                        status={physics.breath_cadence.status}
                        detail={physics.breath_cadence.analysis}
                    />
                    <MetricBar
                        label="Latency Jitter"
                        value={`${physics.latency_jitter.value_ms}ms`}
                        status={physics.latency_jitter.status}
                        detail={physics.latency_jitter.analysis}
                    />
                </div>

                {/* Compliance Violations */}
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700 mb-6">
                    <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
                        Compliance & Violations
                    </h4>
                    <div className="space-y-4">
                        <div className="flex items-start">
                            <span className={`${compliance.nist_800_63b.violation_code.includes('FAIL') ? 'text-red-400' : 'text-green-400'} font-mono font-bold mr-3 text-sm`}>
                                [{compliance.nist_800_63b.violation_code}]
                            </span>
                            <span className="text-sm text-gray-300">
                                {compliance.nist_800_63b.description}
                            </span>
                        </div>
                        <div className="flex items-start">
                            <span className={`${compliance.eu_ai_act.article_50_compliant ? 'text-green-400' : 'text-red-400'} font-mono font-bold mr-3 text-sm`}>
                                [EU-AI-ACT]
                            </span>
                            <span className="text-sm text-gray-300">
                                Transparency: {compliance.eu_ai_act.transparency_notice}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Export Action */}
            <div className="mt-auto pt-6 border-t border-gray-700">
                <div className="text-xs text-center text-gray-500 mb-2">
                    generated via {result.simulation_meta.scenario_type}
                </div>
                <button
                    onClick={handleDownloadReport}
                    className="w-full py-4 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-lg font-bold text-gray-300 flex items-center justify-center opacity-50 cursor-not-allowed"
                    disabled
                >
                    <span className="mr-2">⬇</span> Download PDF (Maintenance)
                </button>
            </div>
        </div>
    );
};

export default DraftAuditReport;
