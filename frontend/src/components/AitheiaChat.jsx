import React, { useState, useEffect, useRef, useCallback } from 'react';
import { apiBase } from '../config';

// Icons
const ChatIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" width="24" height="24">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
);

const CloseIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

const SendIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
);

const MinimizeIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

// Section detection based on scroll position
const SECTION_IDS = ['home', 'team', 'platform', 'demo', 'enterprise', 'contact'];

const AitheiaChat = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [currentSection, setCurrentSection] = useState('home');
    const [suggestions, setSuggestions] = useState([]);
    const [hasNewMessage, setHasNewMessage] = useState(false);

    const chatAreaRef = useRef(null);
    const inputRef = useRef(null);

    const API_URL = apiBase || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://sonotheia-backend.onrender.com');

    // Detect current section based on scroll
    useEffect(() => {
        const handleScroll = () => {
            const scrollPosition = window.scrollY + window.innerHeight / 3;

            for (const sectionId of SECTION_IDS) {
                const element = document.getElementById(sectionId);
                if (element) {
                    const { offsetTop, offsetHeight } = element;
                    if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
                        if (currentSection !== sectionId) {
                            setCurrentSection(sectionId);
                        }
                        break;
                    }
                }
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Initial check

        return () => window.removeEventListener('scroll', handleScroll);
    }, [currentSection]);

    // Fetch suggestions when section changes
    useEffect(() => {
        const fetchSuggestions = async () => {
            try {
                const response = await fetch(`${API_URL}/api/aitheia/suggestions?section=${currentSection}`);
                if (response.ok) {
                    const data = await response.json();
                    setSuggestions(data.suggestions || []);
                }
            } catch (error) {
                console.error('Failed to fetch suggestions:', error);
                // Fallback suggestions
                setSuggestions([
                    "What is Sonotheia?",
                    "How does the detection work?",
                    "Tell me about the founders"
                ]);
            }
        };

        fetchSuggestions();
    }, [currentSection, API_URL]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (chatAreaRef.current) {
            chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
        }
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen && !isMinimized && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen, isMinimized]);

    // Initial greeting when first opened
    useEffect(() => {
        if (isOpen && messages.length === 0) {
            setMessages([{
                role: 'assistant',
                content: `Hello! I'm AITHEIA, your guide to Sonotheia's voice fraud detection technology. True Voice. Verified. How can I help you today?`
            }]);
        }
    }, [isOpen, messages.length]);

    const handleSend = useCallback(async (messageText = null) => {
        const message = messageText || inputValue.trim();
        if (!message) return;

        // Add user message
        const userMessage = { role: 'user', content: message };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsTyping(true);

        try {
            const response = await fetch(`${API_URL}/api/aitheia/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    section: currentSection,
                    conversation_history: messages.slice(-10), // Send last 10 messages for context
                    provider: 'auto'
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.reply,
                source: data.source
            }]);

            // If chat is minimized, show notification
            if (isMinimized) {
                setHasNewMessage(true);
            }

        } catch (error) {
            console.error('AITHEIA chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "I'm having trouble connecting right now. Please try again in a moment.",
                source: 'error'
            }]);
        } finally {
            setIsTyping(false);
        }
    }, [inputValue, messages, currentSection, API_URL, isMinimized]);

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        handleSend(suggestion);
    };

    const toggleChat = () => {
        setIsOpen(!isOpen);
        setIsMinimized(false);
        setHasNewMessage(false);
    };

    const toggleMinimize = () => {
        setIsMinimized(!isMinimized);
        if (isMinimized) {
            setHasNewMessage(false);
        }
    };

    // Section label for header
    const sectionLabels = {
        home: 'Home',
        team: 'Team',
        platform: 'Technology',
        demo: 'Demo',
        enterprise: 'Enterprise',
        contact: 'Contact'
    };

    return (
        <>
            <style>{`
                .aitheia-container {
                    position: fixed;
                    bottom: 24px;
                    right: 24px;
                    z-index: 9999;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                }

                .aitheia-fab {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #059669 0%, #047857 100%);
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    box-shadow: 0 4px 20px rgba(5, 150, 105, 0.4);
                    transition: all 0.3s ease;
                    position: relative;
                }

                .aitheia-fab:hover {
                    transform: scale(1.05);
                    box-shadow: 0 6px 25px rgba(5, 150, 105, 0.5);
                }

                .aitheia-fab-badge {
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    width: 18px;
                    height: 18px;
                    background: #E5B956;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 10px;
                    font-weight: bold;
                    color: #0a0a0f;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }

                .aitheia-panel {
                    position: absolute;
                    bottom: 70px;
                    right: 0;
                    width: 380px;
                    max-height: 550px;
                    background: #0a0a0f;
                    border-radius: 16px;
                    border: 1px solid rgba(5, 150, 105, 0.3);
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    animation: slideUp 0.3s ease;
                }

                .aitheia-panel.minimized {
                    max-height: 56px;
                }

                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .aitheia-header {
                    padding: 14px 16px;
                    background: linear-gradient(135deg, rgba(5, 150, 105, 0.15) 0%, rgba(5, 5, 8, 0.95) 100%);
                    border-bottom: 1px solid rgba(5, 150, 105, 0.2);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }

                .aitheia-header-left {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .aitheia-status-dot {
                    width: 8px;
                    height: 8px;
                    background: #059669;
                    border-radius: 50%;
                    box-shadow: 0 0 8px rgba(5, 150, 105, 0.6);
                }

                .aitheia-title {
                    font-weight: 700;
                    color: #F0F0F2;
                    font-size: 14px;
                    letter-spacing: 0.05em;
                }

                .aitheia-brand {
                    font-family: 'Inter', sans-serif;
                    letter-spacing: 0.2em;
                    text-transform: uppercase;
                    color: #059669;
                }

                .aitheia-section-badge {
                    font-size: 10px;
                    color: rgba(240, 240, 242, 0.5);
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }

                .aitheia-header-actions {
                    display: flex;
                    gap: 8px;
                }

                .aitheia-header-btn {
                    background: none;
                    border: none;
                    color: rgba(240, 240, 242, 0.5);
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: all 0.2s;
                }

                .aitheia-header-btn:hover {
                    color: #F0F0F2;
                    background: rgba(255, 255, 255, 0.05);
                }

                .aitheia-chat-area {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    min-height: 250px;
                    max-height: 350px;
                }

                .aitheia-message {
                    max-width: 85%;
                    padding: 12px 14px;
                    border-radius: 12px;
                    font-size: 13px;
                    line-height: 1.5;
                }

                .aitheia-message.user {
                    align-self: flex-end;
                    background: rgba(5, 150, 105, 0.15);
                    border: 1px solid rgba(5, 150, 105, 0.3);
                    color: #F0F0F2;
                    border-bottom-right-radius: 4px;
                }

                .aitheia-message.assistant {
                    align-self: flex-start;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    color: rgba(240, 240, 242, 0.9);
                    border-bottom-left-radius: 4px;
                }

                .aitheia-message-label {
                    font-size: 9px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    margin-bottom: 6px;
                    display: block;
                    color: rgba(240, 240, 242, 0.4);
                }

                .aitheia-message.user .aitheia-message-label {
                    text-align: right;
                    color: #059669;
                }

                .aitheia-typing {
                    display: flex;
                    gap: 4px;
                    padding: 12px 14px;
                    align-self: flex-start;
                }

                .aitheia-typing-dot {
                    width: 6px;
                    height: 6px;
                    background: rgba(5, 150, 105, 0.5);
                    border-radius: 50%;
                    animation: typingBounce 1.4s infinite ease-in-out both;
                }

                .aitheia-typing-dot:nth-child(1) { animation-delay: -0.32s; }
                .aitheia-typing-dot:nth-child(2) { animation-delay: -0.16s; }

                @keyframes typingBounce {
                    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }

                .aitheia-suggestions {
                    padding: 8px 16px 12px;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                    border-top: 1px solid rgba(255, 255, 255, 0.05);
                }

                .aitheia-suggestion {
                    font-size: 11px;
                    padding: 6px 10px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 16px;
                    color: rgba(240, 240, 242, 0.7);
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .aitheia-suggestion:hover {
                    background: rgba(5, 150, 105, 0.1);
                    border-color: rgba(5, 150, 105, 0.3);
                    color: #F0F0F2;
                }

                .aitheia-input-area {
                    padding: 12px 16px;
                    border-top: 1px solid rgba(255, 255, 255, 0.08);
                    background: rgba(255, 255, 255, 0.02);
                }

                .aitheia-input-wrapper {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .aitheia-input {
                    flex: 1;
                    background: rgba(5, 5, 8, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: #F0F0F2;
                    padding: 10px 14px;
                    font-size: 13px;
                    font-family: inherit;
                    outline: none;
                    transition: border-color 0.2s;
                }

                .aitheia-input:focus {
                    border-color: rgba(5, 150, 105, 0.5);
                }

                .aitheia-input::placeholder {
                    color: rgba(240, 240, 242, 0.3);
                }

                .aitheia-send-btn {
                    width: 38px;
                    height: 38px;
                    border-radius: 8px;
                    background: #059669;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    transition: all 0.2s;
                }

                .aitheia-send-btn:hover {
                    background: #047857;
                }

                .aitheia-send-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                @media (max-width: 480px) {
                    .aitheia-container {
                        bottom: 16px;
                        right: 16px;
                    }

                    .aitheia-panel {
                        width: calc(100vw - 32px);
                        right: 0;
                        bottom: 70px;
                    }
                }
            `}</style>

            <div className="aitheia-container">
                {/* Chat Panel */}
                {isOpen && (
                    <div className={`aitheia-panel ${isMinimized ? 'minimized' : ''}`}>
                        {/* Header */}
                        <div className="aitheia-header">
                            <div className="aitheia-header-left">
                                <div className="aitheia-status-dot" />
                                <div>
                                    <div className="aitheia-title">
                                        <span className="aitheia-brand">AITHEIA</span>
                                    </div>
                                    <div className="aitheia-section-badge">
                                        {sectionLabels[currentSection] || 'Home'}
                                    </div>
                                </div>
                            </div>
                            <div className="aitheia-header-actions">
                                <button className="aitheia-header-btn" onClick={toggleMinimize} title={isMinimized ? "Expand" : "Minimize"}>
                                    <MinimizeIcon />
                                </button>
                                <button className="aitheia-header-btn" onClick={toggleChat} title="Close">
                                    <CloseIcon />
                                </button>
                            </div>
                        </div>

                        {/* Chat Content (hidden when minimized) */}
                        {!isMinimized && (
                            <>
                                {/* Messages */}
                                <div className="aitheia-chat-area" ref={chatAreaRef}>
                                    {messages.map((msg, idx) => (
                                        <div key={idx} className={`aitheia-message ${msg.role}`}>
                                            <span className="aitheia-message-label">
                                                {msg.role === 'user' ? 'You' : 'AITHEIA'}
                                            </span>
                                            {msg.content}
                                        </div>
                                    ))}
                                    {isTyping && (
                                        <div className="aitheia-typing">
                                            <div className="aitheia-typing-dot" />
                                            <div className="aitheia-typing-dot" />
                                            <div className="aitheia-typing-dot" />
                                        </div>
                                    )}
                                </div>

                                {/* Suggestions */}
                                {messages.length <= 2 && suggestions.length > 0 && (
                                    <div className="aitheia-suggestions">
                                        {suggestions.slice(0, 3).map((suggestion, idx) => (
                                            <button
                                                key={idx}
                                                className="aitheia-suggestion"
                                                onClick={() => handleSuggestionClick(suggestion)}
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Input */}
                                <div className="aitheia-input-area">
                                    <div className="aitheia-input-wrapper">
                                        <input
                                            ref={inputRef}
                                            type="text"
                                            className="aitheia-input"
                                            placeholder="Ask AITHEIA anything..."
                                            value={inputValue}
                                            onChange={(e) => setInputValue(e.target.value)}
                                            onKeyPress={handleKeyPress}
                                            disabled={isTyping}
                                        />
                                        <button
                                            className="aitheia-send-btn"
                                            onClick={() => handleSend()}
                                            disabled={!inputValue.trim() || isTyping}
                                        >
                                            <SendIcon />
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* FAB Button */}
                <button className="aitheia-fab" onClick={toggleChat} aria-label="Chat with AITHEIA">
                    {isOpen ? <CloseIcon /> : <ChatIcon />}
                    {hasNewMessage && !isOpen && <span className="aitheia-fab-badge">1</span>}
                </button>
            </div>
        </>
    );
};

export default AitheiaChat;
