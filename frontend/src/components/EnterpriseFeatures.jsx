const CAPABILITIES = [
  {
    title: "Deepfake Detection",
    description: "Physics-based signal analysis of liveness and spectral integrity across replay, deepfake, and voice conversion attacks.",
    icon: "🔬"
  },
  {
    title: "SAR Documentation",
    description: "Automated evidence packages with key detection factors, timelines, and file hashes ready for compliance filing.",
    icon: "📋"
  },
  {
    title: "Risk Scoring",
    description: "Real-time assessment with configurable thresholds and factor-level explainability—no black-box scores.",
    icon: "📊"
  },
  {
    title: "Human\u2011in\u2011the\u2011Loop",
    description: "Designed for analyst review with clear visual indicators for rapid decision making and compliance oversight.",
    icon: "👥"
  },
  {
    title: "Audit Logging",
    description: "Comprehensive analysis tracking with granular event logs and tamper-evident findings for regulatory compliance.",
    icon: "📝"
  },
  {
    title: "API & SDK Integration",
    description: "REST API and React Native SDK for seamless integration into contact centers, MFA flows, and fraud workflows.",
    icon: "🔗"
  }
];

const EnterpriseFeatures = () => (
  <section id="enterprise" className="enterprise-features">
    <div className="section-container">
      <h2 className="section-title">Enterprise Platform</h2>
      <p className="section-text">
        Our enterprise platform turns raw audio into case-ready risk signals,
        with audit trails tailored for compliance teams.
      </p>

      <div className="enterprise-grid">
        {CAPABILITIES.map((feature) => (
          <div key={feature.title} className="enterprise-card">
            <span className="enterprise-icon">{feature.icon}</span>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export default EnterpriseFeatures;
