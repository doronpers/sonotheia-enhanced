import { useState } from "react";
import { apiBase } from "../config";

function getDefaultQuestion(verdict) {
  switch (verdict?.toUpperCase()) {
    case "REAL":
    case "CLEAR":
      return "Why did you classify this as real?";
    case "SYNTHETIC":
    case "SUSPECT":
      return "Why did you think this might be synthetic?";
    default:
      return "Can you explain your analysis?";
  }
}

function DetectorChat({ detectionResult }) {
  // detectionResult is the full JSON from /api/v2/detect/quick
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState([]); // {question, answer_markdown, ts}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!detectionResult) return null;

  const defaultQuestion = getDefaultQuestion(detectionResult.verdict);
  const currentQuestion = question || defaultQuestion;

  const handleAsk = async () => {
    const q = currentQuestion.trim();
    if (!q) return;

    setLoading(true);
    setError("");

    try {
      const payload = {
        verdict: detectionResult.verdict,
        detail: detectionResult.detail,
        evidence: detectionResult.evidence,
        question: q,
      };

      const res = await fetch(`${apiBase}/api/v2/explain`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Explain request failed with ${res.status}`);
      }

      const data = await res.json();

      setConversation((prev) => [
        ...prev,
        {
          question: q,
          answer_markdown: data.answer_markdown,
          ts: Date.now(),
        },
      ]);

      // Clear the input after successful submission
      setQuestion("");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to get explanation.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    // Submit on Ctrl+Enter or Cmd+Enter (allows plain Enter for newlines)
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      handleAsk();
    }
  };

  return (
    <section className="detector-chat">
      <div className="section-container">
        <h3 className="section-title">Ask the Detector</h3>
        <p className="section-text">
          You're talking to the same system that produced the verdict — but in a voice tuned
          for explanation, not marketing.
        </p>

        <div className="detector-chat-input">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            className="detector-chat-textarea"
            placeholder={defaultQuestion}
            aria-label="Ask a question about the detection result"
            title="Press Ctrl+Enter or Cmd+Enter to submit"
          />
          <button
            onClick={handleAsk}
            className="cta-button"
            disabled={loading}
          >
            {loading ? "Listening..." : "Ask"}
          </button>
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="detector-chat-log">
          {conversation.map((turn) => (
            <div key={turn.ts} className="detector-chat-turn">
              <div className="detector-chat-question">
                <strong>You:</strong> {turn.question}
              </div>
              <div className="detector-chat-answer">
                <strong><span className="sonotheia-brand">Sonotheia</span>:</strong>
                {/* You can later swap this to a markdown renderer */}
                <pre className="detector-chat-markdown">
                  {turn.answer_markdown}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default DetectorChat;
