import React from 'react';
import { Waves, Thermometer, Compass, Activity, ShieldCheck } from 'lucide-react';
import { Artifact } from '../../api/types';

interface OceanCardProps {
  artifact: Artifact;
}

export const OceanCard: React.FC<OceanCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const location = data.location || {};
  const obs = data.observations || {};
  const current = data.current || {};
  const tempObj = data.temperature || {};
  const salObj = data.salinity || {};
  const currentsObj = data.currents || {};
  const wavesObj = data.waves || {};

  const sstVal = tempObj.value ?? obs.sst?.value ?? current.sea_surface_temperature;
  const sst = sstVal !== undefined && sstVal !== null ? `${sstVal} °C` : 'Unavailable from Copernicus';

  const salVal = salObj.value ?? obs.salinity?.value;
  const salinity = salVal !== undefined && salVal !== null ? `${salVal} PSU` : 'Unavailable';

  const currentSpeedVal = currentsObj.speed_ms ?? obs.current?.speed ?? current.ocean_current_velocity;
  const currentSpeed = currentSpeedVal !== undefined && currentSpeedVal !== null ? `${currentSpeedVal} m/s` : 'Unavailable';

  const currentDirVal = currentsObj.direction_deg ?? obs.current?.direction;
  const currentDir = currentDirVal !== undefined && currentDirVal !== null ? `${currentDirVal}°` : 'N/A';

  const waveHeightVal = wavesObj.significant_wave_height_m ?? obs.wave?.height ?? current.wave_height;
  const waveHeight = waveHeightVal !== undefined && waveHeightVal !== null ? `${waveHeightVal} m` : 'Unavailable';

  const swellPeriodVal = wavesObj.mean_wave_period_s ?? obs.wave?.period ?? current.swell_wave_period;
  const swellPeriod = swellPeriodVal !== undefined && swellPeriodVal !== null ? `${swellPeriodVal} s` : 'Unavailable';

  return (
    <div className="glass-card rounded-2xl p-5 border border-blue-500/20 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Waves className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">{location.name || 'Offshore Region'}</p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
          Copernicus Physics
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
            <Thermometer className="w-3.5 h-3.5 text-rose-400" /> Sea Temp (SST)
          </div>
          <div className="text-lg font-bold text-slate-100">{sst}</div>
        </div>

        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
            <Activity className="w-3.5 h-3.5 text-cyan-400" /> Ocean Current
          </div>
          <div className="text-lg font-bold text-slate-100">{currentSpeed}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Dir: {currentDir}</div>
        </div>

        <div className="p-3.5 rounded-xl bg-ocean-950/60 border border-slate-800">
          <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
            <Waves className="w-3.5 h-3.5 text-blue-400" /> Significant Waves
          </div>
          <div className="text-lg font-bold text-slate-100">{waveHeight}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Swell Period: {swellPeriod}</div>
        </div>
      </div>

      <div className="flex items-center justify-between p-3 rounded-xl bg-ocean-950/80 border border-slate-800 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Sea Surface Salinity: <strong className="text-slate-100">{salinity}</strong></span>
        </div>
        <span className="text-[10px] text-slate-400">Modelled Reanalysis</span>
      </div>
    </div>
  );
};
