import React from 'react';

const FEATURES = [
  {
    title: "Bio-Acoustic Dynamics",
    description:
      "Physics-based modeling of human speech production mechanics. Our sensors track impossible formant velocities and phase discontinuities that generative models fail to simulate.",
    redacted: true
  },
  {
    title: "Multi-Sensor Fusion",
    description: "Deterministic arbitration layer that combines spectral, resonant, and temporal signals. Unlike black-box ML, our fusion engine provides granular, explainable evidence for every alert.",
    redacted: true
  },
  {
    title: "Liveness Detection",
    description: "Distinguishes live speakers from recordings and synthetic audio with factor-level evidence chains for audit review.",
    redacted: true
  },
  {
    title: "Adaptive Scoring",
    description: "Adjusts threat models based on emerging attack patterns—detecting unknown generators without retraining.",
    redacted: true
  },
];

const Technology = () => {
  return (
    <section id="technology" className="technology" aria-labelledby="technology-title">
      <div className="section-container">
        <h2 id="technology-title" className="section-title">Detection Technology</h2>
        <p className="section-text tech-intro">
          <span className="sonotheia-brand">Sonotheia</span> combines acoustic science with machine learning to expose
          what pure model fingerprinting cannot—helping detect unknown threats and emerging attack techniques.
        </p>
        <div className="features-grid" role="list" aria-labelledby="technology-title">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="feature-card" role="listitem">
              <h3>
                {feature.title}
                {feature.redacted && (
                  <span className="redacted-badge" aria-label="Proprietary methodology">
                    ●
                  </span>
                )}
              </h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
        <p className="proprietary-notice" role="note" aria-label="Proprietary methodology notice">
          <span className="redacted-badge" aria-hidden="true">●</span> Indicates proprietary methodology —
          expanded technical details available under NDA.
        </p>
      </div>
    </section>
  );
};

export default Technology;
