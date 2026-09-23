import React, { useEffect, useRef } from 'react';
import { Fish, Sparkles, MapPin, AlertCircle } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Artifact } from '../../api/types';

interface PFZMapCardProps {
  artifact: Artifact;
}

export const PFZMapCard: React.FC<PFZMapCardProps> = ({ artifact }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const { data } = artifact;
  const location = data.location || {};
  const candidates = data.candidates || data.pfz_candidates || [];
  const fronts = data.thermal_fronts || [];

  const centerLat = location.latitude ?? (candidates[0]?.latitude ?? candidates[0]?.lat) ?? 15.0;
  const centerLon = location.longitude ?? (candidates[0]?.longitude ?? candidates[0]?.lon) ?? 73.0;

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const leafletObj = L || (window as any).L;
    if (!leafletObj) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = leafletObj.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([centerLat, centerLon], 8);

    leafletObj.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_2tka_1_84b8380ea0ef34e5e4bac11c', {
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.current = map;

    const bounds = leafletObj.latLngBounds([]);

    // Location center marker
    if (location.latitude && location.longitude) {
      const locMarker = leafletObj.circleMarker([location.latitude, location.longitude], {
        radius: 8,
        fillColor: '#00d2ff',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 0.9,
      }).addTo(map);
      locMarker.bindPopup(`<b>Target Region:</b> ${location.name || 'Center'}`);
      bounds.extend([location.latitude, location.longitude]);
    }

    // PFZ Candidate markers
    candidates.forEach((cand: any, idx: number) => {
      const lat = cand.latitude ?? cand.lat;
      const lon = cand.longitude ?? cand.lon;
      if (lat !== undefined && lon !== undefined) {
        const candMarker = leafletObj.circleMarker([lat, lon], {
          radius: 10,
          fillColor: '#10b981',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 0.9,
        }).addTo(map);

        const scoreText = cand.pfz_score ? `${(cand.pfz_score * 100).toFixed(0)}%` : 'High Likelihood';
        candMarker.bindPopup(`
          <div style="font-family: sans-serif; padding: 2px;">
            <b style="color: #047857;">Candidate PFZ #${idx + 1}</b><br/>
            <span>${cand.name || 'Fishing Zone'}</span><br/>
            <span>Rating: <b>${scoreText}</b></span><br/>
            <small>${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E</small>
          </div>
        `);
        bounds.extend([lat, lon]);
      }
    });

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [25, 25] });
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [centerLat, centerLon, candidates]);

  return (
    <div className="glass-card rounded-2xl p-5 border border-emerald-500/20 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Fish className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">{location.name} • Candidate Zones: {candidates.length}</p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
          INCOIS PFZ
        </span>
      </div>

      {/* Interactive Map Display */}
      <div className="relative w-full h-56 rounded-xl overflow-hidden border border-slate-800 my-4 bg-ocean-950">
        <div ref={mapContainerRef} className="w-full h-full z-10" />
      </div>

      <div className="my-3 space-y-2">
        <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
          <span className="flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-amber-400" /> Pelagic Aggregation Candidates</span>
          <span className="text-[10px] text-emerald-400 font-mono">Status: {data.pfz_status || 'CALCULATED'}</span>
        </div>

        {candidates.length > 0 ? (
          <div className="grid gap-2 max-h-44 overflow-y-auto pr-1">
            {candidates.slice(0, 4).map((cand: any, idx: number) => {
              const lat = cand.latitude ?? cand.lat;
              const lon = cand.longitude ?? cand.lon;
              return (
                <div key={idx} className="p-2.5 rounded-xl bg-ocean-950/80 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 px-2 rounded-lg bg-emerald-950 text-emerald-400 font-bold text-xs">
                      #{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{cand.name || `PFZ Zone ${idx + 1}`}</div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-500" />
                        {lat !== undefined ? `${Number(lat).toFixed(2)}°N` : ''}, {lon !== undefined ? `${Number(lon).toFixed(2)}°E` : ''}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-emerald-400">
                      {cand.pfz_score ? `${(cand.pfz_score * 100).toFixed(0)}%` : 'High Likelihood'}
                    </div>
                    <div className="text-[10px] text-slate-400">Score Rating</div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-3 text-center text-xs text-slate-400 bg-ocean-950/60 rounded-xl border border-slate-800">
            No active PFZ candidates in immediate vicinity
          </div>
        )}
      </div>

      {data.recommendation && (
        <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-300 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
          <span>{data.recommendation}</span>
        </div>
      )}
    </div>
  );
};
