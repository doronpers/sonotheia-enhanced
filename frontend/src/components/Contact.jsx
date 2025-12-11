const Contact = () => (
  <section id="contact" className="contact" aria-labelledby="contact-title">
    <div className="section-container">
      <h2 id="contact-title" className="section-title">SECURE COMMUNICATIONS</h2>
      <p className="section-text">
        Don't trust blindly. Demand explainability. We're here to listen.
      </p>

      <div className="contact-cta">
        <a
          href="mailto:inquiries@sonotheia.ai?subject=Briefing%20Request"
          className="btn btn-primary"
          aria-label="Send email to inquiries@sonotheia.ai to request a briefing"
        >
          Let's Talk
        </a>
        <p className="contact-tagline" style={{ marginTop: '1rem', fontStyle: 'italic', color: 'rgba(255,255,255,0.7)' }}>
          We're experienced listeners.
        </p>
        <p className="contact-email">
          <a
            href="mailto:inquiries@sonotheia.ai"
            aria-label="Email inquiries@sonotheia.ai"
          >
            inquiries@sonotheia.ai
          </a>
        </p>
      </div>
    </div>
  </section>
);

export default Contact;

