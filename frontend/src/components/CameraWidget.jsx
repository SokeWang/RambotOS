
import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function CameraWidget({ stream, active }) {
    const videoRef = useRef(null);

    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    if (!active || !stream) return null;

    return (
        <motion.div
            drag
            dragMomentum={false}
            initial={{ opacity: 0, scale: 0.8, x: 20, y: 20 }}
            animate={{ opacity: 1, scale: 1 }}
            className="fixed bottom-32 right-12 z-50 group pointer-events-auto"
        >
            <div className="relative w-48 h-48 md:w-64 md:h-64 bg-white/10 backdrop-blur-[60px] rounded-[2.5rem] border border-white/20 shadow-[0_30px_80px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden">
                {/* Video Content */}
                <div className="flex-1 overflow-hidden relative">
                    <video
                        ref={videoRef}
                        className="w-full h-full object-cover transform scale-x-[-1]"
                        autoPlay
                        muted
                        playsInline
                    />
                    {/* Live Indicator Overlay */}
                    <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1 bg-black/40 backdrop-blur-md rounded-full border border-white/10">
                        <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
                        <span className="text-[10px] font-bold text-white uppercase tracking-widest opacity-80">VISION ACTIVE</span>
                    </div>
                </div>

                {/* Grab Bar Container */}
                <div className="h-4 flex items-center justify-center p-2 bg-white/5">
                    <div className="h-1 w-12 bg-white/20 rounded-full group-hover:bg-white/40 group-active:bg-white/60 transition-all"></div>
                </div>
            </div>

            {/* Context Tooltip */}
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                <span className="text-[10px] font-bold text-white uppercase tracking-[0.2em]">Neural Feed</span>
            </div>
        </motion.div>
    );
}
