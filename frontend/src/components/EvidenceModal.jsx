import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Tabs,
  Tab,
  Box,
  Typography
} from "@mui/material";

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export default function EvidenceModal({ open, onClose, segment, evidence }) {
  const [tabValue, setTabValue] = React.useState(0);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Evidence: {segment?.label} Segment ({segment?.start}-{segment?.end}s)
      </DialogTitle>
      <DialogContent>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Fusion Analysis" />
          <Tab label="Waveform" />
          <Tab label="Spectrogram" />
          <Tab label="Sensor Breakdown" />
          <Tab label="SAR Narrative" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {evidence?.fusion_verdict ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Global Risk Assessment
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Risk Score: {(evidence.fusion_verdict.global_risk_score * 100).toFixed(1)}%
                </Typography>
                <Box sx={{
                  width: '100%',
                  height: 24,
                  bgcolor: 'grey.200',
                  borderRadius: 1,
                  overflow: 'hidden',
                  mt: 1
                }}>
                  <Box sx={{
                    width: `${evidence.fusion_verdict.global_risk_score * 100}%`,
                    height: '100%',
                    bgcolor: evidence.fusion_verdict.verdict === 'SYNTHETIC' ? 'error.main' :
                      evidence.fusion_verdict.verdict === 'REAL' ? 'success.main' : 'warning.main',
                    transition: 'width 0.5s ease'
                  }} />
                </Box>
                <Typography variant="h5" sx={{ mt: 2 }}>
                  Verdict: <strong>{evidence.fusion_verdict.verdict}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Confidence: {(evidence.fusion_verdict.confidence * 100).toFixed(1)}%
                </Typography>
              </Box>

              <Typography variant="h6" gutterBottom>
                Top Contributing Sensors
              </Typography>
              {evidence.fusion_verdict.contributing_factors?.slice(0, 3).map((factor, idx) => (
                <Box key={idx} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="subtitle2">
                    {idx + 1}. {factor.sensor_name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Weight: {(factor.weight * 100).toFixed(0)}% | Contribution: {(factor.contribution * 100).toFixed(1)}%
                  </Typography>
                  {factor.reason && (
                    <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                      Finding: {factor.reason}
                    </Typography>
                  )}
                  {factor.detail && (
                    <Typography variant="caption" color="text.secondary">
                      {factor.detail}
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>
          ) : (
            <Typography>No fusion analysis available</Typography>
          )}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <img
            src={evidence?.waveformImg || '/placeholder-waveform.png'}
            alt="Waveform"
            style={{ width: "100%" }}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <img
            src={evidence?.spectrogramImg || '/placeholder-spectrogram.png'}
            alt="Spectrogram"
            style={{ width: "100%" }}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Session Metadata</Typography>
              <Typography variant="body2"><strong>Device:</strong> {evidence?.device || "N/A"}</Typography>
              <Typography variant="body2"><strong>Location:</strong> {evidence?.location || "N/A"}</Typography>
              <Typography variant="body2"><strong>Session ID:</strong> {evidence?.sessionId || "N/A"}</Typography>
            </Paper>

            <Typography variant="h6" sx={{ mt: 1 }}>Sensor Results</Typography>
            {Object.entries(evidence || {})
              .filter(([key]) => !['device', 'location', 'sessionId', 'fusion_verdict', 'waveformImg', 'spectrogramImg', 'sarNarrative'].includes(key))
              .map(([key, data]) => (
                <Paper key={key} sx={{ p: 2, borderLeft: 6, borderColor: data.passed ? 'success.main' : 'error.main' }}>
                  <Typography variant="subtitle1" sx={{ textTransform: 'capitalize', fontWeight: 'bold' }}>
                    {key.replace(/_/g, ' ')}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Status: <strong style={{ color: data.passed ? 'green' : 'red' }}>{data.passed ? 'PASSED' : 'FAILED'}</strong>
                  </Typography>
                  {data.value !== undefined && (
                    <Typography variant="body2">Score: {data.value}</Typography>
                  )}
                  {data.detail && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                      {data.detail}
                    </Typography>
                  )}
                </Paper>
              ))
            }
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>
            {evidence?.sarNarrative || "No SAR narrative generated"}
          </Typography>
        </TabPanel>
      </DialogContent>
    </Dialog>
  );
}
