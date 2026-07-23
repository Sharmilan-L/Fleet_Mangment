import React, { useEffect, useRef } from 'react';

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

const getPopupContent = (e, color) => {
  return `
    <div style="color: #ffffff; font-family: inherit; font-size: 12px; line-height: 1.4;">
      <div style="font-weight: 700; color: ${color}; text-transform: uppercase; margin-bottom: 2px;">
        ${e.eventType.replace('_', ' ')}
      </div>
      <div style="color: #a0a0ab;">
        Severity: <span style="font-weight: 600; color: #ffffff;">${e.severity}</span><br/>
        Time: <span style="color: #ffffff;">${new Date(e.startedAt).toLocaleTimeString()}</span>
        ${e.durationMs ? `<br/>Duration: <span style="color: #ffffff;">${(e.durationMs / 1000).toFixed(1)}s</span>` : ''}
      </div>
    </div>
  `;
};

export default function LiveMap({ latitude, longitude, events = [] }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const pathRef = useRef(null);
  const pathCoordinatesRef = useRef([]);
  const eventMarkersRef = useRef({});

  useEffect(() => {
    // Check if Leaflet is loaded from CDN
    if (!window.L) {
      console.error('Leaflet library not loaded.');
      return;
    }

    // Initialize Leaflet Map
    const initialLat = latitude || 6.9271;
    const initialLng = longitude || 79.8612;

    const map = window.L.map(mapContainerRef.current, {
      zoomControl: false,
    }).setView([initialLat, initialLng], 14);

    // Add Dark Mode/Sleek Theme Map Tiles from CartoDB (matches premium theme)
    window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; CartoDB &copy; OpenStreetMap',
      maxZoom: 20,
    }).addTo(map);

    // Add Zoom Control at bottom right
    window.L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Custom Icon for Vehicle
    const vehicleIcon = window.L.icon({
      iconUrl: 'https://images.rawpixel.com/image_png_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIzLTA4L3Jhd3BpeGVsX29mZmljZV8zM19hX3NpbXBsZV9mbGF0X2ljb25fb2ZfYV9jYXJfX21pbmltYWxpc3RfZGVzaWdfX19lMzQ2NGRiOC05NDM5LTQ3OTAtOTgyNi1kNGUxN2I1MGQ0MDYucG5n.png', // Fallback simple car png
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    // Create Marker and add to Map
    const marker = window.L.marker([initialLat, initialLng]).addTo(map);
    markerRef.current = marker;

    // Create empty Polyline path for vehicle route trail
    const path = window.L.polyline([], {
      color: '#00e5ff', // var(--accent-cyan)
      weight: 4,
      opacity: 0.8,
      dashArray: '5, 10',
    }).addTo(map);
    pathRef.current = path;

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update position and route path when new coordinates arrive
  useEffect(() => {
    if (!mapRef.current || !latitude || !longitude) return;

    const newPos = [latitude, longitude];

    // Center map on new position
    mapRef.current.panTo(newPos);

    // Update marker position
    if (markerRef.current) {
      markerRef.current.setLatLng(newPos);
    }

    // Append to route trail
    pathCoordinatesRef.current.push(newPos);
    if (pathRef.current) {
      pathRef.current.setLatLngs(pathCoordinatesRef.current);
    }
  }, [latitude, longitude]);

  // Reset route path when coordinates are cleared (trip ends/restarts)
  useEffect(() => {
    if (!latitude && !longitude) {
      pathCoordinatesRef.current = [];
      if (pathRef.current) {
        pathRef.current.setLatLngs([]);
      }
    }
  }, [latitude, longitude]);

  // Render and update event markers on map
  useEffect(() => {
    if (!mapRef.current) return;

    const currentMarkers = eventMarkersRef.current;

    // 1. Remove markers for events that are no longer in the events list
    const eventIds = new Set(events.filter((e) => e.latitude && e.longitude).map((e) => e.id));
    Object.keys(currentMarkers).forEach((id) => {
      if (!eventIds.has(id)) {
        currentMarkers[id].remove();
        delete currentMarkers[id];
      }
    });

    // 2. Add or update markers for events
    events.forEach((e) => {
      if (!e.latitude || !e.longitude) return;

      const pos = [e.latitude, e.longitude];
      const color = getSeverityColor(e.severity);

      if (currentMarkers[e.id]) {
        // Update popup content in case duration or severity changed
        currentMarkers[e.id].getPopup().setContent(getPopupContent(e, color));
      } else {
        // Create a new marker with a beautiful glowing indicator matching our premium dark theme
        const icon = window.L.divIcon({
          html: `<div style="
            background: ${color};
            box-shadow: 0 0 10px ${color}, inset 0 0 5px rgba(0,0,0,0.5);
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 9px;
            cursor: pointer;
            animation: pulse-marker 1.5s infinite;
          ">!</div>`,
          className: '',
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        });

        const marker = window.L.marker(pos, { icon }).addTo(mapRef.current);
        marker.bindPopup(getPopupContent(e, color), {
          className: 'custom-leaflet-popup',
        });
        currentMarkers[e.id] = marker;
      }
    });
  }, [events]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <style>{`
        .leaflet-popup-content-wrapper {
          background: #18181c !important;
          color: #ffffff !important;
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 8px !important;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6) !important;
        }
        .leaflet-popup-tip {
          background: #18181c !important;
        }
        @keyframes pulse-marker {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.15); opacity: 0.8; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '8px',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}
      />
    </div>
  );
}
