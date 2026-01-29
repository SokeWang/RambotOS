import React from 'react';

const LoadingScreen = () => {
    return (
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-black overflow-hidden font-sans">
            {/* Background glowing effect */}
            <div className="absolute inset-0 bg-radial-gradient from-blue-900/10 via-black to-black opacity-60"></div>

            {/* Futuristic Tech Frame */}
            <div className="relative flex flex-col items-center">

                {/* Outer Scanning Ring */}
                <div className="absolute w-64 h-64 border-2 border-cyan-500/20 rounded-full animate-ping"></div>
                <div className="absolute w-64 h-64 border border-cyan-500/10 rounded-full"></div>

                {/* Rotating Hexagons / Rings */}
                <div className="w-48 h-48 border-2 border-t-cyan-400 border-r-transparent border-b-cyan-400 border-l-transparent rounded-full animate-spin-slow"></div>

                {/* Inner Pulsing Orb */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
                    <div className="w-32 h-32 bg-cyan-500/5 rounded-full blur-xl animate-pulse"></div>
                    <div className="w-16 h-16 border-2 border-cyan-400 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(34,211,238,0.4)]">
                        <div className="w-8 h-8 bg-cyan-400 rounded-full animate-pulse-fast"></div>
                    </div>
                </div>
            </div>

            {/* Status Information */}
            <div className="mt-16 text-center z-10">
                <h1 className="text-3xl font-bold tracking-[0.3em] text-white uppercase mb-2 drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
                    RAMBOT
                </h1>
                <div className="flex flex-col items-center gap-2">
                    <div className="h-0.5 w-48 bg-gray-800 relative overflow-hidden rounded-full">
                        <div className="absolute top-0 left-0 h-full bg-cyan-400 animate-shimmer w-1/2"></div>
                    </div>
                    <p className="text-cyan-400 font-mono text-xs tracking-widest uppercase animate-pulse">
                        Synchronizing Neural Link...
                    </p>
                </div>
            </div>

            {/* Decorative Tech Elements */}
            <div className="absolute bottom-12 left-12 font-mono text-[10px] text-cyan-800 uppercase tracking-tighter">
                <p>MK-VI Initialize: [OK]</p>
                <p>Subsystem Check: [OK]</p>
                <p>Neural Index: [LOADING]</p>
            </div>

            <div className="absolute bottom-12 right-12 font-mono text-[10px] text-cyan-800 uppercase tracking-tighter text-right">
                <p>Access Level: Admin</p>
                <p>Location: Classified</p>
                <p>Uptime: 99.9%</p>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes spin-slow {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .animate-spin-slow {
                    animation: spin-slow 8s linear infinite;
                }
                @keyframes pulse-fast {
                    0%, 100% { opacity: 0.6; transform: scale(0.95); }
                    50% { opacity: 1; transform: scale(1.05); }
                }
                .animate-pulse-fast {
                    animation: pulse-fast 1s ease-in-out infinite;
                }
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(200%); }
                }
                .animate-shimmer {
                    animation: shimmer 1.5s infinite;
                }
                .bg-radial-gradient {
                    background: radial-gradient(circle at center, var(--tw-gradient-from), var(--tw-gradient-via), var(--tw-gradient-to));
                }
            `}} />
        </div>
    );
};

export default LoadingScreen;
