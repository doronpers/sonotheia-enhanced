import React from "react";
import { Card, CardContent, Typography, Collapse, Button } from "@mui/material";

export default function FactorCard({ name, score, state, explanation, highlight }) {
  const [expanded, setExpanded] = React.useState(false);
  
  const stateColors = {
    pass: "#4CAF50",
    warn: "#FFC107",
    fail: "#F44336"
  };
  
  const stateIcons = {
    pass: "🟢",
    warn: "🟡",
    fail: "🔴"
  };
  
  return (
    <Card 
      sx={{
        border: `2px solid ${stateColors[state]}`,
        backgroundColor: highlight ? "#E3F2FD" : "#FFFFFF",
        margin: 1,
        minWidth: 200,
        transition: "all 0.3s ease"
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {name}
        </Typography>
        <Typography variant="body1">
          Score: <strong>{score}</strong>
        </Typography>
        <Typography variant="body1" sx={{ color: stateColors[state] }}>
          {stateIcons[state]} {state.toUpperCase()}
        </Typography>
        <Button 
          size="small" 
          onClick={() => setExpanded(!expanded)}
          sx={{ mt: 1 }}
        >
          {expanded ? "Hide" : "Show Why"}
        </Button>
        <Collapse in={expanded}>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {explanation}
          </Typography>
        </Collapse>
      </CardContent>
    </Card>
  );
}
