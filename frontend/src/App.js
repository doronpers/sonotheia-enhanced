import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, CircularProgress, Button } from "@mui/material";
import WaveformDashboard from "./components/WaveformDashboard";
import EvidenceModal from "./components/EvidenceModal";
import RiskScoreBox from "./components/RiskScoreBox";

function App() {
  const [loading, setLoading] = useState(false);
  const [waveformData, setWaveformData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  useEffect(() => {
    // Fetch demo data from backend
    loadDemoData();
  }, []);

  const loadDemoData = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/demo/waveform/sample1");
      const data = await response.json();
      setWaveformData(data);
    } catch (err) {
      console.error("Failed to load demo data:", err);
    } finally {
      setLoading(false);
    }
  };

  const factorResults = [
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
  ];

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

      {waveformData && (
        <Box sx={{ mb: 4 }}>
          <RiskScoreBox 
            score={0.25} 
            level="LOW" 
            factors={[
              "Medium value transaction: $15,000",
              "Known device with good reputation"
            ]}
          />
        </Box>
      )}

      {waveformData && (
        <WaveformDashboard
          waveformData={waveformData}
          segments={waveformData.segments}
          factorResults={factorResults}
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

export default App;
