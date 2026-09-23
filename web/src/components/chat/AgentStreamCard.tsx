import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, Loader2, Sparkles, Brain } from 'lucide-react';
import { AgentStepPayload } from '../../api/types';

interface AgentStreamCardProps {
  steps: AgentStepPayload[];
  isComplete: boolean;
}

export const AgentStreamCard: React.FC<AgentStreamCardProps> = ({ steps, isComplete }) => {
  const [isExpanded, setIsExpanded] = useState(!isComplete);
  const [startTime] = useState<number>(Date.now());
  const [duration, setDuration] = useState<number>(0);

  useEffect(() => {
    if (isComplete) {
      setIsExpanded(false);
      setDuration((Date.now() - startTime) / 1000);
    } else {
      const interval = setInterval(() => {
        setDuration((Date.now() - startTime) / 1000);
      }, 200);
      return () => clearInterval(interval);
    }
  }, [isComplete, startTime]);

  if (!steps || steps.length === 0) return null;

  const displaySteps = steps.filter(
    (s) => s.label && s.label !== 'Fast Response Agent'
  );

  if (displaySteps.length === 0) return null;

  // Group steps logically by capability
  const categories: { [key: string]: AgentStepPayload[] } = {
    'Marine Intelligence': [],
    'Ocean Agent': [],
    'Weather Agent': [],
    'Fishery & Marine Life': [],
    'Safety & Geofence': [],
  };

  displaySteps.forEach((step) => {
    const node = (step.node || '').toLowerCase();
    if (node.includes('ocean')) {
      categories['Ocean Agent'].push(step);
    } else if (node.includes('weather')) {
      categories['Weather Agent'].push(step);
    } else if (node.includes('fishery')) {
      categories['Fishery & Marine Life'].push(step);
    } else if (node.includes('safety') || node.includes('risk') || node.includes('geofence') || node.includes('tide') || node.includes('route')) {
      categories['Safety & Geofence'].push(step);
    } else {
      categories['Marine Intelligence'].push(step);
    }
  });

  const activeCategories = Object.keys(categories).filter(
    (cat) => categories[cat].length > 0
  );

  return (
    <div className="my-2 max-w-xl rounded-2xl border border-cyan-500/20 bg-ocean-900/80 backdrop-blur-md overflow-hidden text-xs shadow-md transition-all">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3.5 py-2 flex items-center justify-between bg-ocean-950/60 hover:bg-ocean-850/80 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          {isComplete ? (
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          ) : (
            <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
          )}
          <span className="font-semibold text-slate-200 text-xs">
            {isComplete ? `✦ Analyzed in ${duration.toFixed(1)}s` : `✦ SAMUDRA Analyzing (${duration.toFixed(1)}s)...`}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono">
            {activeCategories.length} agent group{activeCategories.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-400">
          <span className="text-[10px] text-slate-500">{isExpanded ? 'Hide' : 'View execution'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {isExpanded && (
        <div className="p-3 space-y-2 border-t border-slate-800/60 bg-ocean-950/90 max-h-64 overflow-y-auto scrollbar-thin">
          {activeCategories.map((catName) => {
            const catSteps = categories[catName];
            return (
              <div key={catName} className="rounded-xl border border-slate-800/80 bg-ocean-900/40 p-2.5 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-cyan-300 text-[11px] pb-1 border-b border-slate-800/60">
                  <span className="flex items-center gap-1.5">
                    <Brain className="w-3 h-3 text-cyan-400" />
                    {catName}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Completed
                  </span>
                </div>
                <div className="space-y-1 pt-0.5">
                  {catSteps.map((step, idx) => (
                    <div key={idx} className="flex items-center justify-between text-[11px] text-slate-300 pl-2">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="text-xs">{step.icon || '✓'}</span>
                        <span className="font-medium text-slate-200">{step.label}</span>
                        <span className="text-slate-400 truncate hidden sm:inline">— {step.thought || step.message}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

