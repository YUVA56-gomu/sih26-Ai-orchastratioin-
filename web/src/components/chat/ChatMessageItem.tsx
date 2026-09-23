import React from 'react';
import { Logo } from '../brand/Logo';
import { User, ShieldCheck, MapPin, Sparkles } from 'lucide-react';
import { Artifact, AgentStepPayload } from '../../api/types';
import { ArtifactRenderer } from '../artifacts/ArtifactRenderer';
import { AgentStreamCard } from './AgentStreamCard';
import { EvidencePanel } from '../evidence/EvidencePanel';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  agentSteps?: AgentStepPayload[];
  artifacts?: Artifact[];
  isStreaming?: boolean;
  evidence?: any[];
  evidenceSummary?: any;
  riskLevel?: string;
  riskScore?: number;
}

interface ChatMessageItemProps {
  message: ChatMessage;
  onQuickAction?: (query: string) => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, onQuickAction }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-3 my-4 px-2">
        <div className="max-w-2xl rounded-2xl px-4 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg text-sm leading-relaxed">
          {message.content}
        </div>
        <div className="p-2 rounded-xl bg-cyan-950 border border-cyan-500/30 text-cyan-300 flex-shrink-0">
          <User className="w-5 h-5" />
        </div>
      </div>
    );
  }

  // Derive target location for follow-up query context
  const locName = message.artifacts?.find((a) => a.data?.location?.name || a.data?.name)?.data?.location?.name ||
                  message.artifacts?.find((a) => a.data?.name)?.data?.name || 'Visakhapatnam';

  const textLower = (message.content || '').toLowerCase();
  const hasPFZ = message.artifacts?.some((a) => a.type === 'pfz_map') || textLower.includes('fish') || textLower.includes('pfz');
  const hasWeather = message.artifacts?.some((a) => a.type === 'weather_card') || textLower.includes('weather') || textLower.includes('wind');
  const hasRoute = message.artifacts?.some((a) => a.type === 'route_map') || textLower.includes('route') || textLower.includes('path');

  let followUpChips = [];
  if (hasPFZ) {
    followUpChips = [
      { label: '⚓ Check Safety Risk', query: `Is it safe to go to that fishing zone tomorrow?` },
      { label: '🗺 Show Navigation Route', query: `Show route to the nearest fishing zone` },
      { label: '📊 Detailed Ocean Data', query: `Show SST and current velocity at that spot` },
    ];
  } else if (hasWeather) {
    followUpChips = [
      { label: '🌊 Check Wave Heights', query: `What are the wave heights and swell forecast near ${locName}?` },
      { label: '📅 Compare Tomorrow', query: `What about the weather tomorrow near ${locName}?` },
      { label: '🐟 Check Fishing Potential', query: `Are there potential fishing zones near ${locName}?` },
    ];
  } else if (hasRoute) {
    followUpChips = [
      { label: '🌤 Weather Along Route', query: `Check weather forecast along this route` },
      { label: '🛡 Check Restricted Areas', query: `Are there any marine exclusion zones on this route?` },
      { label: '🛟 Safety Assessment', query: `Evaluate overall risk score for this voyage` },
    ];
  } else {
    followUpChips = [
      { label: '🌤 Weather Forecast', query: `What is the weather forecast near ${locName}?` },
      { label: '🌊 Ocean Hydrodynamics', query: `What are the SST, current speed, and salinity near ${locName}?` },
      { label: '🐟 Fishing Zones (PFZ)', query: `Show potential fishing zones near ${locName}` },
      { label: '⚓ Safety Risk Check', query: `Evaluate marine safety risk level near ${locName}` },
    ];
  }

  // Extract evidence records
  const evidenceRecords = message.evidence || message.artifacts?.flatMap((a) =>
    Array.isArray(a.data?.provenance) ? a.data.provenance : a.data?.provenance ? [a.data.provenance] : []
  ) || [];

  return (
    <div className="flex items-start gap-3 my-6 px-2">
      <div className="flex-shrink-0 mt-1">
        <Logo variant="blue" size="sm" showText={false} />
      </div>

      <div className="flex-1 min-w-0 space-y-4">
        {/* Agent Thinking Stream Card if available */}
        {message.agentSteps && message.agentSteps.length > 0 && (
          <AgentStreamCard steps={message.agentSteps} isComplete={!message.isStreaming} />
        )}

        {/* Main Response Content */}
        {message.content && (
          <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed glass-card rounded-2xl p-5 border border-slate-800 bg-ocean-900/40">
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        )}

        {/* Render Artifacts if present */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="space-y-4 pt-2">
            {message.artifacts.map((art) => (
              <ArtifactRenderer key={art.id || Math.random().toString()} artifact={art} />
            ))}
          </div>
        )}

        {/* Scientific Evidence Panel if present */}
        {evidenceRecords.length > 0 && (
          <EvidencePanel evidence={evidenceRecords} summary={message.evidenceSummary} />
        )}

        {/* Contextual Follow-up Chips */}
        {!message.isStreaming && onQuickAction && (
          <div className="pt-2">
            <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Suggested Follow-ups:
            </div>
            <div className="flex flex-wrap gap-2">
              {followUpChips.slice(0, 4).map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => onQuickAction(chip.query)}
                  className="px-3 py-1.5 rounded-xl bg-ocean-900/80 hover:bg-ocean-850 text-cyan-300 border border-cyan-500/20 hover:border-cyan-500/40 text-xs font-medium transition-all shadow-sm flex items-center gap-1"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
