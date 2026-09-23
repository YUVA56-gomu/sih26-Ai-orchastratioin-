import React from 'react';
import { Logo } from '../brand/Logo';
import { CloudSun, Waves, Fish, Navigation, ShieldCheck, Compass, Anchor, MapPin } from 'lucide-react';

interface WelcomeScreenProps {
  onQuickAction: (query: string) => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onQuickAction }) => {
  const examplePrompts = [
    {
      icon: <Waves className="w-5 h-5 text-cyan-400" />,
      title: 'Ocean Conditions',
      query: "What's the sea condition near me?",
      badge: 'Copernicus Marine',
    },
    {
      icon: <Fish className="w-5 h-5 text-emerald-400" />,
      title: 'Fishing Zones',
      query: 'Find potential fishing zones near Visakhapatnam.',
      badge: 'INCOIS PFZ',
    },
    {
      icon: <Navigation className="w-5 h-5 text-amber-400" />,
      title: 'Navigation & Travel',
      query: 'Can I travel to Chennai tomorrow?',
      badge: 'A* Route Engine',
    },
    {
      icon: <CloudSun className="w-5 h-5 text-blue-400" />,
      title: 'Weather & Waves',
      query: 'Show the weather and waves for tomorrow morning.',
      badge: 'Open-Meteo & ECMWF',
    },
  ];

  const capabilities = [
    { label: 'Weather', icon: <CloudSun className="w-3.5 h-3.5 text-cyan-400" /> },
    { label: 'Ocean Conditions', icon: <Waves className="w-3.5 h-3.5 text-blue-400" /> },
    { label: 'Fishing Zones', icon: <Fish className="w-3.5 h-3.5 text-emerald-400" /> },
    { label: 'Marine Safety', icon: <ShieldCheck className="w-3.5 h-3.5 text-rose-400" /> },
    { label: 'Navigation', icon: <Navigation className="w-3.5 h-3.5 text-amber-400" /> },
    { label: 'Marine Data', icon: <Anchor className="w-3.5 h-3.5 text-purple-400" /> },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto my-auto animate-fade-in">
      <div className="mb-6 relative">
        <div className="absolute inset-0 bg-cyan-500/20 blur-3xl rounded-full -z-10" />
        <Logo variant="blue" size="xl" showText={false} className="mx-auto" />
      </div>

      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
        SAMUDRA <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">AI</span>
      </h1>
      <p className="text-base sm:text-lg font-medium text-slate-300 max-w-xl mb-4">
        Marine intelligence through conversation.
      </p>

      {/* Capabilities Pills */}
      <div className="flex flex-wrap justify-center gap-2 max-w-xl mb-8">
        {capabilities.map((cap, i) => (
          <span
            key={i}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-ocean-900/90 border border-slate-800 text-xs text-slate-300 shadow-sm"
          >
            {cap.icon}
            <span>{cap.label}</span>
          </span>
        ))}
      </div>

      {/* Example Prompt Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl mb-8 text-left">
        {examplePrompts.map((act, idx) => (
          <button
            key={idx}
            onClick={() => onQuickAction(act.query)}
            className="glass-card p-4 rounded-2xl border border-slate-800 hover:border-cyan-500/40 hover:bg-ocean-850/80 transition-all text-left flex flex-col justify-between group shadow-lg"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="p-2.5 rounded-xl bg-ocean-950 border border-slate-800 group-hover:border-cyan-500/30 transition-colors">
                {act.icon}
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-ocean-950 text-slate-400 border border-slate-800">
                {act.badge}
              </span>
            </div>
            <div>
              <div className="font-semibold text-slate-200 text-sm group-hover:text-cyan-300 transition-colors">
                {act.title}
              </div>
              <p className="text-xs text-slate-400 line-clamp-2 mt-1 font-mono">{act.query}</p>
            </div>
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-400 glass-card px-4 py-2 rounded-full border border-slate-800">
        <ShieldCheck className="w-4 h-4 text-cyan-400" />
        <span>One conversation. One AI brain. Many capabilities.</span>
      </div>
    </div>
  );
};

