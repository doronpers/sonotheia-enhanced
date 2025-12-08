/**
 * Escalation Review Interface
 * 
 * Component for reviewing and making decisions on escalated sessions
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Divider,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Info,
  PriorityHigh,
  Person,
  AccessTime
} from '@mui/icons-material';

export interface EscalationItem {
  escalation_id: string;
  session_id: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_review' | 'approved' | 'declined' | 'needs_info';
  risk_score: number;
  details: {
    [key: string]: any;
  };
  created_at: string;
  assigned_to?: string;
}

export interface EscalationReviewProps {
  escalation: EscalationItem;
  onApprove: (escalationId: string, notes: string) => void;
  onDecline: (escalationId: string, notes: string) => void;
  onRequestInfo: (escalationId: string, notes: string) => void;
  onEscalateFurther: (escalationId: string, notes: string) => void;
  reviewerId: string;
}

const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'critical': return '#f44336';
    case 'high': return '#ff5722';
    case 'medium': return '#ff9800';
    case 'low': return '#4caf50';
    default: return '#757575';
  }
};

const getPriorityIcon = (priority: string) => {
  return <PriorityHigh sx={{ color: getPriorityColor(priority) }} />;
};

export const EscalationReview: React.FC<EscalationReviewProps> = ({
  escalation,
  onApprove,
  onDecline,
  onRequestInfo,
  onEscalateFurther,
  reviewerId
}) => {
  const [decision, setDecision] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!decision || !notes.trim()) {
      alert('Please select a decision and provide notes');
      return;
    }

    setIsSubmitting(true);
    try {
      switch (decision) {
        case 'approve':
          await onApprove(escalation.escalation_id, notes);
          break;
        case 'decline':
          await onDecline(escalation.escalation_id, notes);
          break;
        case 'request_info':
          await onRequestInfo(escalation.escalation_id, notes);
          break;
        case 'escalate_further':
          await onEscalateFurther(escalation.escalation_id, notes);
          break;
      }
      setNotes('');
      setDecision('');
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {getPriorityIcon(escalation.priority)}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Escalation #{escalation.escalation_id}
          </Typography>
          <Chip
            label={escalation.priority.toUpperCase()}
            sx={{
              backgroundColor: getPriorityColor(escalation.priority),
              color: 'white',
              fontWeight: 'bold',
              mr: 1
            }}
          />
          <Chip
            label={escalation.status.toUpperCase()}
            variant="outlined"
          />
        </Box>

        {/* Escalation Info */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Info sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Session ID:
              </Typography>
              <Typography variant="body2" sx={{ ml: 1, fontWeight: 'bold' }}>
                {escalation.session_id}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AccessTime sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Created:
              </Typography>
              <Typography variant="body2" sx={{ ml: 1 }}>
                {new Date(escalation.created_at).toLocaleString()}
              </Typography>
            </Box>
          </Grid>
          {escalation.assigned_to && (
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Person sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  Assigned To:
                </Typography>
                <Typography variant="body2" sx={{ ml: 1 }}>
                  {escalation.assigned_to}
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>

        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Reason for Escalation:
          </Typography>
          <Typography variant="body2">
            {escalation.reason}
          </Typography>
        </Alert>

        {/* Risk Score */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Risk Score:
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                width: '100%',
                height: 8,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                borderRadius: 1,
                overflow: 'hidden'
              }}
            >
              <Box
                sx={{
                  width: `${escalation.risk_score * 100}%`,
                  height: '100%',
                  backgroundColor: escalation.risk_score > 0.7 ? '#f44336' : '#ff9800',
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
            <Typography variant="body2" sx={{ ml: 2, fontWeight: 'bold' }}>
              {(escalation.risk_score * 100).toFixed(1)}%
            </Typography>
          </Box>
        </Box>

        {/* Details */}
        {Object.keys(escalation.details).length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Additional Details:
            </Typography>
            {Object.entries(escalation.details).map(([key, value]) => (
              <Box
                key={key}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  p: 1,
                  borderRadius: 1,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  mb: 0.5
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </Typography>
                <Typography variant="body2">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Review Form */}
        <Typography variant="h6" gutterBottom>
          Review Decision
        </Typography>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Decision</InputLabel>
          <Select
            value={decision}
            onChange={(e) => setDecision(e.target.value)}
            label="Decision"
          >
            <MenuItem value="approve">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle sx={{ mr: 1, color: '#4caf50' }} />
                Approve
              </Box>
            </MenuItem>
            <MenuItem value="decline">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Cancel sx={{ mr: 1, color: '#f44336' }} />
                Decline
              </Box>
            </MenuItem>
            <MenuItem value="request_info">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Info sx={{ mr: 1, color: '#2196f3' }} />
                Request More Information
              </Box>
            </MenuItem>
            <MenuItem value="escalate_further">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <PriorityHigh sx={{ mr: 1, color: '#ff9800' }} />
                Escalate Further
              </Box>
            </MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Review Notes"
          placeholder="Provide detailed reasoning for your decision..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          sx={{ mb: 2 }}
          required
        />

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => {
              setDecision('');
              setNotes('');
            }}
            disabled={isSubmitting}
          >
            Clear
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!decision || !notes.trim() || isSubmitting}
            startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default EscalationReview;
