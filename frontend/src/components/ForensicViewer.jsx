import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Button, Paper, Grid } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import RestartAltIcon from '@mui/icons-material/RestartAlt';

const ForensicViewer = ({ audioUrl, metadataUrl }) => {
    const canvasRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [metadata, setMetadata] = useState(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [error, setError] = useState(null);

    // Audio Refs
    const audioCtxRef = useRef(null);
    const sourceRef = useRef(null);
    const analyserRef = useRef(null);
    const bufferRef = useRef(null);
    const startTimeRef = useRef(0);
    const reqIdRef = useRef(null);

    // Constants
    const BACKEND_URL = "http://localhost:8000"; // Assuming dev environment

    useEffect(() => {
        const loadData = async () => {
            try {
                // Initialize Audio Context
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                audioCtxRef.current = new AudioContext();

                // Fetch Audio
                const finalAudioUrl = audioUrl || `${BACKEND_URL}/api/static/forensics/artifact_sample.wav`;
                const audioRes = await fetch(finalAudioUrl);
                const arrayBuffer = await audioRes.arrayBuffer();
                bufferRef.current = await audioCtxRef.current.decodeAudioData(arrayBuffer);

                // Fetch Metadata
                const finalMetaUrl = metadataUrl || `${BACKEND_URL}/api/static/forensics/artifact_metadata.json`;
                const metaRes = await fetch(finalMetaUrl);
                const metaJson = await metaRes.json();
                setMetadata(metaJson);

                console.log("Forensic Data Loaded", metaJson);
            } catch (err) {
                console.error("Load Error:", err);
                setError("Failed to load forensic data. Ensure backend is running.");
            }
        };

        loadData();

        return () => {
            if (sourceRef.current) sourceRef.current.stop();
            if (audioCtxRef.current) audioCtxRef.current.close();
            if (reqIdRef.current) cancelAnimationFrame(reqIdRef.current);
        };
    }, [audioUrl, metadataUrl]);

    // Spectrogram Loop
    useEffect(() => {
        if (!metadata || !bufferRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, width, height);

        // Draw Annotations (Static)
        // In a real implementation, we would draw these on a separate layer or re-draw every frame.
        // For simplicity, we draw them on top in the paint loop.

    }, [metadata]);

    const startPlayback = () => {
        if (isPlaying) {
            stopPlayback();
            return;
        }

        if (!audioCtxRef.current || !bufferRef.current) return;

        // Create Nodes
        sourceRef.current = audioCtxRef.current.createBufferSource();
        sourceRef.current.buffer = bufferRef.current;
        analyserRef.current = audioCtxRef.current.createAnalyser();
        analyserRef.current.fftSize = 2048;

        // Connect
        sourceRef.current.connect(analyserRef.current);
        analyserRef.current.connect(audioCtxRef.current.destination);

        // Start
        sourceRef.current.start(0);
        startTimeRef.current = audioCtxRef.current.currentTime;
        setIsPlaying(true);

        // Animation Loop
        paintLoop();

        // Auto-stop
        sourceRef.current.onended = () => stopPlayback();
    };

    const stopPlayback = () => {
        if (sourceRef.current) {
            try {
                sourceRef.current.stop();
            } catch (e) { } // ignore if already stopped
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        setIsPlaying(false);
        if (reqIdRef.current) cancelAnimationFrame(reqIdRef.current);
    };

    const paintLoop = () => {
        if (!analyserRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate progress
        const elapsed = audioCtxRef.current.currentTime - startTimeRef.current;
        setCurrentTime(elapsed);
        const progress = elapsed / bufferRef.current.duration;
        const x = Math.floor(progress * width);

        // Draw Column
        // This simple version draws a single column at current X
        // A full spectrogram keeps history. To keep history without clearing, 
        // we just don't clear the canvas in the loop!

        if (x < width) {
            for (let i = 0; i < bufferLength; i++) {
                const val = dataArray[i];
                if (val === 0) continue;

                // Map frequency bin to Y
                const y = height - Math.floor((i / bufferLength) * height);

                // Heatmap Color
                let color = `rgba(0,0,0,0)`;
                const v = val / 255;
                if (v > 0.1) color = `rgba(0, 0, ${val}, ${v})`;
                if (v > 0.5) color = `rgba(${val}, ${val}, 0, ${v})`;
                if (v > 0.8) color = `rgba(255, 0, 0, ${v})`;

                ctx.fillStyle = color;
                ctx.fillRect(x, y, 2, 2);
            }
        }

        // Draw Annotations Overlay
        // We really should use a separate canvas or div overlay for performance,
        // but let's just use the metadata to highlight.
        // (Skipping complex redrawing for this MVP component)

        reqIdRef.current = requestAnimationFrame(paintLoop);
    };

    // Render Annotations as HTML overlays
    const renderAnnotations = () => {
        if (!metadata || !canvasRef.current) return null;
        const width = canvasRef.current.width; // 800 assumed
        const duration = metadata.duration;
        const nyquist = metadata.sampleRate / 2;

        return metadata.artifacts.map((art, idx) => {
            const left = (art.startTime / duration) * 100 + "%";
            const w = ((art.endTime - art.startTime) / duration) * 100 + "%";
            const bottom = (art.freqMin / nyquist) * 100 + "%";
            const h = ((art.freqMax - art.freqMin) / nyquist) * 100 + "%";

            return (
                <Box
                    key={idx}
                    sx={{
                        position: 'absolute',
                        left: left,
                        width: w,
                        bottom: bottom,
                        height: h,
                        border: `2px solid ${art.color || 'red'}`,
                        backgroundColor: 'rgba(255,0,0,0.1)',
                        zIndex: 10
                    }}
                >
                    <Typography sx={{
                        color: 'white',
                        bgcolor: art.color,
                        fontSize: '10px',
                        px: 0.5,
                        position: 'absolute',
                        top: -20,
                        whiteSpace: 'nowrap'
                    }}>
                        {art.name}
                    </Typography>
                </Box>
            );
        });
    };

    return (
        <Paper sx={{ p: 2, bgcolor: '#1e293b', color: 'white' }}>
            <Box display="flex" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Forensic Analyzer</Typography>
                <Box>
                    <Button
                        variant="contained"
                        color={isPlaying ? "error" : "primary"}
                        startIcon={isPlaying ? <StopIcon /> : <PlayArrowIcon />}
                        onClick={startPlayback}
                    >
                        {isPlaying ? "Stop" : "Analyze"}
                    </Button>
                </Box>
            </Box>

            {error && <Typography color="error">{error}</Typography>}

            <Box sx={{ position: 'relative', height: 400, bgcolor: 'black', border: '1px solid #334155' }}>
                <canvas
                    ref={canvasRef}
                    width={800}
                    height={400}
                    style={{ width: '100%', height: '100%' }}
                />

                {/* Overlay Layer */}
                <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}>
                    {renderAnnotations()}
                </Box>

                {/* Playhead */}
                {metadata && (
                    <Box
                        sx={{
                            position: 'absolute',
                            left: `${(currentTime / metadata.duration) * 100}%`,
                            top: 0,
                            bottom: 0,
                            width: 2,
                            bgcolor: 'white',
                            zIndex: 20
                        }}
                    />
                )}
            </Box>

            <Grid container spacing={2} sx={{ mt: 2 }}>
                {metadata && metadata.artifacts.map((art, idx) => (
                    <Grid item xs={12} md={4} key={idx}>
                        <Paper sx={{ p: 1, bgcolor: '#334155' }}>
                            <Typography variant="subtitle2" color={art.color}>{art.name}</Typography>
                            <Typography variant="body2" sx={{ color: '#94a3b8' }}>{art.description}</Typography>
                        </Paper>
                    </Grid>
                ))}
            </Grid>
        </Paper>
    );
};

export default ForensicViewer;
