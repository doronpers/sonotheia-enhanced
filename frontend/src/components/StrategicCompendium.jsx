import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    RadialLinearScale,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import { Line, Radar, Bar } from 'react-chartjs-2';
import { useState, useEffect, useRef } from 'react';

// Simple useInView hook to avoid extra dependencies
function useInView(options = {}) {
    const [isInView, setIsInView] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const element = ref.current;
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setIsInView(true);
                observer.disconnect(); // Only need to load once
            }
        }, options);

        if (element) {
            observer.observe(element);
        }

        return () => {
            if (element) observer.unobserve(element);
            observer.disconnect();
        };
    }, []);

    return [ref, isInView];
}

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    RadialLinearScale,
    Title,
    Tooltip,
    Legend,
    Filler
);

// Styles matching the site's design system

const StrategicCompendium = () => {
    // Chart colors matching site design
    const goldColor = '#E5B956';
    const greenColor = '#059669';
    const redColor = '#F43F5E';
    const grayColor = 'rgba(240, 240, 242, 0.5)';

    const [lineRef, lineInView] = useInView({ threshold: 0.1 });
    const [radarRef, radarInView] = useInView({ threshold: 0.1 });
    const [barRef, barInView] = useInView({ threshold: 0.1 });

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: grayColor, font: { family: 'Inter', size: 11 } }
            },
            tooltip: {
                backgroundColor: 'rgba(5, 5, 8, 0.95)',
                titleColor: '#F0F0F2',
                bodyColor: 'rgba(240, 240, 242, 0.8)',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
            }
        },
        scales: {
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.06)' },
                ticks: { color: grayColor, font: { size: 10 } }
            },
            x: {
                grid: { display: false },
                ticks: { color: grayColor, font: { size: 10 } }
            }
        }
    };

    const inflectionData = {
        labels: ['2020', '2021', '2022', '2023', '2024', '2025'],
        datasets: [
            {
                label: 'Cost to Generate Attack',
                data: [100, 80, 50, 20, 5, 0],
                borderColor: redColor,
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2,
            },
            {
                label: 'Cost of Voice Biometrics',
                data: [80, 80, 75, 75, 70, 70],
                borderColor: grayColor,
                borderDash: [5, 5],
                tension: 0.1,
                borderWidth: 2,
            }
        ]
    };

    const radarData = {
        labels: ['Spectral\nFlatness', 'Latency\nJitter', 'Respiration', 'Micro-\nTremors', 'Emotional\nDynamics'],
        datasets: [
            {
                label: 'Synthetic',
                data: [95, 10, 5, 10, 20],
                backgroundColor: 'rgba(244, 63, 94, 0.15)',
                borderColor: redColor,
                pointBackgroundColor: redColor,
                borderWidth: 2,
                pointRadius: 4,
            },
            {
                label: 'Human',
                data: [40, 60, 90, 85, 80],
                backgroundColor: 'rgba(52, 211, 153, 0.15)',
                borderColor: greenColor,
                pointBackgroundColor: greenColor,
                borderWidth: 2,
                pointRadius: 4,
            }
        ]
    };

    const radarOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: grayColor, font: { family: 'Inter', size: 11 } }
            },
        },
        scales: {
            r: {
                angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
                grid: { color: 'rgba(255, 255, 255, 0.06)' },
                pointLabels: { color: 'rgba(240, 240, 242, 0.7)', font: { size: 10 } },
                ticks: { display: false, backdropColor: 'transparent' }
            }
        }
    };

    const complianceData = {
        labels: ['Legacy Auth', 'Voice Bio', 'AIETHIA'],
        datasets: [{
            label: 'Identity Assurance Score',
            data: [20, 50, 95],
            backgroundColor: [grayColor, goldColor, greenColor],
            borderRadius: 6,
            barThickness: 24,
        }]
    };

    const complianceOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.06)' },
                ticks: { color: grayColor },
                max: 100
            },
            y: {
                grid: { display: false },
                ticks: { color: '#F0F0F2', font: { weight: '600', size: 11 } }
            }
        }
    };

    return (
        <div className="compendium-container">
            <div className="compendium-section">
                {/* Section Header */}
                <h2 className="compendium-section-title">Strategic Intelligence</h2>
                <p className="compendium-section-subtitle">
                    Understanding the evolving threat landscape and how our Physics Engine technology provides a decisive advantage.
                </p>

                {/* Row 1: Inflection Point Chart + Analysis */}
                <div className="compendium-grid-2" style={{ marginBottom: '3rem' }}>
                    <div className="compendium-card">
                        <h3 className="compendium-card-title">The Cost Inflection Point</h3>
                        <p className="compendium-card-subtitle">Attack costs approaching zero while defense remains static.</p>
                        <div className="compendium-chart-container" ref={lineRef}>
                            {lineInView && <Line data={inflectionData} options={commonOptions} />}
                        </div>
                    </div>
                    <div className="compendium-card">
                        <h3 className="compendium-card-title">Signal Analysis Engine</h3>
                        <p className="compendium-card-subtitle">Comparing spectral signatures: Deepfakes are "too perfect."</p>
                        <div className="compendium-chart-container" ref={radarRef}>
                            {radarInView && <Radar data={radarData} options={radarOptions} />}
                        </div>
                    </div>
                </div>

                {/* Row 2: Feature Explanations */}
                <div className="compendium-grid-2 desktop-only" style={{ marginBottom: '3rem' }}>
                    <div>
                        <div className="compendium-feature-item">
                            <div className="compendium-feature-title">
                                <span className="compendium-feature-icon">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2C6.48 2 2 6.48 2 12ZM4 12C4 7.58 7.58 4 12 4C16.42 4 20 7.58 20 12C20 16.42 16.42 20 12 20C7.58 20 4 16.42 4 12Z" fill="currentColor" fillOpacity="0.4" />
                                        <path d="M7 12H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                        <path d="M12 7V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
                                    </svg>
                                </span>
                                Spectral Flatness Detection
                            </div>
                            <p className="compendium-feature-text">
                                Generative AI minimizes loss functions, creating 'statistically perfect' audio. Our engine detects this unnatural spectral perfection, flagging signals that lack the chaotic micro-variances of organic speech.
                            </p>
                        </div>
                        <div className="compendium-feature-item">
                            <div className="compendium-feature-title">
                                <span className="compendium-feature-icon">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20ZM12 6C10 6 8.23 7.06 7.21 8.7L8.93 9.7C9.53 8.68 10.68 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16C10.68 16 9.53 15.32 8.93 14.3L7.21 15.3C8.23 16.94 10 18 12 18C15.31 18 18 15.31 18 12C18 8.69 15.31 6 12 6Z" fill="currentColor" />
                                    </svg>
                                </span>
                                Respiration Analysis
                            </div>
                            <p className="compendium-feature-text">
                                Humans must breathe. Deepfakes often forget to inhale or have unnatural pause durations.
                            </p>
                        </div>
                        <div className="compendium-callout-box">
                            <div className="compendium-callout-label">Privacy by Design</div>
                            <p className="compendium-callout-text">
                                "We analyze physics, not biometrics. No Voice Prints. No database. This ensures full GDPR and privacy compliance."
                            </p>
                        </div>
                    </div>
                    <div className="compendium-card">
                        <h3 className="compendium-card-title">Compliance Positioning</h3>
                        <p className="compendium-card-subtitle">NIST 800-63B & EU AI Act Article 50 alignment.</p>
                        <div className="compendium-chart-container" style={{ height: '200px' }} ref={barRef}>
                            {barInView && <Bar data={complianceData} options={complianceOptions} />}
                        </div>
                        <div style={{ marginTop: '1.5rem' }}>
                            <div className="compendium-bullet-item">
                                <span className="compendium-bullet-dot">●</span>
                                <p className="compendium-bullet-text"><strong style={{ color: '#F0F0F2' }}>NIST AAL3:</strong> Verifier Impersonation Resistance (Liveness)</p>
                            </div>
                            <div className="compendium-bullet-item">
                                <span className="compendium-bullet-dot">●</span>
                                <p className="compendium-bullet-text"><strong style={{ color: '#F0F0F2' }}>EU Article 50:</strong> Mandates detection/labeling of Deepfakes</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Row 3: Butler States */}
                <div className="compendium-card" style={{ marginBottom: '0' }}>
                    <h3 className="compendium-card-title" style={{ textAlign: 'center', marginBottom: '0.25rem' }}>
                        The "Butler" Interface States
                    </h3>
                    <p className="compendium-card-subtitle" style={{ textAlign: 'center' }}>
                        Progressive disclosure based on confidence levels.
                    </p>

                    <div className="compendium-states-grid">
                        {/* State 1: Invisible */}
                        <div className="compendium-state-card" style={{ borderColor: 'rgba(255, 255, 255, 0.08)' }}>
                            <div className="compendium-state-label" style={{ color: grayColor }}>State 01</div>
                            <div className="compendium-state-emoji">🛡️</div>
                            <div className="compendium-state-title" style={{ color: grayColor }}>Invisible</div>
                            <div className="compendium-state-confidence">Confidence &gt; 90%</div>
                            <div className="compendium-state-desc">Silent operation. Agent focuses on&nbsp;customer.</div>
                        </div>

                        {/* State 2: Nudge */}
                        <div className="compendium-state-card" style={{ borderColor: 'rgba(229, 185, 86, 0.4)' }}>
                            <div className="compendium-state-label" style={{ color: goldColor }}>State 02</div>
                            <div className="compendium-state-emoji">🤔</div>
                            <div className="compendium-state-title" style={{ color: goldColor }}>The Nudge</div>
                            <div className="compendium-state-confidence">Confidence 50-89%</div>
                            <div className="compendium-state-desc">Prompt to inject unpredictability (Liveness&nbsp;Challenge).</div>
                        </div>

                        {/* State 3: Shield */}
                        <div className="compendium-state-card" style={{ borderColor: 'rgba(244, 63, 94, 0.4)' }}>
                            <div className="compendium-state-label" style={{ color: redColor }}>State 03</div>
                            <div className="compendium-state-emoji">🛑</div>
                            <div className="compendium-state-title" style={{ color: redColor }}>The Shield</div>
                            <div className="compendium-state-confidence">Confidence &lt; 50%</div>
                            <div className="compendium-state-desc">Block detected. "Audio is Synthetic.&nbsp;Disconnect."</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StrategicCompendium;
