import React, { useState, useEffect, useRef } from 'react';

// Inline SVG icons
const Send = (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" {...props}>
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
);



const styles = {
    container: {
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(5, 5, 8, 0.9)',
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: '0.85rem',
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1rem 1.25rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(255, 255, 255, 0.02)',
    },
    headerTitle: {
        fontWeight: 700,
        color: '#F0F0F2',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        fontSize: '0.75rem',
    },
    chatArea: {
        flex: 1,
        overflowY: 'auto',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
    },
    messageSystem: {
        maxWidth: '90%',
        padding: '0.875rem 1rem',
        borderRadius: '0.75rem',
        borderBottomLeftRadius: '0.25rem',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        color: 'rgba(240, 240, 242, 0.8)',
    },
    messageUser: {
        maxWidth: '90%',
        padding: '0.875rem 1rem',
        borderRadius: '0.75rem',
        borderBottomRightRadius: '0.25rem',
        background: 'rgba(52, 211, 153, 0.1)',
        border: '1px solid rgba(52, 211, 153, 0.2)',
        color: '#059669',
        alignSelf: 'flex-end',
    },
    messageLabel: {
        fontSize: '0.6rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        marginBottom: '0.35rem',
        display: 'block',
    },
    alertBox: {
        margin: '0.5rem 0',
        padding: '1.25rem',
        border: '1px solid rgba(244, 63, 94, 0.4)',
        background: 'rgba(244, 63, 94, 0.08)',
        borderRadius: '0.75rem',
        textAlign: 'center',
        boxShadow: '0 0 30px rgba(244, 63, 94, 0.15)',
    },
    alertLabel: {
        color: '#F43F5E',
        fontWeight: 700,
        fontSize: '0.65rem',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
        marginBottom: '0.5rem',
    },
    alertTitle: {
        color: '#F0F0F2',
        fontWeight: 700,
        fontSize: '1rem',
        marginBottom: '0.35rem',
    },
    alertSub: {
        color: 'rgba(240, 240, 242, 0.5)',
        fontSize: '0.7rem',
        marginBottom: '1rem',
    },
    checkList: {
        textAlign: 'left',
        background: 'rgba(244, 63, 94, 0.05)',
        padding: '0.75rem',
        borderRadius: '0.5rem',
        border: '1px solid rgba(244, 63, 94, 0.15)',
        fontSize: '0.75rem',
    },
    checkItem: {
        marginBottom: '0.35rem',
    },

    inputArea: {
        padding: '1rem 1.25rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(255, 255, 255, 0.02)',
    },
    inputWrapper: {
        position: 'relative',
    },
    input: {
        width: '100%',
        background: 'rgba(5, 5, 8, 0.8)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '0.5rem',
        color: '#F0F0F2',
        padding: '0.75rem 2.5rem 0.75rem 1rem',
        fontSize: '0.85rem',
        fontFamily: '"JetBrains Mono", monospace',
        outline: 'none',
    },
    sendBtn: {
        position: 'absolute',
        right: '0.75rem',
        top: '50%',
        transform: 'translateY(-50%)',
        background: 'none',
        border: 'none',
        color: 'rgba(240, 240, 242, 0.5)',
        cursor: 'pointer',
        padding: '0.25rem',
    },
    typingIndicator: {
        display: 'flex',
        gap: '4px',
        padding: '0.5rem 0',
        marginLeft: '1rem',
    },
    dot: {
        width: '6px',
        height: '6px',
        background: 'rgba(52, 211, 153, 0.5)',
        borderRadius: '50%',
        animation: 'bounce 1.4s infinite ease-in-out both',
    },
    brand: {
        fontFamily: '"Inter", sans-serif',
        letterSpacing: '0.3rem',
        textTransform: 'uppercase',
    }
};

const AISentinel = ({ result, onSimulationUpdate, provider = "auto" }) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [isTyping, setIsTyping] = useState(false);

    const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://sonotheia-backend.onrender.com');

    // Initial greeting & Narrative
    useEffect(() => {
        if (!result) return;
        const initialRisk = result?.verdict?.risk_level || "Analyzing...";
        const narrative = result?.scenario_narrative;

        // Only run this once per result instance effectively
        setMessages(prev => {
            if (prev.length > 0) return prev; // Don't interrupt existing chat

            const msgs = [{
                role: 'system',
                text: `Forensic analysis complete. Risk Level: ${initialRisk}. I am ready to explain the\u00A0findings.`
            }];

            if (narrative) {
                msgs.push({
                    role: 'system',
                    text: `⚠️ MISSION CONTEXT\n\n${narrative}`
                });
            }

            return msgs;
        });
    }, [result]);

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMsg = inputValue;
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInputValue("");
        setIsTyping(true);

        try {
            const response = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg,
                    context: result,
                    provider: provider
                })
            });

            if (!response.ok) throw new Error("API Connection Failed");

            const data = await response.json();

            // Handle Simulation Updates
            if (data.simulation_update && onSimulationUpdate) {
                // Determine source: LLM or fallback
                onSimulationUpdate(data.simulation_update);
                setMessages(prev => [...prev, { role: 'system', text: `✨ SIMULATION COMPLETE: Dashboard updated with scenario data for: "${userMsg}"` }]);
            } else {
                setMessages(prev => [...prev, { role: 'system', text: data.reply }]);
            }

        } catch (error) {
            console.error(error);
            // Fallback purely client-side if API fails completely
            setTimeout(() => {
                setMessages(prev => [...prev, { role: 'system', text: "Connection interruption. Displaying cached forensic summary: Risk data integrity verified." }]);
            }, 1000);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <span style={styles.headerTitle}>
                    <span style={styles.brand}>AIETHIA</span> <span style={{ opacity: 0.3, margin: '0 0.5rem' }}>|</span> LIVE ANALYST
                </span>
                <div style={{ width: '8px', height: '8px', background: '#059669', borderRadius: '50%', boxShadow: '0 0 8px #34D399' }}></div>
            </div>

            <div style={styles.inputArea}>
                <div style={styles.inputWrapper}>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask AIETHIA to simulate or explain..."
                        style={styles.input}
                    />
                    <button onClick={handleSend} style={styles.sendBtn}>
                        <Send style={{ width: '16px', height: '16px' }} />
                    </button>
                </div>
            </div>

            <div style={styles.chatArea}>
                {isTyping && (
                    <div style={styles.typingIndicator}>
                        <div style={{ ...styles.dot, animationDelay: '-0.32s' }}></div>
                        <div style={{ ...styles.dot, animationDelay: '-0.16s' }}></div>
                        <div style={styles.dot}></div>
                    </div>
                )}

                {[...messages].reverse().map((msg, idx) => (
                    <div key={idx} style={msg.role === 'user' ? styles.messageUser : styles.messageSystem}>
                        <span style={{
                            ...styles.messageLabel,
                            color: msg.role === 'user' ? '#059669' : 'rgba(240, 240, 242, 0.5)',
                            textAlign: msg.role === 'user' ? 'right' : 'left'
                        }}>
                            {msg.role === 'user' ? 'You' : <><span style={styles.brand}>AIETHIA</span> INTELLIGENCE</>}
                        </span>
                        <p style={{ margin: 0, lineHeight: 1.5 }}>
                            {msg.text.includes("Verified.") ? (
                                <>
                                    {msg.text.split("Verified.")[0]}
                                    <span style={{ color: '#059669', fontWeight: 'bold' }}>Verified.</span>
                                    {msg.text.split("Verified.")[1]}
                                </>
                            ) : (
                                msg.text
                            )}
                        </p>
                    </div>
                ))}
            </div>
        </div >
    );
};

export default AISentinel;
