import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  LinearProgress,
} from '@mui/material';
import { keyframes } from '@emotion/react';
import { Mic, CloudUpload, Send, Stop, FiberManualRecord } from '@mui/icons-material';
import axios from 'axios';

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
`;

export default function AuthenticationForm({ onAuthenticate }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);
  
  const [formData, setFormData] = useState({
    transaction_id: `TXN-${Date.now()}`,
    customer_id: 'CUST-12345',
    amount_usd: 15000.0,
    channel: 'wire_transfer',
    destination_country: 'US',
    is_new_beneficiary: false,
    voice_sample: null,
    device_info: {
      device_id: 'DEV-001',
      integrity_check: true,
      location_consistent: true,
    },
  });

  const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData((prev) => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Convert file to base64
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result.split(',')[1]; // Remove data:audio/wav;base64, prefix
        setFormData((prev) => ({
          ...prev,
          voice_sample: base64String,
        }));
        setAudioBlob(file);
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        setAudioUrl(URL.createObjectURL(file));
      };
      reader.readAsDataURL(file);
    }
  };

  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });
      
      streamRef.current = stream;
      audioChunksRef.current = [];
      
      // Create MediaRecorder with WAV format if supported, otherwise use default
      const options = { mimeType: 'audio/webm' };
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        options.mimeType = 'audio/webm;codecs=opus';
      }
      
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        
        // Create URL for playback
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        
        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64String = reader.result.split(',')[1];
          setFormData((prev) => ({
            ...prev,
            voice_sample: base64String,
          }));
        };
        reader.readAsDataURL(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
      
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const clearAudio = () => {
    if (isRecording) {
      stopRecording();
    }
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setFormData((prev) => ({
      ...prev,
      voice_sample: null,
    }));
    setRecordingTime(0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${apiBase}/api/authenticate`, {
        transaction_id: formData.transaction_id,
        customer_id: formData.customer_id,
        amount_usd: parseFloat(formData.amount_usd),
        channel: formData.channel,
        destination_country: formData.destination_country,
        is_new_beneficiary: formData.is_new_beneficiary,
        voice_sample: formData.voice_sample,
        device_info: formData.device_info,
      });

      if (onAuthenticate) {
        onAuthenticate(response.data);
      }
    } catch (err) {
      console.error('Authentication failed:', err);
      setError(
        err.response?.data?.detail?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Authentication request failed'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Submit Authentication Request
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Enter transaction details and upload a voice sample for multi-factor authentication
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Transaction ID"
              value={formData.transaction_id}
              onChange={(e) => handleInputChange('transaction_id', e.target.value)}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Customer ID"
              value={formData.customer_id}
              onChange={(e) => handleInputChange('customer_id', e.target.value)}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Amount (USD)"
              type="number"
              value={formData.amount_usd}
              onChange={(e) => handleInputChange('amount_usd', e.target.value)}
              required
              inputProps={{ min: 0, step: 0.01 }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Channel</InputLabel>
              <Select
                value={formData.channel}
                label="Channel"
                onChange={(e) => handleInputChange('channel', e.target.value)}
              >
                <MenuItem value="wire_transfer">Wire Transfer</MenuItem>
                <MenuItem value="ach">ACH</MenuItem>
                <MenuItem value="mobile">Mobile</MenuItem>
                <MenuItem value="web">Web</MenuItem>
                <MenuItem value="branch">Branch</MenuItem>
                <MenuItem value="atm">ATM</MenuItem>
                <MenuItem value="phone">Phone</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Destination Country"
              value={formData.destination_country}
              onChange={(e) => handleInputChange('destination_country', e.target.value)}
              placeholder="US"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_new_beneficiary}
                  onChange={(e) => handleInputChange('is_new_beneficiary', e.target.checked)}
                />
              }
              label="New Beneficiary"
            />
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Voice Sample (Optional)
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                Record audio directly in your browser or upload an audio file
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
                {!isRecording ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<Mic />}
                    onClick={startRecording}
                    disabled={loading}
                  >
                    Start Recording
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<Stop />}
                    onClick={stopRecording}
                  >
                    Stop Recording
                  </Button>
                )}
                
                <input
                  accept="audio/*"
                  style={{ display: 'none' }}
                  id="voice-upload"
                  type="file"
                  onChange={handleFileUpload}
                  disabled={isRecording || loading}
                />
                <label htmlFor="voice-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<CloudUpload />}
                    disabled={isRecording || loading}
                  >
                    Upload Audio File
                  </Button>
                </label>
                
                {formData.voice_sample && !isRecording && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={clearAudio}
                    disabled={loading}
                  >
                    Clear
                  </Button>
                )}
              </Box>
              
              {isRecording && (
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <FiberManualRecord
                      sx={{
                        color: 'error.main',
                        animation: `${pulse} 1s ease-in-out infinite`,
                      }}
                    />
                    <Typography variant="body2" color="error.main" fontWeight="bold">
                      Recording... {formatTime(recordingTime)}
                    </Typography>
                  </Box>
                  <LinearProgress />
                </Box>
              )}
              
              {audioUrl && !isRecording && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 1 }}>
                    ✓ Audio ready
                  </Typography>
                  <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '400px' }} />
                </Box>
              )}
            </Box>
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Device Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Device ID"
                    value={formData.device_info.device_id}
                    onChange={(e) => handleInputChange('device_info.device_id', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.device_info.integrity_check}
                        onChange={(e) =>
                          handleInputChange('device_info.integrity_check', e.target.checked)
                        }
                      />
                    }
                    label="Integrity Check"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.device_info.location_consistent}
                        onChange={(e) =>
                          handleInputChange('device_info.location_consistent', e.target.checked)
                        }
                      />
                    }
                    label="Location Consistent"
                  />
                </Grid>
              </Grid>
            </Box>
          </Grid>
          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <Send />}
              disabled={loading}
              fullWidth
            >
              {loading ? 'Authenticating...' : 'Submit Authentication Request'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
}

