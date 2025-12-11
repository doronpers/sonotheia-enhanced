import React from "react";
import { Box, Typography, Paper } from "@mui/material";

export default function RiskScoreBox({ score, level, factors }) {
  const levelColors = {
    LOW: "#4CAF50",
    MEDIUM: "#FFC107",
    HIGH: "#FF9800",
    CRITICAL: "#F44336"
  };

  const color = levelColors[level] || "#9E9E9E";

  return (
    <Paper 
      elevation={3}
      sx={{ 
        p: 3, 
        backgroundColor: color + "20",
        border: `2px solid ${color}`,
        borderRadius: 2
      }}
    >
      <Typography variant="h5" gutterBottom>
        Risk Assessment
      </Typography>
      
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            backgroundColor: color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          <Typography variant="h4" color="white" fontWeight="bold">
            {Math.round(score * 100)}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="h6" color={color} fontWeight="bold">
            {level}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Risk Level
          </Typography>
        </Box>
      </Box>

      {factors && factors.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Risk Factors:
          </Typography>
          {factors.map((factor, idx) => (
            <Typography key={idx} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
              • {factor}
            </Typography>
          ))}
        </Box>
      )}
    </Paper>
  );
}
