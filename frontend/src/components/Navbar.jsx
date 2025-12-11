const Navbar = ({ onOpenLab, onOpenSim }) => (
  <nav className="navbar" role="navigation" aria-label="Main navigation">
    <div className="nav-container">
      <a href="#home" className="nav-logo" aria-label="Sonotheia - Return to home">
        SONOTHEIA
      </a>
      <ul className="nav-menu" role="menubar">
        <li role="none">
          <button
            onClick={onOpenLab}
            className="nav-link text-emerald-400 hover:text-emerald-300 font-mono text-sm tracking-wider mr-4"
            role="menuitem"
          >
            [ R&D LAB ]
          </button>
        </li>
        <li role="none">
          <button
            onClick={onOpenSim}
            className="nav-link text-purple-400 hover:text-purple-300 font-mono text-sm tracking-wider mr-4"
            role="menuitem"
          >
            [ SIMULATION ]
          </button>
        </li>
        <li role="none">
          <a href="#team" className="nav-link" role="menuitem" aria-label="Navigate to leadership team section">
            LEADERSHIP
          </a>
        </li>
        <li role="none">
          <a href="#platform" className="nav-link" role="menuitem" aria-label="Navigate to platform overview">
            PLATFORM
          </a>
        </li>
        <li role="none">
          <a href="#demo" className="nav-link" role="menuitem" aria-label="Navigate to demo simulation section">
            DEMO
          </a>
        </li>
        <li role="none">
          <a href="#contact" className="nav-link nav-link-primary" role="menuitem" aria-label="Request a briefing - primary action">
            REQUEST BRIEFING
          </a>
        </li>
      </ul>

      {/* Mobile Only Demo Button */}
      <a href="#demo" className="mobile-only mobile-demo-btn" aria-label="Go to Demo">
        TRY DEMO
      </a>
    </div>
  </nav>
);

export default Navbar;
