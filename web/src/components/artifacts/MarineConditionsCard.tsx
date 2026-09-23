import React from 'react';
import { Waves, Wind, Compass, Info, Activity } from 'lucide-react';
import { Artifact } from '../../api/types';

interface MarineConditionsCardProps {
  artifact: Artifact;
}

export const MarineConditionsCard: React.FC<MarineConditionsCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const location = data.location || {};
  const curr = data.current || {};

  const waveHeight = curr.wave_height ?? curr.significant_wave_height_m ?? 'N/A';
  const waveDir = curr.wave_direction ?? 'N/A';
  const wavePeriod = curr.wave_period ?? curr.mean_wave_period_s ?? 'N/A';

  const swellHeight = curr.swell_wave_height ?? 'N/A';
  const swellDir = curr.swell_wave_direction ?? 'N/A';
  const swellPeriod = curr.swell_wave_period ?? 'N/A';

  const windWaveHeight = curr.wind_wave_height ?? 'N/A';

  return (
    <div className="glass-card rounded-2xl p-5 border border-cyan-500/20 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Waves className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">{location.name || 'Offshore Location'}</p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-cyan-500/20 text-cyan-300 rounded-full border border-cyan-500/30">
          Open-Meteo Marine
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 my-4">
        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Significant Wave</div>
          <div className="text-xl font-bold text-cyan-300">{waveHeight} <span className="text-xs font-normal text-slate-400">m</span></div>
          <div className="text-[10px] text-slate-400 mt-0.5">Period: {wavePeriod}s</div>
        </div>

        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Swell Waves</div>
          <div className="text-xl font-bold text-blue-300">{swellHeight} <span className="text-xs font-normal text-slate-400">m</span></div>
          <div className="text-[10px] text-slate-400 mt-0.5">Period: {swellPeriod}s</div>
        </div>

        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 mb-1">Wind Waves</div>
          <div className="text-xl font-bold text-teal-300">{windWaveHeight} <span className="text-xs font-normal text-slate-400">m</span></div>
          <div className="text-[10px] text-slate-400 mt-0.5">Dir: {waveDir}°</div>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Wave and swell dynamics are numerical model forecasts from Open-Meteo Marine API.</span>
      </div>
    </div>
  );
};
