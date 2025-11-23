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
          <Tab label="Waveform" />
          <Tab label="Spectrogram" />
          <Tab label="Metadata" />
          <Tab label="SAR Narrative" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <img 
            src={evidence?.waveformImg || '/placeholder-waveform.png'} 
            alt="Waveform" 
            style={{ width: "100%" }}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <img 
            src={evidence?.spectrogramImg || '/placeholder-spectrogram.png'} 
            alt="Spectrogram" 
            style={{ width: "100%" }}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="body2">
            <strong>Device:</strong> {evidence?.device || "N/A"}
          </Typography>
          <Typography variant="body2">
            <strong>Location:</strong> {evidence?.location || "N/A"}
          </Typography>
          <Typography variant="body2">
            <strong>Session ID:</strong> {evidence?.sessionId || "N/A"}
          </Typography>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>
            {evidence?.sarNarrative || "No SAR narrative generated"}
          </Typography>
        </TabPanel>
      </DialogContent>
    </Dialog>
  );
}
