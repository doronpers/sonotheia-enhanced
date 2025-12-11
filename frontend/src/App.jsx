import { useState } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import PlatformOverview from "./components/PlatformOverview";
import EnterpriseFeatures from "./components/EnterpriseFeatures";
import Team from "./components/Team";
import ForensicButler from "./components/ForensicButler";
import Contact from "./components/Contact";
import Footer from "./components/Footer";
import ErrorBoundary from "./components/ErrorBoundary";
import AitheiaChat from "./components/AitheiaChat";
import HumanAnalysisLab from "./components/HumanAnalysisLab";

import DataFactoryController from "./components/DataFactoryController";

const App = () => {
  const [isLabOpen, setIsLabOpen] = useState(false);
  const [isSimOpen, setIsSimOpen] = useState(false);

  return (
    <ErrorBoundary>
      <Navbar
        onOpenLab={() => setIsLabOpen(true)}
        onOpenSim={() => setIsSimOpen(true)}
      />
      <HumanAnalysisLab isOpen={isLabOpen} onClose={() => setIsLabOpen(false)} />
      <DataFactoryController isOpen={isSimOpen} onClose={() => setIsSimOpen(false)} />
      <main id="main-content">
        <Hero />
        <Team />
        <PlatformOverview />
        <ForensicButler />
        <EnterpriseFeatures />
        <Contact />
      </main>
      <Footer />
      <AitheiaChat />
    </ErrorBoundary>
  );
};

export default App;

