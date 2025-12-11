/**
 * Risk Slider Widget
 * 
 * Interactive risk score slider with real-time updates and visual feedback
 */

import React, { useState, useEffect } from 'react';
import { Box, Slider, Typography, Chip, Card, CardContent } from '@mui/material';
import { Warning, CheckCircle, Error } from '@mui/icons-material';

export interface RiskSliderProps {
  value: number; // Risk score 0-1
  onChange?: (value: number) => void;
  onChangeCommitted?: (value: number) => void;
  readOnly?: boolean;
  showFactors?: boolean;
  factors?: Array<{
    name: string;
    contribution: number;
    description?: string;
  }>;
}

const getRiskLevel = (score: number): string => {
  if (score < 0.3) return 'LOW';
  if (score < 0.5) return 'MEDIUM';
  if (score < 0.7) return 'HIGH';
  return 'CRITICAL';
};

const getRiskColor = (score: number): string => {
  if (score < 0.3) return '#4caf50'; // Green
  if (score < 0.5) return '#ff9800'; // Orange
  if (score < 0.7) return '#ff5722'; // Deep Orange
  return '#f44336'; // Red
};

const getRiskIcon = (score: number) => {
  if (score < 0.3) return <CheckCircle sx={{ color: '#4caf50' }} />;
  if (score < 0.7) return <Warning sx={{ color: '#ff9800' }} />;
  return <Error sx={{ color: '#f44336' }} />;
};

export const RiskSlider = ({
  value,
  onChange,
  onChangeCommitted,
  readOnly = false,
  showFactors = false,
  factors = []
}) => {
  const [displayValue, setDisplayValue] = useState(value);
  const riskLevel = getRiskLevel(displayValue);
  const riskColor = getRiskColor(displayValue);
  const riskIcon = getRiskIcon(displayValue);

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  const handleChange = (_event, newValue) => {
    const val = Array.isArray(newValue) ? newValue[0] : newValue;
    setDisplayValue(val);
    if (onChange) {
      onChange(val);
    }
  };

  const handleChangeCommitted = (_event, newValue) => {
    const val = Array.isArray(newValue) ? newValue[0] : newValue;
    if (onChangeCommitted) {
      onChangeCommitted(val);
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {riskIcon}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Risk Score
          </Typography>
          <Chip
            label={riskLevel}
            sx={{
              backgroundColor: riskColor,
              color: 'white',
              fontWeight: 'bold'
            }}
          />
        </Box>

        <Box sx={{ px: 2 }}>
          <Slider
            value={displayValue}
            onChange={handleChange}
            onChangeCommitted={handleChangeCommitted}
            min={0}
            max={1}
            step={0.01}
            disabled={readOnly}
            marks={[
              { value: 0, label: '0' },
              { value: 0.3, label: '0.3' },
              { value: 0.5, label: '0.5' },
              { value: 0.7, label: '0.7' },
              { value: 1, label: '1.0' }
            ]}
            sx={{
              color: riskColor,
              '& .MuiSlider-thumb': {
                backgroundColor: riskColor,
              },
              '& .MuiSlider-track': {
                backgroundColor: riskColor,
              },
              '& .MuiSlider-rail': {
                opacity: 0.3,
              }
            }}
          />
        </Box>

        <Typography
          variant="h4"
          align="center"
          sx={{ mt: 2, color: riskColor, fontWeight: 'bold' }}
        >
          {(displayValue * 100).toFixed(1)}%
        </Typography>

        {showFactors && factors.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Risk Factors:
            </Typography>
            {factors.map((factor, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mb: 1,
                  p: 1,
                  borderRadius: 1,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)'
                }}
              >
                <Typography variant="body2" sx={{ flexGrow: 1 }}>
                  {factor.name}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 'bold',
                    color: getRiskColor(factor.contribution)
                  }}
                >
                  +{(factor.contribution * 100).toFixed(1)}%
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {!readOnly && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 2, textAlign: 'center' }}
          >
            Drag the slider to simulate risk score changes
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default RiskSlider;
