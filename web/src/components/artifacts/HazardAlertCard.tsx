import React from 'react';
import { AlertOctagon, ShieldAlert, CheckCircle2, Info } from 'lucide-react';
import { Artifact } from '../../api/types';

interface HazardAlertCardProps {
  artifact: Artifact;
}

export const HazardAlertCard: React.FC<HazardAlertCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const status = data.status || 'CLEAR';
  const alerts = data.alerts || [];

  const isWarning = status === 'ACTIVE' || alerts.length > 0;

  return (
    <div className={`glass-card rounded-2xl p-5 border bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full ${isWarning ? 'border-amber-500/30' : 'border-emerald-500/30'}`}>
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl border ${isWarning ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
            {isWarning ? <AlertOctagon className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">INCOIS & IMD Official Hazard Bulletins</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${isWarning ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'}`}>
          {isWarning ? 'ACTIVE ADVISORY' : 'NO WARNINGS'}
        </span>
      </div>

      <div className="my-4 space-y-2">
        {alerts.length > 0 ? (
          alerts.map((al: any, idx: number) => (
            <div key={idx} className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/20 text-xs text-amber-200">
              <div className="font-bold text-amber-300 flex items-center justify-between mb-1">
                <span>{al.hazard_type || al.title || 'Coastal Warning'}</span>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-500/20 text-amber-300 rounded">
                  {al.severity || 'WARNING'}
                </span>
              </div>
              <p className="text-slate-300">{al.description || al.message || 'Active marine hazard advisory in coastal area.'}</p>
            </div>
          ))
        ) : (
          <div className="p-4 rounded-xl bg-ocean-950/80 border border-slate-800 text-center text-xs text-slate-300 flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>No active coastal cyclone, high wave, or swell surge advisories for this location.</span>
          </div>
        )}
      </div>

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Official bulletins are parsed from INCOIS and IMD coastal hazard feeds. Mariners must verify local NAVAREA VIII warnings.</span>
      </div>
    </div>
  );
};
