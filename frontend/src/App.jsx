import React, { useState, useEffect, useRef } from 'react';
import ScoreGauge from './components/ScoreGauge';
import TelemetryGauges from './components/TelemetryGauges';
import EventTimeline from './components/EventTimeline';
import SimulatorControl from './components/SimulatorControl';
import LiveMap from './components/LiveMap';

export default function App() {
  const [options, setOptions] = useState(null);
  const [selectedDriver, setSelectedDriver] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState('');
  const [activeTrip, setActiveTrip] = useState(null);
  const [telemetry, setTelemetry] = useState({});
  const [events, setEvents] = useState([]);
  const [score, setScore] = useState(100.0);
  const [riskLevel, setRiskLevel] = useState('LOW');
  const [simStatus, setSimStatus] = useState({ status: 'STOPPED' });
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef = useRef(null);

  // 1. Fetch start options on load & restore active session if exists
  useEffect(() => {
    fetch('/api/v1/trips/start-options')
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setOptions(data.data);
          if (data.data.drivers.length > 0) setSelectedDriver(data.data.drivers[0].id);
          if (data.data.vehicles.length > 0) setSelectedVehicle(data.data.vehicles[0].id);
        }
      })
      .catch((err) => console.error('Failed to load start options', err));

    // Restore active session
    fetch('/api/v1/trips/active')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data.length > 0) {
          const active = data.data[0];
          fetch(`/api/v1/trips/${active.id}/live`)
            .then((res) => res.json())
            .then((liveData) => {
              if (liveData.success) {
                const tripData = liveData.data;
                setActiveTrip({
                  id: tripData.trip.id,
                  tripCode: tripData.trip.tripCode,
                  currentScore: tripData.score?.currentScore ?? 100.0,
                  riskLevel: tripData.score?.riskLevel ?? 'LOW',
                  driver: tripData.driver,
                  vehicle: tripData.vehicle,
                  device: tripData.device,
                });
                setScore(tripData.score?.currentScore ?? 100.0);
                setRiskLevel(tripData.score?.riskLevel ?? 'LOW');
                setEvents(tripData.events || []);
                setTelemetry(tripData.latestTelemetry || {});
              }
            })
            .catch((err) => console.error('Failed to fetch live trip snapshot', err));
        }
      })
      .catch((err) => console.error('Failed to check active trips', err));
  }, []);

  // 2. Poll simulator status when active
  useEffect(() => {
    let interval;
    if (activeTrip) {
      interval = setInterval(() => {
        fetch('/api/v1/simulator/status')
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              setSimStatus(data.data);
            }
          })
          .catch((err) => console.error(err));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [activeTrip]);

  // 3. Connect to WebSocket when trip is active
  useEffect(() => {
    if (!activeTrip) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/trips/${activeTrip.id}`;

    console.log('Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log('WebSocket Event Received:', msg);
      
      if (msg.type === 'TELEMETRY_SNAPSHOT') {
        setTelemetry(msg.data);
      } else if (msg.type === 'EVENT_DETECTED') {
        setEvents((prev) => {
          const index = prev.findIndex((e) => e.id === msg.data.id);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...msg.data };
            return updated;
          } else {
            return [msg.data, ...prev];
          }
        });
      } else if (msg.type === 'SCORE_UPDATED') {
        setScore(msg.data.newScore);
        setRiskLevel(msg.data.currentRiskLevel);
      } else if (msg.type === 'TRIP_STATUS_CHANGED') {
        if (msg.data.status === 'COMPLETED') {
          setActiveTrip(null);
        }
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket connection closed');
    };

    return () => {
      if (ws) ws.close();
    };
  }, [activeTrip]);

  const handleStartTrip = async () => {
    if (!selectedDriver || !selectedVehicle) return;
    try {
      const res = await fetch('/api/v1/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          driverId: selectedDriver,
          vehicleId: selectedVehicle,
          tripMode: 'TEST',
          appliedSpeedLimitKmh: 60.0,
          startReason: 'Pitch presentation simulation run',
        }),
      });
      const data = await res.json();
      if (data.success) {
        setActiveTrip(data.data);
        setScore(data.data.currentScore);
        setRiskLevel(data.data.riskLevel);
        setEvents([]);
        setTelemetry({});
      } else {
        alert(data.error?.message || 'Failed to start trip');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleEndTrip = async () => {
    if (!activeTrip) return;
    try {
      const res = await fetch(`/api/v1/trips/${activeTrip.id}/end`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endReason: 'Demo complete' }),
      });
      const data = await res.json();
      if (data.success) {
        setActiveTrip(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <header className="app-header">
        <div className="brand-container">
          <div className="brand-logo">E</div>
          <h1 className="brand-title">EvolveX</h1>
          <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>|</span>
          <span style={{ fontSize: '14px', fontWeight: '500', color: 'var(--text-secondary)' }}>Pitch Demo Dashboard</span>
        </div>
        <div className="simulation-badge">
          <span className="pulse-dot"></span>
          Simulation Mode — Test Data
        </div>
      </header>

      <main className="dashboard-grid">
        {/* Left Column: Trip Configuration */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div className="panel-title">Trip Setup</div>
            {!activeTrip ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Driver</label>
                  <select
                    className="select-input"
                    value={selectedDriver}
                    onChange={(e) => setSelectedDriver(e.target.value)}
                  >
                    {options?.drivers.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Vehicle</label>
                  <select
                    className="select-input"
                    value={selectedVehicle}
                    onChange={(e) => setSelectedVehicle(e.target.value)}
                  >
                    {options?.vehicles.map((v) => (
                      <option key={v.id} value={v.id}>{v.registrationNumber}</option>
                    ))}
                  </select>
                </div>

                <button className="btn btn-primary" onClick={handleStartTrip} style={{ marginTop: '8px' }}>
                  Start Trip
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Active Trip Code</div>
                    <div style={{ fontWeight: '700', fontSize: '14px', marginTop: '2px', color: 'var(--accent-cyan)' }}>{activeTrip.tripCode}</div>
                  </div>
                  
                  {activeTrip.driver?.name && (
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Driver</div>
                      <div style={{ fontWeight: '600', fontSize: '13px', marginTop: '2px', color: 'var(--text-primary)' }}>{activeTrip.driver.name}</div>
                    </div>
                  )}

                  {activeTrip.vehicle?.registrationNumber && (
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Vehicle</div>
                      <div style={{ fontWeight: '600', fontSize: '13px', marginTop: '2px', color: 'var(--text-primary)' }}>{activeTrip.vehicle.registrationNumber}</div>
                    </div>
                  )}

                  {activeTrip.device?.deviceCode && (
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Device Code</div>
                      <div style={{ fontWeight: '600', fontSize: '13px', marginTop: '2px', color: 'var(--text-primary)' }}>{activeTrip.device.deviceCode}</div>
                    </div>
                  )}

                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>WebSocket Status</div>
                    <div style={{ fontWeight: '700', fontSize: '13px', color: wsConnected ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '2px' }}>
                      {wsConnected ? 'Connected' : 'Disconnected'}
                    </div>
                  </div>
                </div>

                <button className="btn btn-danger" onClick={handleEndTrip}>
                  End Trip
                </button>
              </div>
            )}
          </div>

          <SimulatorControl
            tripId={activeTrip?.id}
            onStartSimulation={(status) => setSimStatus(status)}
            simulationStatus={simStatus}
          />
        </div>

        {/* Center Column: Live Analytics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <TelemetryGauges telemetry={telemetry} />
          <div className="glass-panel map-panel-card" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column' }}>
            <div className="panel-title">Real-Time Vehicle Map Tracks</div>
            <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', border: '1px dashed var(--border-color)', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
              {telemetry.latitude ? (
                <LiveMap latitude={telemetry.latitude} longitude={telemetry.longitude} events={events} />
              ) : (
                <div style={{ display: 'flex', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Awaiting GPS signal from simulation runner...</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Events & Score */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <ScoreGauge score={score} riskLevel={riskLevel} />
          <div style={{ flex: 1 }}>
            <EventTimeline events={events} />
          </div>
        </div>
      </main>
    </div>
  );
}
