// Bio content as React elements to avoid dangerouslySetInnerHTML
const FOUNDERS = [
  {
    name: "Doron Reizes",
    title: "Co-Founder & President",
    bio: (
      <>
        <strong>20+ years</strong> in post-production at <strong>Sony Music Studios</strong>, <strong>Sync Sound</strong>, and <strong>Creative Group</strong>. <strong>MPSE</strong> & <strong>AES</strong> member and <strong>Full Sail University</strong> <strong>course director</strong>. <strong style={{ whiteSpace: 'nowrap' }}>M.S. Valedictorian - Innovation &</strong> <strong>Entrepreneurship</strong>. His ear for authenticity and deep signal analysis expertise form the foundation&nbsp;of&nbsp;<strong>Sonotheia's</strong> detection methodology.
      </>
    )
  },
  {
    name: 'Alexander "Sasha" Forostenko',
    title: "Co-Founder & CEO",
    bio: (
      <>
        Former <strong>managing director and head of compliance regulatory at Charles Schwab</strong> ($8.5T+ AUM), with senior roles at <strong>SVB</strong>, <strong>Citizens</strong>, <strong>RBS</strong>, and <strong>Morgan Stanley</strong>. <strong>Juris Doctorate</strong> and <strong>licensed attorney</strong> with <strong>15+ years</strong> navigating <strong>SEC</strong>, <strong>FINRA</strong>, <strong>CFTC</strong>, and <strong>Federal Reserve</strong> complexity. His institutional credibility and regulatory fluency anchor <strong>Sonotheia's</strong> compliance-first positioning.
      </>
    )
  }
];

const Team = () => (
  <section id="team" className="team" aria-labelledby="team-title">
    <div className="section-container">
      <h2 id="team-title" className="section-title">Leadership</h2>
      <p className="section-text">
        Sonotheia's founding team uniquely combines world-class audio production expertise with senior regulatory compliance leadership from&nbsp;America's&nbsp;largest&nbsp;financial&nbsp;institutions.
      </p>

      <div className="team-grid" role="list" aria-labelledby="team-title">
        {FOUNDERS.map((founder) => (
          <article key={founder.name} className="team-card" role="listitem">
            <h3 className="team-name">{founder.name}</h3>
            <p className="team-title">{founder.title}</p>
            <p className="team-bio">{founder.bio}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
);

export default Team;
