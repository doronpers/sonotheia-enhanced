import { useRef, useState, useEffect } from 'react';
import { LockIcon, ShieldIcon, CheckBadgeIcon } from "./icons/SecurityIcons";

const Hero = () => {
  const videoRef = useRef(null);
  const [hasPlayedInitialRotation, setHasPlayedInitialRotation] = useState(false);

  // Load and play one rotation on mount
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Set up the video source
    video.src = '/svid.mp4';
    video.load();

    // Use refs to track state inside event handlers to avoid stale closures
    let hasPlayed = false;

    const handleTimeUpdate = () => {
      // When video reaches near the end (one rotation), pause it
      if (video.duration && video.currentTime >= video.duration - 0.1 && !hasPlayed) {
        video.pause();
        video.currentTime = 0;
        hasPlayed = true;
        setHasPlayedInitialRotation(true);
      }
    };

    const handleCanPlay = async () => {
      if (!hasPlayed) {
        try {
          await video.play();
        } catch {
          // Silently handle autoplay rejection (browser policy)
          hasPlayed = true;
          setHasPlayedInitialRotation(true);
        }
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('canplay', handleCanPlay);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('canplay', handleCanPlay);
    };
  }, []);

  const playVideo = async () => {
    if (videoRef.current) {
      try {
        await videoRef.current.play();
      } catch {
        // Silently handle play rejection
      }
    }
  };

  const handleMouseEnter = () => {
    if (hasPlayedInitialRotation) {
      playVideo();
    }
  };

  const handleMouseLeave = () => {
    if (videoRef.current && hasPlayedInitialRotation) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0; // Reset to beginning
    }
  };

  const handleKeyDown = async (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (videoRef.current) {
        if (videoRef.current.paused) {
          await playVideo();
        } else {
          videoRef.current.pause();
          videoRef.current.currentTime = 0;
        }
      }
    }
  };

  return (
    <section id="home" className="hero">
      <div className="hero-content">
        <div
          className="hero-logo"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onKeyDown={handleKeyDown}
          role="button"
          tabIndex={0}
          aria-label="Play animated Sonotheia logo (press Enter or Space to toggle)"
        >
          <video
            ref={videoRef}
            loop
            muted
            playsInline
            preload="none"
            className="hero-logo-video"
            aria-hidden="true"
            poster="/logo-s.png"
          />
        </div>
        <h1 className="hero-title"><span className="hero-title-nowrap">True Voice. <span className="hero-verified">Verified.</span></span></h1>
        <p className="hero-subtitle">
          <span className="hero-subtitle-nowrap">Physics-based authenticity scoring for high-risk communications.</span>
        </p>
        <ul className="hero-proof-list desktop-only">
          <li className="proof-item-1"><strong>Bioacoustics</strong> expose what deepfakes cannot fake.</li>
          <li className="proof-item-2"><strong>Audit-ready</strong> evidence trails align with SOC 2 standards.</li>
          <li className="proof-item-3"><strong>Deployment-aware</strong> workflows integrate with MFA flows.</li>
        </ul>
        <p className="hero-subtext">
          <strong>Generative AI is probabilistic. Sonotheia is deterministic.</strong>
          <br />
          We validate the acoustic reality of the speaker, independent of language, accent, or model architecture.
          <br />
          <span className="hero-subtext-second">AI Speed. Human Accountability.</span>
        </p>
        <div className="cta-buttons">
          <a href="#demo" className="btn btn-primary" aria-label="Try our audio detection demo">TRY DEMO</a>
          <a href="#science" className="btn btn-primary" aria-label="Learn about our detection technology">HOW IT WORKS</a>
          <a href="#contact" className="btn btn-primary" aria-label="Contact us for more information">CONTACT US</a>
        </div>
        <div className="trust-badges" role="list" aria-label="Security and compliance features">
          <div className="trust-badge-item" role="listitem" title="We never persist uploaded audio; everything is processed in memory.">
            <LockIcon aria-hidden="true" />
            <span>No Data Stored</span>
          </div>
          <div className="trust-badge-item" role="listitem" title="TLS 1.3 enforced for loads and API callbacks.">
            <ShieldIcon aria-hidden="true" />
            <span>End-to-End Encrypted</span>
          </div>
          <div className="trust-badge-item" role="listitem" title="Independent auditor attestation available on request.">
            <CheckBadgeIcon aria-hidden="true" />
            <span>SOC 2 Compliant</span>
          </div>
        </div>


      </div>
    </section >
  );
};

export default Hero;
