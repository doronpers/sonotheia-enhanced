import { useMemo } from "react";

/**
 * ModelResultsVisualizer - Visualize HF ensemble model results
 * 
 * Features:
 * - Display individual model scores
 * - Show weighted ensemble calculation
 * - Visual confidence bars
 * - Model latency information
 */

const ModelResultsVisualizer = ({ modelResults }) => {
  // Parse model results from evidence
  const { models, aggregateScore, modelsUsed, modelsFailed } = useMemo(() => {
    if (!modelResults?.model_results) {
      return { models: [], aggregateScore: 0, modelsUsed: 0, modelsFailed: 0 };
    }

    const models = modelResults.model_results || [];
    const aggregateScore = modelResults.value || 0;
    
    // Calculate counts in a single pass when metadata values are missing
    let modelsUsed = modelResults.models_used;
    let modelsFailed = modelResults.models_failed;
    
    if (modelsUsed === undefined || modelsFailed === undefined) {
      let successCount = 0;
      let failCount = 0;
      for (const m of models) {
        if (m.status === "ready") {
          successCount++;
        } else {
          failCount++;
        }
      }
      modelsUsed = modelsUsed ?? successCount;
      modelsFailed = modelsFailed ?? failCount;
    }

    return { models, aggregateScore, modelsUsed, modelsFailed };
  }, [modelResults]);

  if (!models.length) {
    return null;
  }

  const getScoreColor = (score) => {
    if (score <= 0.3) return "var(--verification-green)";
    if (score <= 0.5) return "var(--signal-gold)";
    return "var(--alert-red)";
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "ready":
        return "✓";
      case "rate_limited":
        return "⏳";
      case "error":
        return "✗";
      default:
        return "?";
    }
  };

  return (
    <div className="model-results-visualizer">
      <div className="visualizer-header">
        <h4>AI Model Ensemble Results</h4>
        <div className="model-stats">
          <span className="stat success">{modelsUsed} active</span>
          {modelsFailed > 0 && (
            <span className="stat failed">{modelsFailed} failed</span>
          )}
        </div>
      </div>

      {/* Aggregate Score Display */}
      <div className="aggregate-section">
        <div className="aggregate-label">Ensemble Score</div>
        <div className="aggregate-bar-container">
          <div
            className="aggregate-bar"
            style={{
              width: `${Math.min(aggregateScore * 100, 100)}%`,
              backgroundColor: getScoreColor(aggregateScore),
            }}
          />
          <span className="aggregate-threshold" style={{ left: "50%" }}>
            Threshold
          </span>
        </div>
        <div className="aggregate-value">
          <span style={{ color: getScoreColor(aggregateScore) }}>
            {(aggregateScore * 100).toFixed(1)}%
          </span>
          <span className="aggregate-verdict">
            {aggregateScore > 0.5 ? "⚠ Synthetic" : "✓ Likely Real"}
          </span>
        </div>
      </div>

      {/* Individual Model Results */}
      <div className="models-breakdown">
        <div className="breakdown-header">Individual Model Scores</div>
        {models.map((model, index) => (
          <div key={model.model_id || index} className="model-row">
            <div className="model-name">
              <span className={`status-icon ${model.status}`}>
                {getStatusIcon(model.status)}
              </span>
              <span className="name">{model.model_id?.split("/").pop() || "Unknown"}</span>
              {model.latency_ms && (
                <span className="latency">{Math.round(model.latency_ms)}ms</span>
              )}
            </div>
            <div className="model-score-bar-container">
              {model.status === "ready" ? (
                <>
                  <div
                    className="model-score-bar"
                    style={{
                      width: `${Math.min(model.fake_score * 100, 100)}%`,
                      backgroundColor: getScoreColor(model.fake_score),
                    }}
                  />
                  <span className="score-value">
                    {(model.fake_score * 100).toFixed(1)}%
                  </span>
                </>
              ) : (
                <span className="error-message">
                  {model.status === "rate_limited" ? "Rate limited" : model.error || "Error"}
                </span>
              )}
            </div>
            <div className="model-meta">
              <span className="label">{model.label}</span>
              <span className="confidence">
                {model.confidence ? `${(model.confidence * 100).toFixed(0)}% conf.` : ""}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="visualizer-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: "var(--verification-green)" }} />
          <span>Low risk (0-30%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: "var(--signal-gold)" }} />
          <span>Medium risk (30-50%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: "var(--alert-red)" }} />
          <span>High risk (50%+)</span>
        </div>
      </div>

      <style>{`
        .model-results-visualizer {
          background: var(--surface-elevated);
          border: 1px solid var(--surface-border);
          border-radius: 8px;
          padding: 1rem;
          margin: 1rem 0;
        }

        .visualizer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .visualizer-header h4 {
          margin: 0;
          color: var(--signal-gold);
          font-size: 0.9rem;
        }

        .model-stats {
          display: flex;
          gap: 0.5rem;
        }

        .stat {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 500;
        }

        .stat.success {
          background: var(--verification-green-alpha-15);
          color: var(--verification-green);
        }

        .stat.failed {
          background: var(--alert-red-alpha-15);
          color: var(--alert-red);
        }

        .aggregate-section {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 6px;
          padding: 0.75rem;
          margin-bottom: 1rem;
        }

        .aggregate-label {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .aggregate-bar-container {
          position: relative;
          height: 24px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
          overflow: hidden;
        }

        .aggregate-bar {
          height: 100%;
          transition: width 0.3s ease;
        }

        .aggregate-threshold {
          position: absolute;
          top: 0;
          height: 100%;
          width: 2px;
          background: rgba(255, 255, 255, 0.5);
          font-size: 0;
        }

        .aggregate-threshold::after {
          content: "50%";
          position: absolute;
          top: -16px;
          left: -12px;
          font-size: 0.6rem;
          color: var(--text-secondary);
        }

        .aggregate-value {
          display: flex;
          justify-content: space-between;
          margin-top: 0.5rem;
          font-size: 0.85rem;
        }

        .aggregate-verdict {
          font-weight: 600;
        }

        .models-breakdown {
          margin-bottom: 1rem;
        }

        .breakdown-header {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .model-row {
          display: grid;
          grid-template-columns: 1fr 2fr 1fr;
          gap: 0.5rem;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 1px solid var(--surface-border);
        }

        .model-row:last-child {
          border-bottom: none;
        }

        .model-name {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.8rem;
        }

        .status-icon {
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          font-size: 0.65rem;
        }

        .status-icon.ready {
          background: var(--verification-green-alpha-15);
          color: var(--verification-green);
        }

        .status-icon.rate_limited {
          background: var(--signal-gold-alpha-15);
          color: var(--signal-gold);
        }

        .status-icon.error {
          background: var(--alert-red-alpha-15);
          color: var(--alert-red);
        }

        .model-name .name {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 100px;
        }

        .model-name .latency {
          font-size: 0.65rem;
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .model-score-bar-container {
          position: relative;
          height: 16px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
          overflow: hidden;
        }

        .model-score-bar {
          height: 100%;
          transition: width 0.3s ease;
        }

        .score-value {
          position: absolute;
          right: 4px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 0.65rem;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.9);
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }

        .error-message {
          font-size: 0.7rem;
          color: var(--alert-red);
          padding-left: 4px;
        }

        .model-meta {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          font-size: 0.7rem;
        }

        .model-meta .label {
          color: var(--text-secondary);
          text-transform: capitalize;
        }

        .model-meta .confidence {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .visualizer-legend {
          display: flex;
          justify-content: center;
          gap: 1rem;
          font-size: 0.7rem;
          color: var(--text-secondary);
          padding-top: 0.5rem;
          border-top: 1px solid var(--surface-border);
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};

export default ModelResultsVisualizer;
