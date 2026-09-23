import React from 'react';
import { CloudSun, Wind, Droplets, Gauge, Sun, Compass } from 'lucide-react';
import { Artifact } from '../../api/types';

interface WeatherCardProps {
  artifact: Artifact;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const current = data.current || {};
  const location = data.location || {};
  const units = data.units || {};
  const hourly = data.hourly || {};

  const tempVal = current.temperature_2m;
  const temp = tempVal !== undefined && tempVal !== null ? `${tempVal}` : '--';

  const windVal = current.wind_speed_10m;
  const wind = windVal !== undefined && windVal !== null ? `${windVal}` : '--';

  const gustsVal = current.wind_gusts_10m;
  const gusts = gustsVal !== undefined && gustsVal !== null ? `${gustsVal}` : '--';

  const humidVal = current.relative_humidity_2m;
  const humid = humidVal !== undefined && humidVal !== null ? `${humidVal}` : '--';

  const pressureVal = current.surface_pressure ?? current.pressure_msl;
  const pressure = pressureVal !== undefined && pressureVal !== null ? `${pressureVal}` : '--';

  return (
    <div className="glass-card rounded-2xl p-5 border border-cyan-500/20 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <CloudSun className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">{location.name} • {location.latitude}°N, {location.longitude}°E</p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-cyan-500/20 text-cyan-300 rounded-full border border-cyan-500/30">
          Open-Meteo Weather
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mb-1">
            <Sun className="w-3.5 h-3.5 text-amber-400" /> Temp
          </div>
          <div className="text-xl font-bold text-slate-100">{temp}°C</div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mb-1">
            <Wind className="w-3.5 h-3.5 text-cyan-400" /> Wind
          </div>
          <div className="text-xl font-bold text-slate-100">{wind} <span className="text-xs font-normal text-slate-400">km/h</span></div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mb-1">
            <Droplets className="w-3.5 h-3.5 text-blue-400" /> Humidity
          </div>
          <div className="text-xl font-bold text-slate-100">{humid}%</div>
        </div>

        <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-center">
          <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mb-1">
            <Gauge className="w-3.5 h-3.5 text-teal-400" /> Gusts
          </div>
          <div className="text-xl font-bold text-slate-100">{gusts} <span className="text-xs font-normal text-slate-400">km/h</span></div>
        </div>
      </div>

      {hourly.time && Array.isArray(hourly.time) && hourly.time.length > 0 && (
        <div className="pt-3 border-t border-slate-800">
          <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
            <span>24-Hour Forecast Timeline</span>
            <span className="text-[10px] text-slate-400">Pressure: {pressure} hPa</span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {hourly.time.slice(0, 12).map((t: string, idx: number) => {
              const hourLabel = new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              const hTemp = hourly.temperature_2m ? hourly.temperature_2m[idx] : '-';
              const hWind = hourly.wind_speed_10m ? hourly.wind_speed_10m[idx] : '-';
              return (
                <div key={idx} className="flex-shrink-0 p-2 min-w-[64px] rounded-lg bg-ocean-950/80 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400">{hourLabel}</div>
                  <div className="text-xs font-semibold text-cyan-300 my-0.5">{hTemp}°C</div>
                  <div className="text-[10px] text-slate-400">{hWind} km/h</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
