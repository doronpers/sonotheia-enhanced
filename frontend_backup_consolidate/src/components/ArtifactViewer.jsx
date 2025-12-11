import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Paper, Grid, Chip } from '@mui/material';

/**
 * ArtifactViewer - Interactive spectrogram viewer with artifact/anomaly highlighting
 * Displays audio artifacts detected in voice authentication analysis
 */
const ArtifactViewer = ({ audioData, artifacts, sampleRate = 44100, duration = 5.0 }) => {
    const canvasRef = useRef(null);
    const overlayRef = useRef(null);
    const [hoveredArtifact, setHoveredArtifact] = useState(null);

    useEffect(() => {
        if (!canvasRef.current || !audioData) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        // Draw spectrogram background (simplified visualization)
        drawSpectrogram(ctx, canvas.width, canvas.height, audioData);
        
        // Draw artifact overlays
        renderArtifactOverlays();
    }, [audioData, artifacts]);

    const drawSpectrogram = (ctx, width, height, data) => {
        // Create gradient background to simulate spectrogram
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(0.5, '#16213e');
        gradient.addColorStop(1, '#0f3460');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);

        // Add grid lines for frequency markers
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (i / 4) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
    };

    const renderArtifactOverlays = () => {
        if (!artifacts || !overlayRef.current) return;

        const overlay = overlayRef.current;
        overlay.innerHTML = '';

        const width = canvasRef.current.width;
        const height = canvasRef.current.height;
        const nyquist = sampleRate / 2;

        artifacts.forEach((artifact, idx) => {
            // Calculate pixel coordinates
            const x_start = (artifact.startTime / duration) * width;
            const x_width = ((artifact.endTime - artifact.startTime) / duration) * width;
            
            // Frequency coordinates (Y-axis inverted in canvas)
            const y_bottom = height - (artifact.freqMin / nyquist) * height;
            const y_top = height - (artifact.freqMax / nyquist) * height;
            const y_height = y_bottom - y_top;

            // Create artifact box
            const box = document.createElement('div');
            box.style.position = 'absolute';
            box.style.left = `${x_start}px`;
            box.style.width = `${Math.max(2, x_width)}px`;
            box.style.top = `${y_top}px`;
            box.style.height = `${y_height}px`;
            box.style.border = `2px solid ${artifact.color || '#ef4444'}`;
            box.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
            box.style.cursor = 'pointer';
            box.style.transition = 'all 0.2s ease';

            // Add hover effects
            box.onmouseenter = () => {
                box.style.backgroundColor = 'rgba(239, 68, 68, 0.3)';
                setHoveredArtifact(artifact);
            };
            box.onmouseleave = () => {
                box.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
                setHoveredArtifact(null);
            };

            // Create label
            const label = document.createElement('div');
            label.style.backgroundColor = artifact.color || '#ef4444';
            label.style.color = 'white';
            label.style.padding = '2px 6px';
            label.style.fontSize = '10px';
            label.style.fontWeight = 'bold';
            label.style.width = 'fit-content';
            label.style.borderRadius = '2px';
            label.textContent = artifact.id || artifact.name;
            box.appendChild(label);

            overlay.appendChild(box);
        });
    };

    const getFrequencyLabel = (percentage) => {
        const freq = (sampleRate / 2) * (1 - percentage);
        return `${(freq / 1000).toFixed(1)} kHz`;
    };

    return (
        <Box sx={{ width: '100%' }}>
            {/* Main Visualization */}
            <Paper sx={{ p: 2, bgcolor: '#1e293b', color: 'white' }}>
                <Typography variant="h6" gutterBottom>
                    Artifact Detection Visualization
                </Typography>
                
                <Box sx={{ 
                    position: 'relative', 
                    height: 400, 
                    bgcolor: 'black', 
                    border: '1px solid #475569',
                    borderRadius: '4px',
                    overflow: 'hidden'
                }}>
                    {/* Canvas for spectrogram */}
                    <canvas
                        ref={canvasRef}
                        width={800}
                        height={380}
                        style={{ width: '100%', height: '100%', display: 'block' }}
                    />

                    {/* Overlay for artifact boxes */}
                    <div 
                        ref={overlayRef}
                        style={{ 
                            position: 'absolute', 
                            top: 0, 
                            left: 0, 
                            width: '100%', 
                            height: '100%',
                            pointerEvents: 'auto'
                        }}
                    />

                    {/* Frequency axis labels */}
                    {[0, 0.25, 0.5, 0.75, 1].map((pos, idx) => (
                        <Box
                            key={idx}
                            sx={{
                                position: 'absolute',
                                top: `${pos * 100}%`,
                                left: '5px',
                                color: '#94a3b8',
                                fontSize: '0.7rem',
                                bgcolor: 'rgba(0,0,0,0.7)',
                                padding: '2px 4px',
                                pointerEvents: 'none',
                                borderRadius: '2px'
                            }}
                        >
                            {getFrequencyLabel(pos)}
                        </Box>
                    ))}

                    {/* Time axis */}
                    <Box sx={{ 
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: '20px',
                        bgcolor: '#0f172a',
                        borderTop: '1px solid #475569',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        px: 1
                    }}>
                        {[0, 1, 2, 3, 4, 5].map(sec => (
                            <Typography key={sec} sx={{ fontSize: '0.7rem', color: '#666' }}>
                                {sec}s
                            </Typography>
                        ))}
                    </Box>
                </Box>

                {/* Hovered artifact details */}
                {hoveredArtifact && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: '#334155', borderRadius: 1, borderLeft: `4px solid ${hoveredArtifact.color}` }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                            {hoveredArtifact.name}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#94a3b8', mt: 0.5 }}>
                            {hoveredArtifact.description}
                        </Typography>
                        <Typography variant="caption" sx={{ display: 'block', mt: 1, fontFamily: 'monospace', color: '#64748b' }}>
                            Time: {hoveredArtifact.startTime}s - {hoveredArtifact.endTime}s | 
                            Frequency: {hoveredArtifact.freqMin}Hz - {hoveredArtifact.freqMax}Hz
                        </Typography>
                    </Box>
                )}
            </Paper>

            {/* Artifact List */}
            {artifacts && artifacts.length > 0 && (
                <Grid container spacing={2} sx={{ mt: 2 }}>
                    {artifacts.map((artifact, idx) => (
                        <Grid item xs={12} md={6} key={idx}>
                            <Paper 
                                sx={{ 
                                    p: 2, 
                                    bgcolor: '#334155',
                                    borderLeft: `4px solid ${artifact.color}`,
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        bgcolor: '#475569',
                                        transform: 'translateX(4px)'
                                    }
                                }}
                                onMouseEnter={() => setHoveredArtifact(artifact)}
                                onMouseLeave={() => setHoveredArtifact(null)}
                            >
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'white' }}>
                                        {artifact.name}
                                    </Typography>
                                    <Chip 
                                        label={artifact.id} 
                                        size="small" 
                                        sx={{ 
                                            bgcolor: artifact.color, 
                                            color: 'white',
                                            fontWeight: 'bold',
                                            fontSize: '0.7rem'
                                        }} 
                                    />
                                </Box>
                                <Typography variant="body2" sx={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                                    {artifact.description}
                                </Typography>
                                <Typography variant="caption" sx={{ 
                                    display: 'block', 
                                    mt: 1, 
                                    fontFamily: 'monospace',
                                    color: '#64748b'
                                }}>
                                    {artifact.startTime}s - {artifact.endTime}s | {artifact.freqMin}-{artifact.freqMax}Hz
                                </Typography>
                            </Paper>
                        </Grid>
                    ))}
                </Grid>
            )}
        </Box>
    );
};

export default ArtifactViewer;
