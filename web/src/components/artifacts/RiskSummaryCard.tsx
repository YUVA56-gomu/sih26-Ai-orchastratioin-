import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { Artifact } from '../../api/types';

interface RiskSummaryCardProps {
  artifact: Artifact;
}

export const RiskSummaryCard: React.FC<RiskSummaryCardProps> = ({ artifact }) => {
  const { data } = artifact;
  const riskLevel = (data.risk_level || 'UNKNOWN').toUpperCase();
  const riskScore = data.risk_score ?? -1;
  const reasons = data.reasons || [];
  const params = data.evaluated_parameters || {};

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return { bg: 'bg-emerald-500/20', text: 'text-emerald-300', border: 'border-emerald-500/30', bar: 'bg-emerald-500' };
      case 'MODERATE':
        return { bg: 'bg-amber-500/20', text: 'text-amber-300', border: 'border-amber-500/30', bar: 'bg-amber-500' };
      case 'HIGH':
      case 'VERY HIGH':
        return { bg: 'bg-rose-500/20', text: 'text-rose-300', border: 'border-rose-500/30', bar: 'bg-rose-500' };
      default:
        return { bg: 'bg-slate-500/20', text: 'text-slate-300', border: 'border-slate-500/30', bar: 'bg-slate-500' };
    }
  };

  const style = getRiskColor(riskLevel);

  return (
    <div className="glass-card rounded-2xl p-5 border border-slate-700 bg-gradient-to-br from-ocean-900/90 via-ocean-850/80 to-ocean-900/90 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl ${style.bg} ${style.text} border ${style.border}`}>
            {riskLevel === 'LOW' ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{artifact.title}</h3>
            <p className="text-xs text-slate-400">Deterministic Marine Risk Assessment</p>
          </div>
        </div>
        <span className={`px-3 py-1 text-xs font-bold rounded-full border ${style.bg} ${style.text} ${style.border}`}>
          {riskLevel} RISK
        </span>
      </div>

      <div className="my-4 p-4 rounded-xl bg-ocean-950/80 border border-slate-800">
        <div className="flex items-center justify-between mb-2 text-xs">
          <span className="text-slate-300 font-semibold">Risk Index Score</span>
          <span className="font-mono font-bold text-slate-100 text-sm">{riskScore >= 0 ? `${riskScore} / 100` : 'N/A'}</span>
        </div>
        <div className="w-full h-3 bg-ocean-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${style.bar}`}
            style={{ width: `${Math.max(5, Math.min(100, riskScore))}%` }}
          />
        </div>
      </div>

      {reasons.length > 0 && (
        <div className="mb-4 space-y-1.5">
          <div className="text-xs font-semibold text-slate-300">Identified Risk Factors:</div>
          <div className="space-y-1">
            {reasons.map((r: string, idx: number) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-300 p-2 rounded-lg bg-ocean-950/60 border border-slate-800/60">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                <span>{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-3 rounded-xl bg-ocean-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>Algorithmic risk score is a decision-support heuristic and does not replace official Coast Guard or NHO advisories.</span>
      </div>
    </div>
  );
};
