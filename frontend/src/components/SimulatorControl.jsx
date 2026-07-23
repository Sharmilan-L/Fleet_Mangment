import React, { useState, useEffect } from 'react';

export default function SimulatorControl({ tripId, onStartSimulation, simulationStatus = {} }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [intervalMs, setIntervalMs] = useState(1000);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/v1/simulator/scenarios')
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setScenarios(data.data);
          if (data.data.length > 0) {
            setSelectedScenario(data.data[0].code);
          }
        }
      })
      .catch((err) => console.error('Failed to load scenarios', err));
  }, []);

  const handleStart = async () => {
    if (!tripId || !selectedScenario) return;
    setLoading(true);
    try {
      const res = await fetch('/api/v1/simulator/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tripId,
          scenarioCode: selectedScenario,
          packetIntervalMs: Number(intervalMs),
        }),
      });
      const data = await res.json();
      if (data.success) {
        onStartSimulation(data.data);
      } else {
        alert(data.error?.message || 'Failed to start simulation');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      const res = await fetch('/api/v1/simulator/pause', { method: 'POST' });
      await res.json();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResume = async () => {
    try {
      const res = await fetch('/api/v1/simulator/resume', { method: 'POST' });
      await res.json();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStop = async () => {
    try {
      const res = await fetch('/api/v1/simulator/stop', { method: 'POST' });
      await res.json();
    } catch (err) {
      console.error(err);
    }
  };

  const isRunning = simulationStatus.status === 'RUNNING';
  const isPaused = simulationStatus.status === 'PAUSED';

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="panel-title">Telemetry Scenario Simulator</div>
      
      {!isRunning && !isPaused ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Select Scenario</label>
            <select
              className="select-input"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
            >
              {scenarios.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Packet Interval (ms)</label>
            <input
              type="number"
              className="select-input"
              value={intervalMs}
              onChange={(e) => setIntervalMs(Math.max(250, Number(e.target.value)))}
              min="250"
              max="5000"
            />
          </div>

          <button className="btn btn-primary" onClick={handleStart} disabled={loading || !tripId} style={{ marginTop: '8px' }}>
            {loading ? 'Starting...' : 'Start Scenario'}
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Active Scenario</div>
            <div style={{ fontWeight: '700', fontSize: '15px', color: 'var(--accent-yellow)', marginTop: '4px' }}>{simulationStatus.scenarioCode}</div>
            
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>Status</div>
            <div style={{ fontWeight: '700', fontSize: '13px', color: isRunning ? 'var(--accent-green)' : 'var(--accent-yellow)', marginTop: '4px' }}>
              {simulationStatus.status}
            </div>

            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <span>Progress</span>
                <span>{simulationStatus.progressPercent}%</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${simulationStatus.progressPercent}%`, height: '100%', background: 'var(--accent-blue)', transition: 'width 0.3s ease' }}></div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {isRunning ? (
              <button className="btn btn-secondary" onClick={handlePause} style={{ flex: 1 }}>Pause</button>
            ) : (
              <button className="btn btn-primary" onClick={handleResume} style={{ flex: 1 }}>Resume</button>
            )}
            <button className="btn btn-danger" onClick={handleStop} style={{ flex: 1 }}>Stop</button>
          </div>
        </div>
      )}
    </div>
  );
}
