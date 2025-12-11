import React, { useMemo, useRef, useEffect, useState } from 'react';
import SARModal from './SARModal';


const styles = {
    container: {
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        padding: '1.5rem',
        background: 'rgba(5, 5, 8, 0.9)',
        color: '#F0F0F2',
        fontFamily: '"Inter", system-ui, sans-serif',
        overflowY: 'auto',
    },
    sectionLabel: {
        fontSize: '0.65rem',
        fontWeight: 700,
        color: 'rgba(240, 240, 242, 0.5)',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
        marginBottom: '0.5rem',
    },
    chartCard: {
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '1rem',
        padding: '1.25rem',
        minHeight: '250px',
    },
    chartHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem',
    },
    chartTitle: {
        fontSize: '0.85rem',
        fontWeight: 600,
        color: '#F0F0F2',
    },
    chartContainer: {
        height: '180px',
        width: '100%',
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '0.75rem',
        flex: 1,
    },
    metricCard: {
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.005) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        padding: '1rem',
        borderRadius: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
    },
    metricLabel: {
        fontSize: '0.65rem',
        fontWeight: 700,
        color: 'rgba(240, 240, 242, 0.5)',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        marginBottom: '0.35rem',
    },
    metricValue: {
        fontSize: '1.5rem',
        fontWeight: 700,
        fontFamily: '"JetBrains Mono", monospace',
    },
    metricSub: {
        marginTop: '0.75rem',
        fontSize: '0.7rem',
        color: 'rgba(240, 240, 242, 0.5)',
        background: 'rgba(0, 0, 0, 0.3)',
        padding: '0.5rem',
        borderRadius: '0.35rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
    },
};

const MetricCard = React.memo(({ label, value, subLabel, subValue, valueColor = '#F0F0F2' }) => (
    <div style={styles.metricCard}>
        <div>
            <div style={styles.metricLabel}>{label}</div>
            <div style={{ ...styles.metricValue, color: valueColor }}>{value}</div>
        </div>
        <div style={styles.metricSub}>
            <span style={{ color: 'rgba(240, 240, 242, 0.7)', fontWeight: 600 }}>{subLabel}</span>
            <span style={{ opacity: 0.5 }}>|</span>
            <span>{subValue}</span>
        </div>
    </div>
));

const AlgorithmJudgment = React.memo(({ result }) => {
    const physics = result?.physics_engine || {};
    const jitter = physics.latency_jitter?.value_ms || 0;
    const vocalCrypt = physics.vocal_crypt?.value || 0;
    const geo = physics.geo_location?.value || 0;

    const isFail = jitter > 200 || vocalCrypt === 0 || geo === 0;

    return (
        <div style={{ ...styles.chartCard, display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '1rem' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={styles.sectionLabel}>ALGORITHMIC JUDGMENT</div>
                {isFail ?
                    <div style={{
                        color: '#F43F5E',
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '4px 8px',
                        background: 'rgba(244, 63, 94, 0.1)',
                        borderRadius: '4px',
                        textAlign: 'right',
                        lineHeight: '1',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-end',
                        gap: '2px'
                    }}>
                        <span>STEP-UP AUTH</span>
                        <span style={{ fontSize: '0.85rem', fontWeight: 900, letterSpacing: '0.05em' }}>REQUIRED</span>
                    </div> :
                    <div style={{ color: '#059669', fontSize: '0.65rem', fontWeight: 700, padding: '2px 6px', background: 'rgba(52, 211, 153, 0.1)', borderRadius: '4px' }}>PASS</div>
                }
            </div>

            {/* Checklist */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.7rem', fontFamily: '"JetBrains Mono", monospace' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: jitter > 200 ? '#F43F5E' : '#059669' }}>
                    <span>LATENCY JITTER</span>
                    <span>{jitter}ms {jitter > 200 ? "[FAIL]" : "[OK]"}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: vocalCrypt === 0 ? '#F43F5E' : '#059669' }}>
                    <span>VOCAL CRYPT</span>
                    <span>{vocalCrypt === 0 ? "INVALID" : "VALID"}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: geo === 0 ? '#F43F5E' : '#059669' }}>
                    <span>GEOLOCATION</span>
                    <span>{geo === 0 ? "MISMATCH" : "MATCH"}</span>
                </div>
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', fontSize: '0.65rem', color: 'rgba(240,240,242,0.5)' }}>
                Multi-vector analysis indicates {isFail ? "synthetic\u00A0origin" : "authentic\u00A0signal"}
            </div>
        </div>
    );
});

const Spectrogram = React.memo(() => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const animationRef = useRef(null);
    const [showOverlay, setShowOverlay] = useState(false);
    const [scanComplete, setScanComplete] = useState(false);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d', { alpha: false });

        const img = new Image();
        img.src = '/assets/spectrogram-matrix.png';

        let scanLineY = 0;
        let isScanned = false; // Local ref for animation loop

        const draw = () => {
            if (!canvas) return;
            const width = canvas.width;
            const height = canvas.height;

            // Clear with dark greenish-black
            ctx.fillStyle = '#020502';
            ctx.fillRect(0, 0, width, height);

            if (img.complete) {
                // 1. Draw The Specific "Green Waveform" Image
                const zoomFactor = 1.15;

                ctx.save();
                // "Subliminal" look but high contrast to pop the bright horizontal waves
                // Removing blur to keep horizontal lines sharp
                ctx.globalAlpha = 0.5;
                ctx.filter = 'contrast(140%) brightness(0.9)';

                // Add subtle green glow to the texture itself
                ctx.shadowColor = 'rgba(52, 211, 153, 0.4)';
                ctx.shadowBlur = 15;

                // Draw image to cover the canvas
                ctx.drawImage(
                    img,
                    0, 0, img.width, img.height,
                    -width * 0.075, -height * 0.075, width * 1.15, height * 1.15
                );
                ctx.restore();

                // 2. Green Color Grade Overlay
                ctx.save();
                ctx.globalCompositeOperation = 'multiply';
                ctx.fillStyle = 'rgba(52, 211, 153, 0.15)';
                ctx.fillRect(0, 0, width, height);
                ctx.restore();

                // 3. Scanline Animation (Single Pass)
                if (!isScanned) {
                    scanLineY += 3.0; // Faster scan
                    if (scanLineY > height + 50) {
                        isScanned = true;
                        // setScanComplete(true); // Can trigger React state if needed, but risky inside AnimFrame
                    }

                    // Draw scanline beam
                    const gradient = ctx.createLinearGradient(0, scanLineY - 15, 0, scanLineY + 15);
                    gradient.addColorStop(0, 'rgba(52, 211, 153, 0)');
                    gradient.addColorStop(0.5, 'rgba(52, 211, 153, 0.9)');
                    gradient.addColorStop(1, 'rgba(52, 211, 153, 0)');

                    ctx.fillStyle = gradient;
                    ctx.fillRect(0, scanLineY - 15, width, 30);
                }
            }

            // 4. Tech Grid Overlay (Visual Hierarchy Adjustment)
            ctx.save();
            ctx.lineWidth = 1;
            ctx.beginPath();

            // Horizontal Frequency Lines - KEEP BRIGHT/VISIBLE
            ctx.strokeStyle = 'rgba(52, 211, 153, 0.25)'; // Higher opacity
            [0.25, 0.5, 0.75].forEach(fraction => {
                const y = height * fraction;
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
            });
            ctx.stroke();

            // Vertical Time Lines - DIM SIGNIFICANTLY
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(52, 211, 153, 0.03)'; // Very low opacity (subliminal)
            for (let i = 1; i < 12; i++) {
                const x = (width / 12) * i;
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
            }
            ctx.stroke();
            ctx.restore();

            // 4b. Vignette / CRT corners
            const rad = width * 0.9;
            const vignette = ctx.createRadialGradient(width / 2, height / 2, rad / 2, width / 2, height / 2, rad);
            vignette.addColorStop(0, 'rgba(0,0,0,0)');
            vignette.addColorStop(1, 'rgba(0,0,0,0.9)');
            ctx.fillStyle = vignette;
            ctx.fillRect(0, 0, width, height);

            animationRef.current = requestAnimationFrame(draw);
        };

        img.onload = draw;
        // Start loop even if image not loaded yet (will just draw bg)
        draw();

        // Resize handler
        const resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                if (canvas.width !== width || canvas.height !== height) {
                    canvas.width = width;
                    canvas.height = height;
                }
            }
        });

        if (containerRef.current) {
            resizeObserver.observe(containerRef.current);
        }

        return () => {
            resizeObserver.disconnect();
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
        };
    }, []);

    const handleOverlayClick = () => {
        // Toggle or set true
        setShowOverlay(true);
    };

    return (
        <div
            ref={containerRef}
            onClick={handleOverlayClick}
            style={{
                width: '100%',
                height: '100%',
                position: 'relative',
                overflow: 'hidden',
                cursor: 'pointer'
            }}
        >
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />

            {/* Click Overlay */}
            {showOverlay && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'rgba(5, 5, 8, 0.85)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(52, 211, 153, 0.3)',
                    padding: '1.5rem',
                    borderRadius: '8px',
                    width: '80%',
                    maxWidth: '400px',
                    boxShadow: '0 0 40px rgba(0,0,0,0.8), 0 0 10px rgba(52, 211, 153, 0.2)',
                    animation: 'fadeIn 0.3s ease-out'
                }}>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '1rem',
                        borderBottom: '1px solid rgba(255,255,255,0.1)',
                        paddingBottom: '0.5rem'
                    }}>
                        <span style={{
                            color: '#059669',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            letterSpacing: '0.1em',
                            display: 'flex',
                            gap: '0.5rem',
                            alignItems: 'center'
                        }}>
                            <span style={{ width: '8px', height: '8px', background: '#059669', borderRadius: '50%' }}></span>
                            ANALYSIS COMPLETE
                        </span>
                        <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)' }}>
                            T+0.04s
                        </span>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#F0F0F2', fontSize: '0.9rem', fontWeight: 600 }}>Synthetic Pattern Detected</h4>
                        <p style={{ margin: 0, fontSize: '0.8rem', color: 'rgba(240, 240, 242, 0.7)', lineHeight: 1.5 }}>
                            Micro-tremor analysis reveals unnatural periodicity in high-frequency bands (4-8kHz). Phase coherence suggests algorithmic regeneration.
                        </p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                        <div style={{ background: 'rgba(52, 211, 153, 0.05)', padding: '0.5rem', borderRadius: '4px', border: '1px solid rgba(52, 211, 153, 0.1)' }}>
                            <div style={{ fontSize: '0.65rem', color: 'rgba(52, 211, 153, 0.8)', textTransform: 'uppercase' }}>Confidence</div>
                            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#059669', fontFamily: '"JetBrains Mono"' }}>98.2%</div>
                        </div>
                        <div style={{ background: 'rgba(244, 63, 94, 0.05)', padding: '0.5rem', borderRadius: '4px', border: '1px solid rgba(244, 63, 94, 0.1)' }}>
                            <div style={{ fontSize: '0.65rem', color: 'rgba(244, 63, 94, 0.8)', textTransform: 'uppercase' }}>Threat Level</div>
                            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#F43F5E', fontFamily: '"JetBrains Mono"' }}>CRITICAL</div>
                        </div>
                    </div>

                    <button
                        onClick={(e) => { e.stopPropagation(); setShowOverlay(false); }}
                        style={{
                            width: '100%',
                            padding: '0.6rem',
                            background: 'transparent',
                            border: '1px solid rgba(255,255,255,0.15)',
                            color: 'rgba(255,255,255,0.6)',
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            borderRadius: '4px',
                            transition: 'all 0.2s'
                        }}
                        onMouseOver={e => { e.target.style.borderColor = 'rgba(255,255,255,0.3)'; e.target.style.color = '#fff'; }}
                        onMouseOut={e => { e.target.style.borderColor = 'rgba(255,255,255,0.15)'; e.target.style.color = 'rgba(255,255,255,0.6)'; }}
                    >
                        DISMISS
                    </button>

                    <style>{`
                        @keyframes fadeIn {
                            from { opacity: 0; transform: translate(-50%, -45%); }
                            to { opacity: 1; transform: translate(-50%, -50%); }
                        }
                    `}</style>
                </div>
            )}
        </div>
    );
});

const TechnicalEvidenceLog = React.memo(({ result }) => {
    // Mock log entries to simulate a real-time forensic audit trace
    // In a real app, this would come from result.evidence_log or similar
    const logs = useMemo(() => [
        { time: '00:00:01.420', source: 'PHYSICS_ENGINE', level: 'WARN', message: 'Phase discontinuity > 45deg detected' },
        { time: '00:00:02.150', source: 'LPC_ANALYSIS', level: 'CRIT', message: 'Residual signal below noise floor' },
        { time: '00:00:03.800', source: 'VOCAL_TRACT', level: 'INFO', message: 'Formant tracking: F1/F2 anomaly' },
        { time: '00:00:04.100', source: 'FUSION_CORE', level: 'WARN', message: 'Synthetic probability > 0.89' },
        { time: '00:00:04.350', source: 'SAR_GENERATOR', level: 'INFO', message: 'Audit log package compiled' }
    ], []);

    return (
        <div style={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '0.65rem',
            color: 'rgba(240, 240, 242, 0.8)',
            overflowY: 'auto',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
            paddingRight: '0.5rem' // Metric card padding
        }}>
            {logs.map((log, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '60px 35px 1fr', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '0.25rem' }}>
                    <span style={{ color: 'rgba(255, 255, 255, 0.3)' }}>{log.time}</span>
                    <span style={{ color: log.level === 'CRIT' ? '#F43F5E' : log.level === 'WARN' ? '#E5B956' : '#059669', fontWeight: 600 }}>{log.level}</span>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.message}</span>
                </div>
            ))}
            <div style={{ marginTop: 'auto', paddingTop: '0.5rem', color: '#059669', fontWeight: 600 }}>
                <span style={{ animation: 'blink 1s infinite' }}>_</span> END OF STREAM
            </div>
        </div>
    );
});

const ForensicDisplay = ({ result }) => {
    // Generate chart data (memoized) for other metrics if needed, but Spectrogram is now texture-based
    // and Spectral Flatness is removed.

    // Physics & Verdict Data extraction
    const physics = result?.physics_engine || {};
    const verdict = result?.verdict || {};
    const [showSAR, setShowSAR] = useState(false);

    const getStatusColor = (value, passValue = 1.0) =>
        value === passValue ? '#059669' : '#F43F5E';

    return (
        <div style={styles.container}>
            <div style={styles.sectionLabel}>Forensic Analysis</div>

            {/* TOP: Spectrogram (Full Width) */}
            <div style={{ ...styles.chartCard, padding: '0', overflow: 'hidden', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
                    <span style={styles.chartTitle}>SPECTROGRAM ANALYSIS (8kHz Bandwidth)</span>
                </div>
                <div style={{ flex: 1, position: 'relative' }}>
                    <Spectrogram />
                    {/* Overlay Labels */}
                    <div style={{ position: 'absolute', left: '8px', top: '8px', fontSize: '10px', color: 'rgba(52, 211, 153, 0.7)', fontFamily: 'monospace', pointerEvents: 'none' }}>8kHz</div>
                    <div style={{ position: 'absolute', left: '8px', bottom: '8px', fontSize: '10px', color: 'rgba(52, 211, 153, 0.7)', fontFamily: 'monospace', pointerEvents: 'none' }}>0Hz</div>
                </div>
            </div>

            {/* GRID: 2x2 Layout */}
            <div style={styles.grid}>
                {/* 1. Technical Evidence Log (Replaces Spectral Flatness) */}
                <div style={styles.chartCard}>
                    <div style={styles.chartHeader}>
                        <span style={styles.chartTitle}>Technical Evidence Log</span>
                    </div>
                    <div style={{ height: '140px', width: '100%' }}>
                        <TechnicalEvidenceLog result={result} />
                    </div>
                </div>

                {/* 2. Algorithm-Aided Judgment (Replaces VocalCrypt) */}
                <AlgorithmJudgment result={result} />

                {/* 3. Metric: Jitter */}
                <MetricCard
                    label="Latency Jitter"
                    value={`${physics.latency_jitter?.value_ms || 0}ms`}
                    valueColor={physics.latency_jitter?.value_ms > 200 ? '#F43F5E' : '#059669'}
                    subLabel="Check"
                    subValue={physics.latency_jitter?.value_ms > 200 ? "GPU Pause" : "Real-time"}
                />

                {/* 4. Metric: Risk */}
                <MetricCard
                    label="Risk Level"
                    value={verdict.risk_level || "N/A"}
                    valueColor={verdict.risk_level === 'CRITICAL' ? '#F43F5E' : '#E5B956'}
                    subLabel="Verdict"
                    subValue={verdict.final_determination || "PENDING"}
                />
            </div>

            {/* Generate Report Action */}
            <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                    onClick={() => setShowSAR(true)}
                    style={{
                        background: 'transparent',
                        border: '1px solid rgba(229, 185, 86, 0.4)',
                        color: '#E5B956',
                        padding: '0.6rem 1.2rem',
                        borderRadius: '0.4rem',
                        fontFamily: '"JetBrains Mono", monospace',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        transition: 'all 0.2s',
                        opacity: 0.8
                    }}
                    onMouseOver={e => { e.currentTarget.style.background = 'rgba(229, 185, 86, 0.1)'; e.currentTarget.style.opacity = '1'; }}
                    onMouseOut={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.opacity = '0.8'; }}
                >
                    <span style={{ fontSize: '1rem' }}>📋</span> GENERATE SAR REPORT
                </button>
            </div>

            {/* Modal */}
            {showSAR && <SARModal result={result} onClose={() => setShowSAR(false)} />}
        </div>
    );
};

export default ForensicDisplay;
