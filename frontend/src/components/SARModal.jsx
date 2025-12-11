import React from 'react';

const styles = {
    overlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
    },
    modal: {
        background: '#0A0A0F',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '700px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        fontFamily: '"JetBrains Mono", monospace',
        color: '#F0F0F2',
    },
    header: {
        padding: '1.5rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        background: 'rgba(255, 255, 255, 0.02)',
    },
    title: {
        fontSize: '1rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        color: '#F0F0F2',
        marginBottom: '0.5rem',
    },
    meta: {
        fontSize: '0.75rem',
        color: 'rgba(240, 240, 242, 0.6)',
        lineHeight: 1.5,
    },
    content: {
        padding: '2rem',
        overflowY: 'auto',
        fontSize: '0.85rem',
        lineHeight: 1.6,
    },
    section: {
        marginBottom: '2rem',
    },
    sectionTitle: {
        fontSize: '0.75rem',
        color: 'rgba(240, 240, 242, 0.4)',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        marginBottom: '0.75rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        paddingBottom: '0.25rem',
    },
    row: {
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '0.5rem',
    },
    label: {
        color: 'rgba(240, 240, 242, 0.6)',
    },
    value: {
        color: '#F0F0F2',
        fontWeight: 500,
    },
    warning: {
        color: '#F43F5E',
        background: 'rgba(244, 63, 94, 0.1)',
        padding: '0.5rem',
        borderRadius: '4px',
        marginTop: '0.5rem',
        fontSize: '0.8rem',
        border: '1px solid rgba(244, 63, 94, 0.2)',
    },
    success: {
        color: '#059669',
        background: 'rgba(5, 150, 105, 0.1)',
        padding: '0.5rem',
        borderRadius: '4px',
        marginTop: '0.5rem',
        fontSize: '0.8rem',
        border: '1px solid rgba(5, 150, 105, 0.2)',
    },
    actions: {
        padding: '1.5rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '1rem',
        background: 'rgba(255, 255, 255, 0.02)',
    },
    closeBtn: {
        background: 'transparent',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        color: '#F0F0F2',
        padding: '0.5rem 1rem',
        borderRadius: '4px',
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: '0.8rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
    },
    printBtn: {
        background: '#E5B956',
        border: 'none',
        color: '#0A0A0F',
        padding: '0.5rem 1rem',
        borderRadius: '4px',
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: '0.8rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
    }
};

const SARModal = ({ result, onClose }) => {
    if (!result) return null;

    const incidentId = `SAR-${Math.floor(Date.now() / 1000)}-${Math.floor(Math.random() * 1000)}`;
    const timestamp = new Date().toISOString();

    // Extract metrics
    const jitter = result.physics_engine?.latency_jitter?.value_ms || 0;
    const vocalCrypt = result.physics_engine?.vocal_crypt?.value || 0;
    const geo = result.physics_engine?.geo_location?.value || 0;
    const riskLevel = result.verdict?.risk_level || "UNKNOWN";
    const isFail = riskLevel === "CRITICAL" || riskLevel === "HIGH";

    const findings = [];
    if (jitter > 200) findings.push("Network latency variance indicates potential routing anomalies (VPN/Proxy).");
    if (vocalCrypt === 0) findings.push("Spectral coherence analysis reveals potential vocoder artifacts.");
    if (geo === 0) findings.push("Geolocation metadata mismatch with carrier routing path.");
    if (findings.length === 0) findings.push("No significant technical anomalies detected.");

    return (
        <div style={styles.overlay} onClick={onClose}>
            <div style={styles.modal} onClick={e => e.stopPropagation()}>
                <div style={styles.header}>
                    <div>
                        <div style={styles.title}>Suspicious Activity Report</div>
                        <div style={styles.meta}>Incident ID: {incidentId}</div>
                        <div style={styles.meta}>Date: {timestamp}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{
                            ...styles.title,
                            color: isFail ? '#F43F5E' : '#059669',
                            border: `1px solid ${isFail ? '#F43F5E' : '#059669'}`,
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            display: 'inline-block'
                        }}>
                            {riskLevel}
                        </div>
                    </div>
                </div>

                <div style={styles.content}>
                    <div style={styles.section}>
                        <div style={styles.sectionTitle}>01 // Executive Summary</div>
                        <p style={{ marginBottom: '0.5rem' }}>
                            Sonotheia operational analysis has flagged this session with a <strong>{riskLevel}</strong> risk designation.
                            {isFail
                                ? " Technical evidence suggests high probability of synthetic media manipulation or identity spoofing."
                                : " Bio-acoustic markers are consistent with authentic human speech."}
                        </p>
                        <div style={isFail ? styles.warning : styles.success}>
                            Recommended Action: {isFail ? "IMMEDIATE BLOCK / ESCALATE TO FRAUD OPS" : "ALLOW / MONITOR"}
                        </div>
                    </div>

                    <div style={styles.section}>
                        <div style={styles.sectionTitle}>02 // Technical Evidence Manifest</div>
                        {findings.map((f, i) => (
                            <div key={i} style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                                <span style={{ color: '#E5B956' }}>❯</span>
                                <span>{f}</span>
                            </div>
                        ))}
                        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                            <div style={styles.row}>
                                <span style={styles.label}>Jitter Metric:</span>
                                <span style={styles.value}>{jitter}ms</span>
                            </div>
                            <div style={styles.row}>
                                <span style={styles.label}>Signal Integrity:</span>
                                <span style={styles.value}>{vocalCrypt === 1 ? "Valid" : "Corrupt"}</span>
                            </div>
                            <div style={styles.row}>
                                <span style={styles.label}>Origin Routing:</span>
                                <span style={styles.value}>{geo === 1 ? "Verified" : "Mismatch"}</span>
                            </div>
                        </div>
                    </div>

                    <div style={styles.section}>
                        <div style={styles.sectionTitle}>03 // Chain of Custody</div>
                        <div style={styles.row}>
                            <span style={styles.label}>Analysis Engine:</span>
                            <span style={styles.value}>Sonotheia Physics Core v2.4.1</span>
                        </div>
                        <div style={styles.row}>
                            <span style={styles.label}>Processing Node:</span>
                            <span style={styles.value}>us-east-1a-secure</span>
                        </div>
                        <div style={styles.row}>
                            <span style={styles.label}>Session Hash:</span>
                            <span style={styles.value}>{Math.random().toString(36).substring(7).toUpperCase()}...</span>
                        </div>
                    </div>
                </div>

                <div style={styles.actions}>
                    <button style={styles.closeBtn} onClick={onClose}>Close</button>
                    <button style={styles.printBtn} onClick={() => alert("Printing SAR Report...")}>Export PDF</button>
                </div>
            </div>
        </div>
    );
};

export default SARModal;
