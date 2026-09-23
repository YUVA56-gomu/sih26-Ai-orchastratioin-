import React, { useEffect, useRef } from 'react';
import { Navigation, MapPin, ShieldAlert, ShieldCheck, Compass, Info } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Artifact } from '../../api/types';

interface RouteMapCardProps {
  artifact: Artifact;
}

export const RouteMapCard: React.FC<RouteMapCardProps> = ({ artifact }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const { data } = artifact;
  const origin = data.origin || {};
  const dest = data.destination || {};
  const distKm = data.distance_km ?? 0;
  const cost = data.estimated_cost ?? 0;
  const status = data.status || 'OK';
  const geojson = data.geojson || data.route_geometry;
  const waypoints = data.waypoints || [];
  const verification = data.verification || {};

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const leafletObj = L || (window as any).L;
    if (!leafletObj) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const startLat = origin.latitude ?? 15.0;
    const startLon = origin.longitude ?? 73.0;

    const map = leafletObj.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([startLat, startLon], 6);

    leafletObj.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_2tka_1_84b8380ea0ef34e5e4bac11c', {
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.current = map;

    const bounds = L.latLngBounds([]);

    // Render GeoJSON LineString
    if (geojson && geojson.geometry && geojson.geometry.coordinates) {
      const coords = geojson.geometry.coordinates; // [ [lon, lat], ... ]
      const latLngs = coords.map((c: [number, number]) => [c[1], c[0]]);

      const polyline = L.polyline(latLngs, {
        color: '#00d2ff',
        weight: 4,
        opacity: 0.9,
        dashArray: '8, 8',
      }).addTo(map);

      latLngs.forEach((ll: [number, number]) => bounds.extend(ll));
    }

    // Render Origin Marker
    if (origin.latitude && origin.longitude) {
      const oMarker = L.circleMarker([origin.latitude, origin.longitude], {
        radius: 7,
        fillColor: '#10b981',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 1,
      }).addTo(map);
      oMarker.bindPopup(`<b>Origin:</b> ${origin.name || 'Start'}`);
      bounds.extend([origin.latitude, origin.longitude]);
    }

    // Render Destination Marker
    if (dest.latitude && dest.longitude) {
      const dMarker = L.circleMarker([dest.latitude, dest.longitude], {
        radius: 7,
        fillColor: '#ef4444',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 1,
      }).addTo(map);
      dMarker.bindPopup(`<b>Destination:</b> ${dest.name || 'End'}`);
      bounds.extend([dest.latitude, dest.longitude]);
    }

    // Fit Map Bounds
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [30, 30] });
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [geojson, origin, dest]);

  return (
    <div className="glass-card rounded-2xl p-5 border border-cyan-500/30 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-2xl max-w-2xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Navigation className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">
              {origin.name || 'Origin'} ➔ {dest.name || 'Destination'}
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-bold rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30 font-mono">
          A* OPTIMIZED
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 my-4">
        <div className="p-3 rounded-xl bg-ocean-950/70 border border-slate-800 text-center">
          <div className="text-[11px] text-slate-400">Total Distance</div>
          <div className="text-lg font-bold text-cyan-300 font-mono">{distKm.toFixed(1)} <span className="text-xs font-normal text-slate-400">km</span></div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/70 border border-slate-800 text-center">
          <div className="text-[11px] text-slate-400">Cost Score</div>
          <div className="text-lg font-bold text-slate-100 font-mono">{cost.toFixed(1)}</div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/70 border border-slate-800 text-center">
          <div className="text-[11px] text-slate-400">Waypoints</div>
          <div className="text-lg font-bold text-slate-100 font-mono">{waypoints.length || 2}</div>
        </div>
      </div>

      {/* Leaflet Map Display */}
      <div className="relative w-full h-64 rounded-xl overflow-hidden border border-slate-800 my-4 bg-ocean-950">
        <div ref={mapContainerRef} className="w-full h-full z-10" />
      </div>

      {/* Verification status chips */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-xs my-3">
        <div className="flex items-center gap-3">
          <span className="text-slate-400 font-medium">Layer Verification:</span>
          <span className="px-2 py-0.5 text-[10px] font-mono bg-cyan-950 text-cyan-300 rounded border border-cyan-800">EEZ: {verification.eez || 'INFORMATIONAL'}</span>
          <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-950 text-amber-300 rounded border border-amber-800">MPA: {verification.mpa || 'UNAVAILABLE'}</span>
          <span className="px-2 py-0.5 text-[10px] font-mono bg-rose-950 text-rose-300 rounded border border-rose-800">Naval: {verification.naval || 'UNAVAILABLE'}</span>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Calculated route is an AI decision-support suggestion. NOT an official nautical chart or legal maritime clearance.</span>
      </div>
    </div>
  );
};
