import React from 'react';

export default function EventTimeline({ events = [] }) {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return '#ef4444';
      case 'WARNING':
      case 'MODERATE':
        return '#f59e0b';
      default:
        return '#3b82f6';
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-title">Real-Time Driving Event Timeline</div>
      {events.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, minHeight: '120px' }}>
          No events detected for this trip.
        </div>
      ) : (
        <div className="event-list">
          {events.map((e, index) => {
            const color = getSeverityColor(e.severity);
            const isOngoing = e.status === 'ACTIVE';
            return (
              <div key={e.id || index} className="event-item" style={{ position: 'relative' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ fontWeight: '700', fontSize: '14px', textTransform: 'uppercase', color: color }}>
                      {e.eventType.replace('_', ' ')}
                    </div>
                    {isOngoing && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '9px',
                        fontWeight: '800',
                        color: 'var(--accent-green)',
                        background: 'rgba(16, 185, 129, 0.12)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        border: '1px solid rgba(16, 185, 129, 0.25)',
                      }}>
                        <span className="pulse-dot" style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: 'var(--accent-green)',
                          display: 'inline-block',
                        }}></span>
                        ONGOING
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span>{new Date(e.startedAt || Date.now()).toLocaleTimeString()}</span>
                    <span style={{ color: 'var(--text-muted)' }}>•</span>
                    <span style={{ fontWeight: '500' }}>
                      {e.durationMs ? `Duration: ${(e.durationMs / 1000).toFixed(1)}s` : 'Duration: Ongoing'}
                    </span>
                    {e.primaryMeasurement !== undefined && e.primaryMeasurement !== null && (
                      <>
                        <span style={{ color: 'var(--text-muted)' }}>•</span>
                        <span>
                          Peak: {e.primaryMeasurement.toFixed(1)}
                          {e.eventType.includes('SPEEDING') || e.eventType.includes('OVERSPEEDING') ? ' km/h' : ' m/s²'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <div style={{ textTransform: 'uppercase', fontSize: '11px', fontWeight: '800', color: color, background: `${color}15`, padding: '4px 10px', borderRadius: '12px', border: `1px solid ${color}40`, alignSelf: 'center' }}>
                  {e.severity}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
