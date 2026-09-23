import React from 'react';
import { Waves, ArrowUpRight, ArrowDownRight, Clock, Info } from 'lucide-react';
import { Artifact } from '../../api/types';

interface TideCardProps {
  artifact: Artifact;
}

export const TideCard: React.FC<TideCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const extrema = data.extrema || [];
  const curr = data.current || {};
  const currentLevelVal = curr.sea_level_m ?? data.current_sea_level_m;
  const currentLevel = currentLevelVal !== undefined && currentLevelVal !== null ? `${currentLevelVal} m` : 'Unavailable';

  const phase = curr.phase || data.phase || 'STANDARD';
  const trend = curr.trend || data.trend || 'STATIONARY';

  return (
    <div className="glass-card rounded-2xl p-5 border border-cyan-500/20 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Waves className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">Phase 2.4 Astronomical Harmonic Tide Model</p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-cyan-500/20 text-cyan-300 rounded-full border border-cyan-500/30">
          Tide Dynamics
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 my-4">
        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Sea Level MSL</div>
          <div className="text-xl font-bold text-cyan-300">{currentLevel} <span className="text-xs font-normal text-slate-400">m</span></div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Tidal Phase</div>
          <div className="text-sm font-bold text-slate-100 flex items-center justify-center gap-1">
            {phase === 'FLOODING' ? <ArrowUpRight className="w-4 h-4 text-emerald-400" /> : <ArrowDownRight className="w-4 h-4 text-amber-400" />}
            {phase}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Level Trend</div>
          <div className="text-sm font-bold text-slate-100">{trend}</div>
        </div>
      </div>

      {extrema.length > 0 && (
        <div className="my-3 space-y-1.5">
          <div className="text-xs font-semibold text-slate-300">Upcoming High & Low Tide Extrema:</div>
          <div className="grid grid-cols-2 gap-2">
            {extrema.slice(0, 4).map((ext: any, idx: number) => (
              <div key={idx} className="p-2.5 rounded-lg bg-ocean-950/80 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <div className="font-bold text-slate-200">{ext.type || 'EXTREMA'}</div>
                  <div className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {ext.time ? new Date(ext.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                  </div>
                </div>
                <div className="font-mono font-bold text-cyan-300">{ext.height_m ?? ext.value} m</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Harmonic tide calculations are referenced to Mean Sea Level (MSL) and do not represent chart datum (CD).</span>
      </div>
    </div>
  );
};
