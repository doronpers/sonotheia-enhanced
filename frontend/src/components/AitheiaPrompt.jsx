import React, { useState } from 'react';
import { apiBase } from '../config';

/**
 * AitheiaPrompt - Embeddable AITHEIA interaction point for sections
 *
 * This component provides a prominent way to ask AITHEIA questions
 * within specific sections of the website.
 */

const AitheiaPrompt = ({
    section = 'home',
    title = 'Ask AITHEIA',
    subtitle = 'Get instant answers about our technology',
    suggestions = [],
    variant = 'default', // 'default', 'compact', 'hero'
    onResponse = null // Optional callback when response received
}) => {
    const [inputValue, setInputValue] = useState('');
    const [response, setResponse] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showInput, setShowInput] = useState(variant === 'hero');

    const API_URL = apiBase || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://sonotheia-backend.onrender.com');

    const handleAsk = async (question) => {
        const message = question || inputValue.trim();
        if (!message) return;

        setIsLoading(true);
        setResponse(null);

        try {
            const res = await fetch(`${API_URL}/api/aitheia/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    section,
                    provider: 'auto'
                })
            });

            if (!res.ok) throw new Error('Request failed');

            const data = await res.json();
            setResponse(data.reply);

            if (onResponse) {
                onResponse(data);
            }
        } catch (error) {
            console.error('AITHEIA error:', error);
            setResponse("I'm having trouble connecting. Please try the chat button in the bottom right corner.");
        } finally {
            setIsLoading(false);
            setInputValue('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAsk();
        }
    };

    // Variant-specific styles
    const getContainerClass = () => {
        const base = 'aitheia-prompt';
        return `${base} aitheia-prompt--${variant}`;
    };

    return (
        <>
            <style>{`
                .aitheia-prompt {
                    background: linear-gradient(135deg, rgba(5, 150, 105, 0.08) 0%, rgba(5, 5, 8, 0.95) 100%);
                    border: 1px solid rgba(5, 150, 105, 0.2);
                    border-radius: 16px;
                    padding: 24px;
                    margin: 24px 0;
                }

                .aitheia-prompt--hero {
                    background: linear-gradient(135deg, rgba(5, 150, 105, 0.12) 0%, rgba(5, 5, 8, 0.98) 100%);
                    border: 1px solid rgba(5, 150, 105, 0.3);
                    padding: 32px;
                    max-width: 600px;
                    margin: 32px auto;
                }

                .aitheia-prompt--compact {
                    padding: 16px;
                    border-radius: 12px;
                }

                .aitheia-prompt__header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .aitheia-prompt__status {
                    width: 10px;
                    height: 10px;
                    background: #059669;
                    border-radius: 50%;
                    box-shadow: 0 0 10px rgba(5, 150, 105, 0.6);
                    animation: aitheiaGlow 2s ease-in-out infinite;
                }

                @keyframes aitheiaGlow {
                    0%, 100% { box-shadow: 0 0 10px rgba(5, 150, 105, 0.4); }
                    50% { box-shadow: 0 0 20px rgba(5, 150, 105, 0.8); }
                }

                .aitheia-prompt__brand {
                    font-family: 'Inter', sans-serif;
                    font-weight: 700;
                    font-size: 14px;
                    letter-spacing: 0.2em;
                    text-transform: uppercase;
                    color: #059669;
                }

                .aitheia-prompt__title {
                    color: #F0F0F2;
                    font-size: 18px;
                    font-weight: 600;
                    margin: 0 0 4px 0;
                }

                .aitheia-prompt__subtitle {
                    color: rgba(240, 240, 242, 0.5);
                    font-size: 13px;
                    margin: 0;
                }

                .aitheia-prompt__suggestions {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 16px;
                }

                .aitheia-prompt__suggestion {
                    font-size: 12px;
                    padding: 8px 14px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(5, 150, 105, 0.2);
                    border-radius: 20px;
                    color: rgba(240, 240, 242, 0.8);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-family: inherit;
                }

                .aitheia-prompt__suggestion:hover {
                    background: rgba(5, 150, 105, 0.15);
                    border-color: rgba(5, 150, 105, 0.4);
                    color: #F0F0F2;
                    transform: translateY(-1px);
                }

                .aitheia-prompt__suggestion:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none;
                }

                .aitheia-prompt__input-area {
                    margin-top: 16px;
                    display: flex;
                    gap: 10px;
                }

                .aitheia-prompt__input {
                    flex: 1;
                    background: rgba(5, 5, 8, 0.8);
                    border: 1px solid rgba(5, 150, 105, 0.2);
                    border-radius: 8px;
                    color: #F0F0F2;
                    padding: 12px 16px;
                    font-size: 14px;
                    font-family: inherit;
                    outline: none;
                    transition: border-color 0.2s;
                }

                .aitheia-prompt__input:focus {
                    border-color: rgba(5, 150, 105, 0.5);
                }

                .aitheia-prompt__input::placeholder {
                    color: rgba(240, 240, 242, 0.3);
                }

                .aitheia-prompt__send {
                    padding: 12px 20px;
                    background: #059669;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }

                .aitheia-prompt__send:hover {
                    background: #047857;
                }

                .aitheia-prompt__send:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .aitheia-prompt__response {
                    margin-top: 20px;
                    padding: 16px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    border-left: 3px solid #059669;
                }

                .aitheia-prompt__response-label {
                    font-size: 10px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: #059669;
                    margin-bottom: 8px;
                    display: block;
                }

                .aitheia-prompt__response-text {
                    color: rgba(240, 240, 242, 0.9);
                    font-size: 14px;
                    line-height: 1.6;
                    margin: 0;
                }

                .aitheia-prompt__loading {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    color: rgba(240, 240, 242, 0.5);
                    font-size: 13px;
                    margin-top: 16px;
                }

                .aitheia-prompt__loading-dots {
                    display: flex;
                    gap: 4px;
                }

                .aitheia-prompt__loading-dot {
                    width: 6px;
                    height: 6px;
                    background: #059669;
                    border-radius: 50%;
                    animation: dotPulse 1.4s infinite ease-in-out both;
                }

                .aitheia-prompt__loading-dot:nth-child(1) { animation-delay: -0.32s; }
                .aitheia-prompt__loading-dot:nth-child(2) { animation-delay: -0.16s; }

                @keyframes dotPulse {
                    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }

                .aitheia-prompt__toggle {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: none;
                    border: 1px solid rgba(5, 150, 105, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: #059669;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                    margin-top: 12px;
                }

                .aitheia-prompt__toggle:hover {
                    background: rgba(5, 150, 105, 0.1);
                    border-color: rgba(5, 150, 105, 0.5);
                }
            `}</style>

            <div className={getContainerClass()}>
                <div className="aitheia-prompt__header">
                    <div className="aitheia-prompt__status" />
                    <div>
                        <span className="aitheia-prompt__brand">AITHEIA</span>
                        {variant !== 'compact' && (
                            <>
                                <h3 className="aitheia-prompt__title">{title}</h3>
                                <p className="aitheia-prompt__subtitle">{subtitle}</p>
                            </>
                        )}
                    </div>
                </div>

                {/* Suggestions */}
                {suggestions.length > 0 && (
                    <div className="aitheia-prompt__suggestions">
                        {suggestions.map((suggestion, idx) => (
                            <button
                                key={idx}
                                className="aitheia-prompt__suggestion"
                                onClick={() => handleAsk(suggestion)}
                                disabled={isLoading}
                            >
                                {suggestion}
                            </button>
                        ))}
                    </div>
                )}

                {/* Input Area */}
                {(showInput || variant === 'hero') && (
                    <div className="aitheia-prompt__input-area">
                        <input
                            type="text"
                            className="aitheia-prompt__input"
                            placeholder="Ask me anything about Sonotheia..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                        />
                        <button
                            className="aitheia-prompt__send"
                            onClick={() => handleAsk()}
                            disabled={!inputValue.trim() || isLoading}
                        >
                            Ask
                        </button>
                    </div>
                )}

                {/* Toggle for compact/default when not hero */}
                {!showInput && variant !== 'hero' && (
                    <button
                        className="aitheia-prompt__toggle"
                        onClick={() => setShowInput(true)}
                    >
                        <span>+</span> Ask your own question
                    </button>
                )}

                {/* Loading */}
                {isLoading && (
                    <div className="aitheia-prompt__loading">
                        <div className="aitheia-prompt__loading-dots">
                            <div className="aitheia-prompt__loading-dot" />
                            <div className="aitheia-prompt__loading-dot" />
                            <div className="aitheia-prompt__loading-dot" />
                        </div>
                        <span>AITHEIA is thinking...</span>
                    </div>
                )}

                {/* Response */}
                {response && !isLoading && (
                    <div className="aitheia-prompt__response">
                        <span className="aitheia-prompt__response-label">AITHEIA</span>
                        <p className="aitheia-prompt__response-text">{response}</p>
                    </div>
                )}
            </div>
        </>
    );
};

export default AitheiaPrompt;
