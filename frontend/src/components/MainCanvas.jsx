import React from 'react';
import { useUI } from '../context/UIContext';
import { MessageSquare, Calendar, Database, Activity, Shield, BarChart2 } from 'lucide-react';

export default function MainCanvas() {
    const { setShowChatbox, setActiveApp } = useUI();

    const apps = [
        { id: 'chat', name: 'Chatbox', icon: <MessageSquare size={36} />, color: 'from-blue-400 to-blue-600', action: () => setShowChatbox(true) },
        { id: 'calendar', name: 'Timeline', icon: <Calendar size={36} />, color: 'from-purple-400 to-purple-600' },
        { id: 'data', name: 'Knowledge', icon: <Database size={36} />, color: 'from-cyan-400 to-cyan-600', action: () => setActiveApp({ name: 'Knowledge', id: 'Knowledge' }) },
        { id: 'skills', name: 'Skills', icon: <Activity size={36} />, color: 'from-orange-400 to-orange-600', action: () => { console.log("Opening Skills..."); setActiveApp({ name: 'Skills', id: 'Skills' }); } },
        { id: 'security', name: 'Heartbeat', icon: <Activity size={36} />, color: 'from-red-400 to-red-600', action: () => setActiveApp({ name: 'Heartbeat', id: 'security' }) },
        { id: 'charts', name: 'Analytics', icon: <BarChart2 size={36} />, color: 'from-green-400 to-green-600' },
    ];

    return (
        <div className="relative w-full h-full flex flex-col justify-center items-center pointer-events-none">

            {/* 1. App Grid (VisionOS style) */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-20 gap-y-16 animate-in fade-in zoom-in duration-1000">
                {apps.map((app) => (
                    <button
                        key={app.id}
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            if (app.action) app.action();
                        }}
                        className="group flex flex-col items-center gap-6 transition-all duration-300 hover:scale-110 pointer-events-auto"
                    >
                        <div className={`
                                w-24 h-24 md:w-28 md:h-28 rounded-[2.8rem] bg-gradient-to-br ${app.color} 
                                relative overflow-hidden transition-all duration-300 opacity-80 group-hover:opacity-100
                                shadow-[0_20px_40px_rgba(0,0,0,0.4),_inset_0_-4px_8px_rgba(0,0,0,0.3),_inset_0_4px_8px_rgba(255,255,255,0.4)]
                                border-t border-white/30
                            `}>
                            <div className="absolute inset-0 bg-white/30 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <div className="relative z-10 w-full h-full flex items-center justify-center text-white drop-shadow-2xl transition-transform">
                                {app.icon}
                            </div>
                        </div>
                        <span className="text-xs font-bold text-white/60 group-hover:text-white tracking-widest uppercase transition-all drop-shadow-md">
                            {app.name}
                        </span>
                    </button>
                ))}
            </div>

        </div>
    );
}
