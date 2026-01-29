
import React from 'react';
import { Activity, MessageSquare, Database, Shield, BarChart2, Search, LayoutGrid, Mic, Settings } from 'lucide-react';
import { LauncherApps } from '../config/LauncherConfig';
import { useRambot } from '../context/RambotContext';
import { useUI } from '../context/UIContext';

const iconMap = {
    'activity': Activity,
    'message-square': MessageSquare,
    'database': Database,
    'shield': Shield,
    'bar-chart-2': BarChart2
};

export default function Dock({ triggerSystemAction }) {
    const { isListening, toggleListening } = useRambot();
    const { setShowChatbox, showChatbox } = useUI();

    return (
        <div className="flex justify-center w-full mb-8 pointer-events-auto">
            {/* Dock Container with Siri Glow */}
            <div className="relative">
                {/* Apple Intelligence Rainbow Glow (Active when listening) */}
                {isListening && (
                    <>
                        {/* 1. Remote Ambient Glow (Lush, soft background) */}
                        <div className="absolute inset-[-20px] blur-3xl opacity-30 rounded-[5rem] animate-siri-fluid bg-gradient-to-r from-[#5ac8fa] via-[#5856d6] via-[#af52bf] via-[#ff2d55] via-[#ff9500] to-[#5ac8fa] bg-[length:400%_400%]" />

                        {/* 2. The "Outer Ring" (Sharp flowing edge via masking) */}
                        <div
                            className="absolute inset-[-3px] p-[3px] rounded-[3.8rem] animate-siri-fluid bg-gradient-to-r from-[#5ac8fa] via-[#5856d6] via-[#af52bf] via-[#ff2d55] via-[#ff9500] to-[#5ac8fa] bg-[length:400%_400%]"
                            style={{
                                WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                                WebkitMaskComposite: 'xor',
                                maskComposite: 'exclude',
                            }}
                        />
                    </>
                )}

                {/* Dock Nav */}
                <nav className="relative flex items-center gap-3 p-3 bg-white/10 backdrop-blur-[60px] rounded-[3.5rem] border border-white/20 shadow-[0_30px_100px_rgba(0,0,0,0.5)]">

                    {/* Search / Global Actions */}
                    <button className="p-4 hover:bg-white/10 rounded-full transition-all group">
                        <Search size={22} className="text-white/30 group-hover:text-white transition-all" />
                    </button>

                    <div className="w-[1px] h-10 bg-white/10 mx-1" />

                    {/* App Grid Switcher */}
                    <button className="p-4 hover:bg-white/10 rounded-full transition-all group">
                        <LayoutGrid size={22} className="text-white/40 group-hover:text-white" />
                    </button>

                    {/* Main Launcher Apps */}
                    <div className="flex items-center gap-2">
                        {LauncherApps.slice(0, 3).map((item, idx) => {
                            const IconComponent = iconMap[item.icon];
                            return (
                                <button
                                    key={idx}
                                    data-gaze-target="true"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        triggerSystemAction(item.action);
                                    }}
                                    className="p-4 hover:bg-white/10 rounded-full transition-all group relative"
                                    title={item.name}
                                >
                                    {IconComponent && <IconComponent size={22} className="text-white/40 group-hover:text-white transition-all" />}
                                    <span className="absolute -top-12 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-md text-white text-[10px] px-3 py-1.5 rounded-full border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none uppercase tracking-widest font-bold">
                                        {item.name}
                                    </span>
                                </button>
                            );
                        })}
                    </div>

                    {/* AI / Voice Button (The Centerpiece) */}
                    <button
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            toggleListening();
                        }}
                        className={`mx-2 p-5 rounded-full transition-all duration-500 relative overflow-hidden group
                        ${isListening ? 'bg-white/20 shadow-[0_0_30px_rgba(255,255,255,0.3)] scale-110' : 'hover:bg-white/10'}`}
                    >
                        {isListening && (
                            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/40 via-purple-500/40 to-cyan-400/40 animate-pulse" />
                        )}
                        <div className="relative z-10 flex items-center justify-center">
                            {isListening ? (
                                <div className="flex items-center gap-1.5 h-6">
                                    {[...Array(3)].map((_, i) => (
                                        <div
                                            key={i}
                                            className="w-1.5 bg-white rounded-full animate-bounce shadow-[0_0_10px_white]"
                                            style={{
                                                height: `${70 + Math.random() * 30}%`,
                                                animationDuration: `${0.4 + i * 0.1}s`,
                                                animationDelay: `${i * 0.1}s`
                                            }}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <Mic size={24} className="text-white/40 group-hover:text-white transition-all" />
                            )}
                        </div>
                    </button>

                    <div className="w-[1px] h-10 bg-white/10 mx-1" />

                    {/* Chat Toggle */}
                    <button
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowChatbox(!showChatbox);
                        }}
                        className={`p-4 rounded-full transition-all group ${showChatbox ? 'bg-white/20' : 'hover:bg-white/10'}`}>
                        <MessageSquare size={22} className={`${showChatbox ? 'text-white' : 'text-white/40 group-hover:text-white'} transition-all`} />
                    </button>

                    {/* Settings */}
                    <button
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            triggerSystemAction('Settings');
                        }}
                        className="p-4 hover:bg-white/10 rounded-full transition-all group"
                    >
                        <Settings size={22} className="text-white/30 group-hover:text-white transition-all" />
                    </button>
                </nav>
            </div>
        </div>
    );
}
