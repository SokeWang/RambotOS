
import React, { useState, useEffect } from 'react';
import { Mic, Video, X, Check, Minimize2, Wifi, Battery } from 'lucide-react';
import { useUI } from '../../context/UIContext';
import { useRambot } from '../../context/RambotContext';

export default function HeaderPanel() {
    const {
        showCameraSelector, setShowCameraSelector,
        showCameraBackground, setShowCameraBackground
    } = useUI();

    const {
        isListening, toggleListening,
        availableCameras, selectedCameraId, setSelectedCameraId,
        toggleWindowMode,
        developMode, toggleDevelopMode
    } = useRambot();

    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const timeString = time.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit' });

    return (
        <div className="flex justify-between items-center w-full px-4 pointer-events-auto">
            {/* Left Section: Time & Logo */}
            <div className="flex items-center gap-4">
                <div className="bg-white/10 backdrop-blur-[40px] px-6 py-2.5 rounded-full border border-white/20 shadow-2xl flex items-center gap-4">
                    <span className="text-sm font-bold tracking-tight text-white">{timeString}</span>
                    <div className="w-[1px] h-4 bg-white/20"></div>
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isListening ? 'bg-green-400 animate-pulse' : 'bg-cyan-400'}`}></div>
                        <h1 className="text-xs font-black tracking-widest text-white/80">RAMBOT</h1>
                    </div>
                </div>
            </div>

            {/* Center Section: CPU/System Status (Optional, kept small) */}
            <div className="hidden md:flex items-center bg-white/5 backdrop-blur-[20px] px-4 py-1.5 rounded-full border border-white/10 opacity-50">
                <p className="text-[10px] text-white/60 font-mono tracking-tighter uppercase">Neural Engine Active • 58.2 TFLOPS</p>
            </div>

            {/* Right Section: Controls & Status */}
            <div className="flex items-center gap-4">
                {/* System Status Pill */}
                <div className="bg-white/10 backdrop-blur-[40px] px-5 py-2.5 rounded-full border border-white/20 shadow-2xl flex items-center gap-4">
                    <Wifi size={14} className="text-white/60" />
                    <Battery size={14} className="text-white/40" />
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-400 to-blue-600 border border-white/40 shadow-inner" />
                </div>
            </div>
        </div>
    );
}

function CursorControlPanel() {
    const { cursorMode, setCursorMode } = useUI();
    const modes = [
        { id: 'raw', label: 'R' },
        { id: 'ema', label: 'E' },
        { id: 'kalman', label: 'K' }
    ];

    return (
        <div className="bg-white/10 backdrop-blur-[40px] p-1 flex items-center rounded-full border border-white/20 shadow-2xl">
            {modes.map(mode => (
                <button
                    key={mode.id}
                    onClick={() => setCursorMode(mode.id)}
                    className={`px-3 py-1.5 rounded-full text-[10px] font-black transition-all ${cursorMode === mode.id
                        ? 'bg-white/20 text-white shadow-lg'
                        : 'text-white/40 hover:text-white/80'
                        }`}
                >
                    {mode.label}
                </button>
            ))}
        </div>
    );
}
