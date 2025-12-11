/**
 * Evidence Card Widget
 * 
 * Reusable card component for displaying authentication factor evidence
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  Collapse,
  IconButton,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle,
  Cancel,
  Info,
  Warning
} from '@mui/icons-material';

export interface EvidenceCardProps {
  title: string;
  score: number;
  passed: boolean;
  confidence?: number;
  evidence?: {
    [key: string]: any;
  };
  metadata?: {
    [key: string]: any;
  };
  expandable?: boolean;
  onViewDetails?: () => void;
}

const getStatusColor = (passed: boolean, score: number): string => {
  if (!passed) return '#f44336'; // Red
  if (score >= 0.8) return '#4caf50'; // Green
  if (score >= 0.6) return '#ff9800'; // Orange
  return '#ff5722'; // Deep Orange
};

const getStatusIcon = (passed: boolean, score: number) => {
  if (!passed) return <Cancel sx={{ color: '#f44336' }} />;
  if (score >= 0.8) return <CheckCircle sx={{ color: '#4caf50' }} />;
  return <Warning sx={{ color: '#ff9800' }} />;
};

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  title,
  score,
  passed,
  confidence,
  evidence = {},
  metadata = {},
  expandable = true,
  onViewDetails
}) => {
  const [expanded, setExpanded] = useState(false);
  const statusColor = getStatusColor(passed, score);
  const statusIcon = getStatusIcon(passed, score);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Card
      sx={{
        mb: 2,
        border: `2px solid ${statusColor}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 4
        }
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {statusIcon}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            {title}
          </Typography>
          <Chip
            label={passed ? 'PASS' : 'FAIL'}
            sx={{
              backgroundColor: statusColor,
              color: 'white',
              fontWeight: 'bold'
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Score:
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 'bold', color: statusColor }}>
            {(score * 100).toFixed(1)}%
          </Typography>
        </Box>

        {confidence !== undefined && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Confidence:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {(confidence * 100).toFixed(1)}%
            </Typography>
          </Box>
        )}

        {Object.keys(metadata).length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Quick Info:
            </Typography>
            {Object.entries(metadata).slice(0, 2).map(([key, value]) => (
              <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {key}:
                </Typography>
                <Typography variant="caption">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>

      {(expandable || onViewDetails) && (
        <>
          <Divider />
          <CardActions sx={{ justifyContent: 'space-between' }}>
            {onViewDetails && (
              <Button
                size="small"
                startIcon={<Info />}
                onClick={onViewDetails}
              >
                View Full Details
              </Button>
            )}
            {expandable && (
              <IconButton
                onClick={handleExpandClick}
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s'
                }}
                aria-label="show more"
              >
                <ExpandMoreIcon />
              </IconButton>
            )}
          </CardActions>
        </>
      )}

      {expandable && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>
              Evidence Details:
            </Typography>
            
            {Object.keys(evidence).length > 0 && (
              <Box sx={{ mt: 1 }}>
                {Object.entries(evidence).map(([key, value]) => (
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
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {Object.keys(metadata).length > 2 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Additional Metadata:
                </Typography>
                {Object.entries(metadata).slice(2).map(([key, value]) => (
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
                      {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Collapse>
      )}
    </Card>
  );
};

export default EvidenceCard;
