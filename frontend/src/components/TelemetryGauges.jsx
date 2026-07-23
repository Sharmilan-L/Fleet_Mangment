import React from 'react';

export default function TelemetryGauges({ telemetry = {} }) {
  const speed = telemetry.speedKmh !== undefined ? telemetry.speedKmh : 0.0;
  const fwdAccel = telemetry.forwardAccelerationMs2 !== undefined ? telemetry.forwardAccelerationMs2 : 0.0;
  const latAccel = telemetry.lateralAccelerationMs2 !== undefined ? telemetry.lateralAccelerationMs2 : 0.0;
  const yawRate = telemetry.yawRateDegS !== undefined ? telemetry.yawRateDegS : 0.0;

  return (
    <div className="telemetry-grid">
      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span>Speed</span>
        </div>
        <div className="metric-value">
          {speed}
          <span className="metric-unit">km/h</span>
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span>Forward Accel</span>
        </div>
        <div className="metric-value">
          {fwdAccel}
          <span className="metric-unit">m/s²</span>
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span>Lateral Accel</span>
        </div>
        <div className="metric-value">
          {latAccel}
          <span className="metric-unit">m/s²</span>
        </div>
      </div>

      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span>Yaw Rate</span>
        </div>
        <div className="metric-value">
          {yawRate}
          <span className="metric-unit">°/s</span>
        </div>
      </div>
    </div>
  );
}
