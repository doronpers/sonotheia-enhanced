import React from 'react';
import About from './About';
import Technology from './Technology';
import StrategicCompendium from './StrategicCompendium';

const PlatformOverview = () => {
    return (
        <div id="platform-wrapper">
            <About />
            <Technology />
            <StrategicCompendium />
        </div>
    );
};

export default PlatformOverview;
