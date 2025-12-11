import React from 'react';

// Simple inline SVG icon
const ShieldCheck = ({ className, style }) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} style={{ width: '1em', height: '1em', ...style }}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 12 15 15 9" />
    </svg>
);

const DashboardTopBar = () => {
    return (
        <div className="dashboard-topbar">
            <div className="dashboard-branding">
                <ShieldCheck className="dashboard-brand-icon" />
                <span className="dashboard-brand-text">AIETHIA EXPLAINABLE THREAT ASSESSMENT</span>
            </div>
        </div>
    );
};

export default DashboardTopBar;
