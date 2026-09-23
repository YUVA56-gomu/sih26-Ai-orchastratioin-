import React from 'react';
import { Artifact } from '../../api/types';
import { WeatherCard } from './WeatherCard';
import { OceanCard } from './OceanCard';
import { PFZMapCard } from './PFZMapCard';
import { RiskSummaryCard } from './RiskSummaryCard';
import { TideCard } from './TideCard';
import { HazardAlertCard } from './HazardAlertCard';
import { GeofenceAlertCard } from './GeofenceAlertCard';
import { RouteMapCard } from './RouteMapCard';
import { Layers, MapPin } from 'lucide-react';

import { MarineConditionsCard } from './MarineConditionsCard';

interface ArtifactRendererProps {
  artifact: Artifact;
  className?: string;
}

export const ArtifactRenderer: React.FC<ArtifactRendererProps> = ({ artifact, className = '' }) => {
  if (!artifact || !artifact.type) {
    return null;
  }

  switch (artifact.type.toLowerCase()) {
    case 'weather_card':
      return <WeatherCard artifact={artifact} />;

    case 'marine_conditions':
      return <MarineConditionsCard artifact={artifact} />;

    case 'ocean_card':
      return <OceanCard artifact={artifact} />;

    case 'pfz_map':
      return <PFZMapCard artifact={artifact} />;

    case 'risk_summary':
      return <RiskSummaryCard artifact={artifact} />;

    case 'tide_card':
      return <TideCard artifact={artifact} />;

    case 'hazard_alert':
    case 'advisory':
      return <HazardAlertCard artifact={artifact} />;

    case 'geofence_alert':
      return <GeofenceAlertCard artifact={artifact} />;

    case 'route_map':
      return <RouteMapCard artifact={artifact} />;

    case 'location_card':
      const locData = artifact.data || {};
      return (
        <div className="glass-card rounded-xl p-4 border border-slate-800 bg-ocean-900/80 max-w-md w-full flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <div className="font-semibold text-slate-100 text-sm">{artifact.title}</div>
            <div className="text-xs text-slate-400">Coordinates: {locData.latitude}°N, {locData.longitude}°E</div>
          </div>
        </div>
      );

    default:
      return (
        <div className="glass-card rounded-xl p-4 border border-slate-800 bg-ocean-900/60 max-w-md w-full">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Artifact: {artifact.title || artifact.type}</span>
          </div>
          <pre className="text-[11px] font-mono p-2 rounded bg-ocean-950 text-slate-300 overflow-x-auto max-h-40 scrollbar-thin">
            {JSON.stringify(artifact.data, null, 2)}
          </pre>
        </div>
      );
  }
};
