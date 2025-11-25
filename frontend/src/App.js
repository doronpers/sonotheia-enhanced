import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Container, Typography, Box, CircularProgress, Button, AppBar, Toolbar, Tabs, Tab } from "@mui/material";
import WaveformDashboard from "./components/WaveformDashboard";
import EvidenceModal from "./components/EvidenceModal";
import RiskScoreBox from "./components/RiskScoreBox";
import Dashboard from "./components/Dashboard";
import AuthenticationForm from "./components/AuthenticationForm";

function HomePage() {
  const [loading, setLoading] = useState(false);
  const [waveformData, setWaveformData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [authResult, setAuthResult] = useState(null);
  const [factorResults, setFactorResults] = useState([]);

  useEffect(() => {
    // Fetch demo data from backend
    loadDemoData();
  }, []);

  const loadDemoData = async () => {
    setLoading(true);
    try {
      const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/demo/waveform/sample1`);
      const data = await response.json();
      setWaveformData(data);
    } catch (err) {
      console.error("Failed to load demo data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthenticate = (result) => {
    setAuthResult(result);
    
    // Convert API response to factor results format
    const factors = [];
    
    if (result.factor_results?.voice) {
      const voice = result.factor_results.voice;
      factors.push({
        name: "Physics Deepfake",
        score: voice.deepfake_score || 0,
        state: voice.deepfake_score < 0.3 ? "pass" : "fail",
        explanation: voice.explanation || `Deepfake score: ${voice.deepfake_score || 0}`
      });
      
      if (voice.speaker_verification_score !== undefined) {
        factors.push({
          name: "Speaker Verification",
          score: voice.speaker_verification_score,
          state: voice.speaker_verification_score >= 0.85 ? "pass" : "fail",
          explanation: voice.explanation || `Speaker verification score: ${voice.speaker_verification_score}`
        });
      }
      
      if (voice.liveness_passed !== undefined) {
        factors.push({
          name: "Liveness",
          score: voice.liveness_confidence || (voice.liveness_passed ? 1.0 : 0.0),
          state: voice.liveness_passed ? "pass" : "fail",
          explanation: voice.explanation || (voice.liveness_passed ? "Active liveness challenge passed" : "Liveness check failed")
        });
      }
    }
    
    if (result.factor_results?.device) {
      const device = result.factor_results.device;
      factors.push({
        name: "Device Trust",
        score: device.trust_score || 0,
        state: device.device_trusted ? "pass" : "fail",
        explanation: device.explanation || `Device trust score: ${device.trust_score || 0}`
      });
    }
    
    setFactorResults(factors);
    
    // Update waveform data if available from demo endpoint
    loadDemoData();
  };

  if (loading) {
    return (
      <Container sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom>
          Sonotheia Enhanced Authentication
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Multi-Factor Voice Authentication & SAR Reporting System
        </Typography>
      </Box>

      <AuthenticationForm onAuthenticate={handleAuthenticate} />

      {authResult && (
        <Box sx={{ mb: 4 }}>
          <RiskScoreBox 
            score={authResult.risk_score || 0} 
            level={authResult.risk_level || "LOW"} 
            factors={authResult.transaction_risk?.risk_factors || [
              `Transaction amount: $${authResult.amount_usd || 0}`,
              `Decision: ${authResult.decision || "PENDING"}`
            ]}
          />
        </Box>
      )}

      {waveformData && (
        <WaveformDashboard
          waveformData={waveformData}
          segments={waveformData.segments}
          factorResults={factorResults.length > 0 ? factorResults : [
            {
              name: "Physics Deepfake",
              score: 0.15,
              state: "pass",
              explanation: "No synthetic artifacts detected in audio sample"
            },
            {
              name: "Speaker Verification",
              score: 0.96,
              state: "pass",
              explanation: "Voice matches enrolled voiceprint"
            },
            {
              name: "Liveness",
              score: 1.0,
              state: "pass",
              explanation: "Active liveness challenge passed"
            },
            {
              name: "Device Trust",
              score: 0.85,
              state: "pass",
              explanation: "Known device with good reputation"
            }
          ]}
        />
      )}

      <EvidenceModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        segment={selectedEvidence?.segment}
        evidence={selectedEvidence?.evidence}
      />
    </Container>
  );
}

function NavTabs() {
  const location = useLocation();
  const currentPath = location.pathname;
  const tabValue = currentPath === '/dashboard' ? 1 : 0;

  return (
    <Tabs value={tabValue} textColor="inherit" indicatorColor="secondary">
      <Tab label="Authentication" component={Link} to="/" />
      <Tab label="Dashboard" component={Link} to="/dashboard" />
    </Tabs>
  );
}

function App() {
  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Sonotheia Enhanced Platform
            </Typography>
            <NavTabs />
          </Toolbar>
        </AppBar>

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </Box>
    </Router>
  );
}

export default App;
