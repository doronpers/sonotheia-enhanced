import React from 'react';

const About = () => {
  return (
    <section id="about" className="about" aria-labelledby="about-title">
      <div className="section-container">
        <h2 id="about-title" className="section-title">
          About <span className="sonotheia-brand">Sonotheia</span>
        </h2>
        <p className="section-text">
          Sonotheia provides real-time deepfake voice detection and post-incident audio forensics.
          In an era where biometric identifiers are easily cloned, Sonotheia validates the physics of the speaker, not just the identity.
          We provide the 'Proof of Life' layer for high-stakes voice channels.
        </p>

        <div className="enterprise-features">
          <h3 className="subsection-title" id="capabilities-title">Core Capabilities</h3>
          <div className="features-grid" role="list" aria-labelledby="capabilities-title">
            <article className="feature-card" role="listitem">
              <h4>Multi-Layer Detection</h4>
              <p>Proprietary methods that identify deepfakes missed by model fingerprinting alone—including unknown models and emerging attack techniques.</p>
            </article>
            <article className="feature-card" role="listitem">
              <h4>Risk-Based MFA Orchestration</h4>
              <p>Combines voice, device, and behavioral signals with explainable factor weights for AML/KYC reviews and step-up authentication.</p>
            </article>
            <article className="feature-card" role="listitem">
              <h4>Compliance-Ready Workflows</h4>
              <p>Designed to support GDPR, FinCEN/AML, KYC, and SOC 2 workflows with SAR-ready documentation and audit trails.</p>
            </article>
            <article className="feature-card" role="listitem">
              <h4>Immutable Evidence Storage</h4>
              <p>Tamper-evident storage with Object Lock, SHA-256 hashing, and full chain-of-custody metadata—optimized for investigations and regulator reviews.</p>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
