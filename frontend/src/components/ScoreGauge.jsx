import React from 'react';

export default function ScoreGauge({ score = 100, riskLevel = 'LOW' }) {
  const roundedScore = Math.round(score * 10) / 10;
  
  // Calculate SVG stroke offset for gauge (0 to 100)
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (roundedScore / 100) * circumference;

  let gaugeColor = '#10b981'; // LOW
  if (riskLevel === 'MEDIUM' || (score >= 60 && score < 80)) {
    gaugeColor = '#f59e0b';
  } else if (riskLevel === 'HIGH' || score < 60) {
    gaugeColor = '#ef4444';
  }

  return (
    <div className="glass-panel score-card">
      <div className="panel-title">Driver Safety Score</div>
      <div className="gauge-container">
        <svg width="180" height="180" viewBox="0 0 180 180">
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="14"
          />
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="none"
            stroke={gaugeColor}
            strokeWidth="14"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease, stroke 0.5s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>
        <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span className="score-value" style={{ color: gaugeColor }}>{roundedScore}</span>
          <span className="score-label">pts</span>
        </div>
      </div>
      <div className={`risk-badge risk-${riskLevel.toLowerCase()}`}>
        {riskLevel} RISK
      </div>
    </div>
  );
}
