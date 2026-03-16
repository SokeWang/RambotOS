import React, { useState, useEffect } from 'react';
import { useRambot } from '../../context/RambotContext';
import { Activity, RefreshCw, Mail, MessageCircle, AlertCircle, CheckCircle2, Circle } from 'lucide-react';

export default function HeartbeatPanel() {
    const { backend } = useRambot();
    const [statuses, setStatuses] = useState({});
    const [loading, setLoading] = useState(true);

    const fetchStatuses = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://127.0.0.1:8000/monitor/status');
            if (response.ok) {
                const data = await response.json();
                setStatuses(data);
            }
        } catch (e) {
            console.error("Failed to fetch heartbeat statuses:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatuses();
        // Poll every 10 seconds for updates
        const interval = setInterval(fetchStatuses, 10000);
        return () => clearInterval(interval);
    }, [backend]);

    const handleToggle = async (name, currentRunning) => {
        try {
            const url = `http://127.0.0.1:8000/monitor/toggle/${name}?enable=${!currentRunning}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                // Optimistic UI update
                setStatuses(prev => ({ 
                    ...prev, 
                    [name]: {
                        ...prev[name],
                        status: !currentRunning ? 'running' : 'stopped'
                    }
                }));
                // Real status will update on next poll
            }
        } catch (e) {
            console.error(`Failed to toggle ${name}:`, e);
        }
    };

    const getIcon = (iconName) => {
        const icons = {
            'Mail': <Mail className="w-6 h-6 text-blue-400" />,
            'MessageCircle': <MessageCircle className="w-6 h-6 text-green-400" />,
            'Activity': <Activity className="w-6 h-6 text-orange-400" />
        };
        return icons[iconName] || <Activity className="w-6 h-6 text-white" />;
    };

    return (
        <div className="flex flex-col h-full text-white font-sans overflow-hidden bg-black/20">
            {/* Header */}
            <div className="flex items-center justify-between p-8 border-b border-white/10">
                <div className="flex items-center space-x-4">
                    <div className="p-3 bg-orange-500/20 rounded-2xl">
                        <Activity className="w-8 h-8 text-orange-400 animate-pulse" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight">Core System Vital Signs</h2>
                        <p className="text-[10px] text-white/40 font-mono uppercase tracking-[0.2em] mt-1">Core System Vital Monitoring (Heartbeats)</p>
                    </div>
                </div>
                <button
                    onClick={fetchStatuses}
                    className="p-3 hover:bg-white/10 rounded-full transition-all group"
                    title="Refresh Status"
                >
                    <RefreshCw className={`w-6 h-6 text-white/60 group-hover:text-white ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Monitors Grid */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {Object.keys(statuses).map((name) => {
                        const monitor = statuses[name];
                        // Backend returns objects now, but we check for structure
                        const isRunning = (typeof monitor === 'object') ? monitor.status === 'running' : monitor;

                        // Use metadata from backend or fallbacks
                        const label = monitor.label || name.charAt(0).toUpperCase() + name.slice(1);
                        const sublabel = monitor.sublabel || `${name.toUpperCase()} Service Monitoring`;
                        const icon = getIcon(monitor.icon);
                        const color = monitor.color || 'blue';

                        return (
                            <div
                                key={name}
                                className={`
                                        relative group p-6 rounded-[2.5rem] border transition-all duration-500
                                        ${isRunning
                                        ? 'bg-gradient-to-br from-white/10 to-transparent border-white/20'
                                        : 'bg-black/40 border-white/5 opacity-70'}
                                    `}
                            >
                                <div className="flex justify-between items-start mb-6">
                                    <div className={`p-4 rounded-2xl bg-${color}-500/10`}>
                                        {icon}
                                    </div>
                                    <div className={`
                                            flex items-center space-x-2 px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-widest
                                            ${isRunning ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}
                                        `}>
                                        <div className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                                        <span>{isRunning ? 'Active' : 'Standby'}</span>
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <h3 className="text-lg font-bold text-white/90">{label}</h3>
                                    <p className="text-xs text-white/40 font-mono tracking-wider">{sublabel}</p>
                                </div>

                                <div className="mt-8 flex justify-between items-center">
                                    <div className="flex -space-x-2">
                                        {/* Decorative small orbs */}
                                        <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400/50' : 'bg-white/10'}`} />
                                        <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400/30' : 'bg-white/5'}`} />
                                    </div>

                                    <button
                                        onClick={() => handleToggle(name, isRunning)}
                                        className={`
                                                px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-[0.15em] transition-all
                                                ${isRunning
                                                ? 'bg-red-500/20 hover:bg-red-500/40 text-red-400 border border-red-500/30'
                                                : 'bg-white/10 hover:bg-white/20 text-white/70 border border-white/10'}
                                            `}
                                    >
                                        {isRunning ? 'Deactivate' : 'Activate'}
                                    </button>
                                </div>

                                {/* Glassmorphism highlight */}
                                <div className={`absolute inset-0 rounded-[2.5rem] bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none`} />
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Footer Status */}
            <div className="p-6 bg-white/5 border-t border-white/10 flex justify-between items-center px-10">
                <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(249,115,22,0.6)]" />
                    <span className="text-[10px] font-mono text-white/40 uppercase tracking-[0.2em]">Synchronization Module Active</span>
                </div>
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-[0.2em] flex items-center space-x-4">
                    <span>{Object.values(statuses).filter(v => v).length} Modules Running</span>
                    <span className="opacity-20">|</span>
                    <span>System Frequency: 60Hz</span>
                </div>
            </div>
        </div>
    );
}
