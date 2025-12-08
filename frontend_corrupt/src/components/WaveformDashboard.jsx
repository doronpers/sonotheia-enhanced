import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { Box, Button, Grid } from "@mui/material";
import FactorCard from "./FactorCard";

export default function WaveformDashboard({
  waveformData,
  segments,
  factorResults
}) {
  const [currentTime, setCurrentTime] = useState(0);
  const [playingSegment, setPlayingSegment] = useState(null);

  const playSegment = (start, end) => {
    // In production, this would control audio playback
    setPlayingSegment({ start, end });
    console.log(`Playing segment from ${start} to ${end}`);
  };

  // Build Plotly shapes for segment overlays
  // Parse evidence.segments from API response if available
  const segmentShapes = segments?.map(seg => {
    // API response format: { start, end, is_synthetic, risk_score, ... }
    const isSynthetic = seg.is_synthetic ?? (seg.type !== "genuine");
    const riskScore = seg.risk_score ?? (isSynthetic ? 0.8 : 0.2);

    return {
      type: "rect",
      xref: "x",
      yref: "paper",
      x0: seg.start,
      x1: seg.end,
      y0: 0,
      y1: 1,
      fillcolor: isSynthetic
        ? `rgba(220, 50, 50, ${0.15 + riskScore * 0.2})`  // Red zones for synthetic
        : "rgba(60, 180, 100, 0.15)",  // Green for genuine
      line: { width: isSynthetic ? 2 : 0, color: isSynthetic ? "rgba(220, 50, 50, 0.8)" : undefined },
      layer: "below"
    };
  }) || [];

  // Add cursor line
  const cursorShape = {
    type: "line",
    x0: currentTime,
    x1: currentTime,
    y0: 0,
    y1: 1,
    yref: "paper",
    line: { color: "#1E88E5", width: 2 }
  };

  const allShapes = [...segmentShapes, cursorShape];

  return (
    <Box>
      <Plot
        data={[
          {
            x: waveformData.x,
            y: waveformData.y,
            type: "scatter",
            mode: "lines",
            line: { color: "black", width: 1 },
            name: "Waveform"
          }
        ]}
        layout={{
          shapes: allShapes,
          height: 300,
          margin: { l: 40, r: 10, t: 10, b: 40 },
          xaxis: { title: "Time (seconds)" },
          yaxis: { title: "Amplitude", showticklabels: false },
          hovermode: "x"
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%" }}
        onClick={({ points }) => {
          const time = points[0].x;
          const seg = segments?.find(s => time >= s.start && time <= s.end);
          if (seg) playSegment(seg.start, seg.end);
        }}
      />

      <Box sx={{ display: "flex", gap: 1, mb: 2, mt: 2 }}>
        {segments?.map((seg, idx) => (
          <Button
            key={idx}
            variant="outlined"
            size="small"
            onClick={() => playSegment(seg.start, seg.end)}
          >
            Play {seg.label}
          </Button>
        ))}
      </Box>

      <Grid container spacing={2}>
        {factorResults?.map((factor, idx) => {
          // Find corresponding segment for this factor if available
          const correspondingSegment = segments?.[idx];
          const isHighlighted = playingSegment &&
            correspondingSegment &&
            playingSegment.start === correspondingSegment.start;

          return (
            <Grid item xs={12} sm={6} md={4} key={idx}>
              <FactorCard
                {...factor}
                highlight={isHighlighted}
              />
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
