import React from 'react';

const StrategicCompendium = () => {
    return (
        <div className="compendium-container" style={{ padding: 'var(--space-xl) var(--space-md)' }}>
            <div className="compendium-section" style={{ maxWidth: '1000px', margin: '0 auto' }}>
                {/* Section Header */}
                <h2 className="section-title" style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>Strategic Intelligence</h2>
                <p className="section-subtitle" style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto var(--space-xl)', color: 'var(--medium-gray)' }}>
                    Our physics-based approach detects what Generative AI cannot yet simulate: organic chaotic variance.
                </p>

                {/* Core Pillars - Replaces Chart 1 */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginBottom: '4rem' }}>

                    {/* Pillar 1 */}
                    <div style={{
                        borderTop: '1px solid var(--signal-gold)',
                        paddingTop: '1rem'
                    }}>
                        <h3 style={{ fontSize: '1.1rem', color: 'var(--acoustic-silver)', marginBottom: '0.5rem', fontFamily: 'Space Grotesk, sans-serif' }}>
                            Spectral Flatness
                        </h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--medium-gray)', lineHeight: '1.6' }}>
                            Generative AI minimizes loss functions, creating 'statistically perfect' audio. Our engine detects this unnatural perfection, flagging signals that lack the requisite micro-variance of organic speech.
                        </p>
                    </div>

                    {/* Pillar 2 */}
                    <div style={{
                        borderTop: '1px solid var(--trust-green)',
                        paddingTop: '1rem'
                    }}>
                        <h3 style={{ fontSize: '1.1rem', color: 'var(--acoustic-silver)', marginBottom: '0.5rem', fontFamily: 'Space Grotesk, sans-serif' }}>
                            Respiration Dynamics
                        </h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--medium-gray)', lineHeight: '1.6' }}>
                            Synthetic voices often lack coherent respiration patterns. We analyze breath mechanics relative to phrase length, identifying physically impossible speech continuity.
                        </p>
                    </div>

                    {/* Pillar 3 */}
                    <div style={{
                        borderTop: '1px solid var(--alert-red)',
                        paddingTop: '1rem'
                    }}>
                        <h3 style={{ fontSize: '1.1rem', color: 'var(--acoustic-silver)', marginBottom: '0.5rem', fontFamily: 'Space Grotesk, sans-serif' }}>
                            Micro-Tremor Analysis
                        </h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--medium-gray)', lineHeight: '1.6' }}>
                            The human vocal tract produces sub-perceptual tremors (8-12Hz) due to muscle tension. These are typically absent in diffusion-model generated audio.
                        </p>
                    </div>

                </div>

                {/* Compliance Section - Replaces Chart 2 */}
                <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--subtle-gray)',
                    borderRadius: 'var(--radius-md)',
                    padding: '2rem'
                }}>
                    <h3 style={{ fontSize: '1.2rem', marginBottom: '1.5rem' }}>Compliance & Privacy Standards</h3>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                        <div>
                            <h4 style={{ fontSize: '0.9rem', color: 'var(--acoustic-silver)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05rem' }}>
                                NIST 800-63B
                            </h4>
                            <p style={{ fontSize: '0.85rem', color: 'var(--medium-gray)' }}>
                                Aligned with Identity Assurance Level 3 (IAL3) requirements for liveness detection and verifier impersonation resistance.
                            </p>
                        </div>
                        <div>
                            <h4 style={{ fontSize: '0.9rem', color: 'var(--acoustic-silver)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05rem' }}>
                                EU AI Act (Article 50)
                            </h4>
                            <p style={{ fontSize: '0.85rem', color: 'var(--medium-gray)' }}>
                                Meets transparency obligations for deepfake detection systems. Labels synthetic content clearly (95%+ confidence).
                            </p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default StrategicCompendium;
