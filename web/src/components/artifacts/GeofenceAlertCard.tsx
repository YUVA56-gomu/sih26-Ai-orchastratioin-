import React from 'react';
import { ShieldCheck, ShieldAlert, MapPin, Info, AlertTriangle } from 'lucide-react';
import { Artifact } from '../../api/types';

interface GeofenceAlertCardProps {
  artifact: Artifact;
}

export const GeofenceAlertCard: React.FC<GeofenceAlertCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const location = data.location || {};
  const inRestricted = data.inside_restricted_zone || false;
  const inEEZ = data.inside_eez ?? true;
  const matchedZones = data.matched_zones || [];
  const verification = data.verification || {};

  return (
    <div className={`glass-card rounded-2xl p-5 border bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full ${inRestricted ? 'border-rose-500/30' : 'border-cyan-500/30'}`}>
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl border ${inRestricted ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'}`}>
            {inRestricted ? <ShieldAlert className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">{location.name} • Deterministic Raycasting Engine</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${inRestricted ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'}`}>
          {inRestricted ? 'RESTRICTED ZONE' : 'SAFE WATERS'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 my-4">
        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">Indian EEZ Status</div>
          <div className="text-sm font-bold text-cyan-300">{inEEZ ? 'INSIDE EEZ' : 'OUTSIDE EEZ'}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Informational GIS Layer</div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">Defense & MPA Layer</div>
          <div className="text-sm font-bold text-amber-400 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> UNAVAILABLE
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Unmapped in open layer</div>
        </div>
      </div>

      {matchedZones.length > 0 && (
        <div className="my-3 space-y-1">
          <div className="text-xs font-semibold text-slate-300">Intersected Boundary Geometry:</div>
          {matchedZones.map((z: any, idx: number) => (
            <div key={idx} className="p-2.5 rounded-lg bg-ocean-950/80 border border-slate-800 text-xs flex items-center justify-between">
              <span className="font-medium text-slate-200">{z.name || z.id}</span>
              <span className="text-[10px] font-mono text-slate-400">{z.category || 'INFORMATIONAL_GIS'}</span>
            </div>
          ))}
        </div>
      )}

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Marine Regions EEZ polygons are research layers. Naval/Defence restriction geometries require official Ministry of Defence clearance.</span>
      </div>
    </div>
  );
};
