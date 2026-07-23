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
            return (
              <div key={e.id || index} className="event-item">
                <div>
                  <div style={{ fontWeight: '700', fontSize: '14px', textTransform: 'uppercase', color: color }}>
                    {e.eventType.replace('_', ' ')}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {new Date(e.startedAt || Date.now()).toLocaleTimeString()}
                  </div>
                </div>
                <div style={{ textTransform: 'uppercase', fontSize: '11px', fontWeight: '800', color: color, background: `${color}15`, padding: '4px 10px', borderRadius: '12px', border: `1px solid ${color}40` }}>
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
