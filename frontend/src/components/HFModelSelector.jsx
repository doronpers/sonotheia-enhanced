import { useState, useEffect } from "react";
import { apiBase } from "../config";

/**
 * HFModelSelector - Component for selecting and managing Hugging Face models
 * 
 * Features:
 * - Display list of available models
 * - Add/remove models from ensemble
 * - Show model status (ready, rate limited, error)
 * - Trigger model warm-up
 */

const HFModelSelector = ({ onModelChange }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newModelId, setNewModelId] = useState("");
  const [newModelWeight, setNewModelWeight] = useState(1.0);
  const [isAddingModel, setIsAddingModel] = useState(false);
  const [apiAvailable, setApiAvailable] = useState(false);
  const [localFallbackAvailable, setLocalFallbackAvailable] = useState(false);

  // Fetch models on mount
  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/api/admin/hf/models`);
      if (!response.ok) {
        throw new Error("Failed to fetch models");
      }
      const data = await response.json();
      setModels(data.models || []);
      setApiAvailable(data.api_available || false);
      setLocalFallbackAvailable(data.local_fallback_available || false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddModel = async (e) => {
    e.preventDefault();
    if (!newModelId.trim()) return;

    setIsAddingModel(true);
    try {
      const response = await fetch(
        `${apiBase}/api/admin/hf/models?model_id=${encodeURIComponent(newModelId)}&weight=${newModelWeight}`,
        { method: "POST" }
      );
      if (!response.ok) {
        throw new Error("Failed to add model");
      }
      setNewModelId("");
      setNewModelWeight(1.0);
      await fetchModels();
      onModelChange?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAddingModel(false);
    }
  };

  const handleRemoveModel = async (modelId) => {
    if (!window.confirm(`Remove model ${modelId}?`)) return;

    try {
      const response = await fetch(
        `${apiBase}/api/admin/hf/models/${encodeURIComponent(modelId)}`,
        { method: "DELETE" }
      );
      if (!response.ok) {
        throw new Error("Failed to remove model");
      }
      await fetchModels();
      onModelChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleWarmup = async () => {
    try {
      const response = await fetch(`${apiBase}/api/admin/hf/warmup`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Failed to warm up models");
      }
      await fetchModels();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusBadge = (status) => {
    const statusStyles = {
      ready: { backgroundColor: "var(--verification-green)", color: "#fff" },
      warming_up: { backgroundColor: "var(--signal-gold)", color: "#000" },
      rate_limited: { backgroundColor: "var(--alert-red)", color: "#fff" },
      error: { backgroundColor: "var(--alert-red)", color: "#fff" },
      unavailable: { backgroundColor: "var(--medium-gray)", color: "#fff" },
    };

    // Use explicit fallback with warning for unknown statuses
    const style = statusStyles[status];
    if (!style && status) {
      console.warn(`Unknown HF model status: ${status}`);
    }

    return (
      <span
        className="hf-status-badge"
        style={{
          ...(style || statusStyles.unavailable),
          padding: "2px 8px",
          borderRadius: "4px",
          fontSize: "0.75rem",
          fontWeight: "500",
          textTransform: "uppercase",
        }}
      >
        {(status || "unknown").replace("_", " ")}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="hf-model-selector loading">
        <div className="spinner" aria-label="Loading models" />
        <p>Loading models...</p>
      </div>
    );
  }

  return (
    <div className="hf-model-selector">
      <div className="hf-header">
        <h3>Local Engine Health</h3>
        <div className="hf-status-indicators">
          {/* Engine Status Badge */}
          <div className="engine-badge">
            <span className="dot"></span>
            <span>ONLINE</span>
          </div>
        </div>
      </div>

      {/* System Metrics Panel */}
      <div className="system-metrics">
        <div className="metric-row">
          <span className="metric-label">CPU LOAD</span>
          <div className="metric-bar-container">
            <div className="metric-bar" style={{ width: `${models.cpuUsage || 0}%` }}></div>
          </div>
          <span className="metric-value">{models.cpuUsage || 0}%</span>
        </div>
        <div className="metric-row">
          <span className="metric-label">RAM USAGE</span>
          <div className="metric-bar-container">
            <div className="metric-bar" style={{ width: `${models.memoryUsage || 0}%` }}></div>
          </div>
          <span className="metric-value">{models.memoryUsage || 0}%</span>
        </div>
        <div className="metric-row">
          <span className="metric-label">OPTIMIZATION</span>
          <span className={`optimization-badge ${models.quantizationActive ? 'active' : ''}`}>
            {models.quantizationActive ? 'QUANTIZED (INT8)' : 'STANDARD (FP32)'}
          </span>
        </div>
      </div>

      <div className="hf-model-list">
        {/* Simplified model list - purely informational now */}
        {models.models && models.models.length > 0 ? (
          models.models.map((model) => (
            <div key={model.model_id} className="hf-model-item">
              <span className="model-id">{model.model_id.split("/").pop()}</span>
              <span className="model-weight">Active</span>
            </div>
          ))
        ) : (
          <p className="no-models">Physics Engine Only (No ML Models)</p>
        )}
      </div>

      <div className="hf-actions">
        <button className="refresh-btn" onClick={fetchModels}>
          🔄 Refresh Telemetry
        </button>
      </div>

      <style>{`
        .hf-model-selector {
          background: var(--surface-elevated);
          border: 1px solid var(--surface-border);
          border-radius: 8px;
          padding: 1rem;
          margin: 1rem 0;
        }

        .hf-header h3 {
          margin: 0;
          color: var(--emerald-400); /* Sonotheia Green */
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .engine-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.7rem;
            color: var(--emerald-400);
            background: rgba(16, 185, 129, 0.1);
            padding: 2px 8px;
            border-radius: 999px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .engine-badge .dot {
            width: 6px;
            height: 6px;
            background: var(--emerald-400);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--emerald-400);
        }

        .system-metrics {
            margin: 1rem 0;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .metric-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            font-family: monospace;
            font-size: 0.75rem;
        }

        .metric-label {
            width: 80px;
            color: var(--text-secondary);
        }

        .metric-bar-container {
            flex: 1;
            height: 4px;
            background: var(--surface-muted);
            border-radius: 2px;
            overflow: hidden;
        }

        .metric-bar {
            height: 100%;
            background: var(--emerald-500);
            transition: width 0.3s ease;
        }

        .metric-value {
            width: 40px;
            text-align: right;
            color: var(--text-primary);
        }

        .optimization-badge {
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--surface-muted);
            color: var(--text-secondary);
        }

        .optimization-badge.active {
            background: rgba(16, 185, 129, 0.1);
            color: var(--emerald-400);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .hf-model-item {
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--surface-border);
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
        }
        
        .hf-actions button {
             width: 100%;
             padding: 0.5rem;
             margin-top: 0.5rem;
             background: var(--surface-muted);
             border: 1px solid var(--surface-border);
             color: var(--text-secondary);
             border-radius: 4px;
             cursor: pointer;
             font-size: 0.8rem;
        }
        
        .hf-actions button:hover {
            background: var(--surface-elevated);
            color: var(--text-primary);
        }
      `}</style>
    </div>
  );
};

export default HFModelSelector;
