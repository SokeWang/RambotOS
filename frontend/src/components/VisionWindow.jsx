import React from 'react';
import { ChevronLeft, X, Hand, Activity } from 'lucide-react';

/**
 * VisionWindow - Apple VisionOS Style Spatial Window
 * Supports dragging via a grab bar.
 */
const VisionWindow = ({
    name,
    onClose,
    windowPos,
    isDragging,
    startDragging,
    children
}) => {
    return (
        <div className="absolute inset-0 flex items-center justify-center z-50 pointer-events-none">
            <div
                style={{
                    transform: `translate(${windowPos.x}px, ${windowPos.y}px)`,
                    transition: isDragging ? 'none' : 'transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
                }}
                className="pointer-events-auto w-full max-w-5xl h-full max-h-[720px] bg-white/10 backdrop-blur-[100px] rounded-[3.5rem] 
                border border-white/20 shadow-[0_60px_150px_rgba(0,0,0,0.7)] flex flex-col overflow-hidden animate-in zoom-in-95 fade-in duration-500"
            >
                {/* Window Control Bar */}
                <div className="px-10 py-8 flex items-center justify-between bg-white/5">
                    <div className="flex items-center gap-5">
                        <button onClick={onClose} className="p-3 hover:bg-white/10 rounded-full text-white/50 transition-all">
                            <ChevronLeft size={24} />
                        </button>
                        <h2 className="text-3xl font-bold tracking-tight text-white">{name}</h2>
                    </div>
                    <button onClick={onClose} className="p-3.5 bg-white/10 hover:bg-red-500/20 rounded-full transition-all border border-white/10">
                        <X size={22} className="text-white" />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 relative overflow-hidden">
                    {children || (
                        <div className="p-12 overflow-y-auto w-full h-full">
                            <div className="grid grid-cols-2 gap-10">
                                <div className="p-10 bg-black/30 rounded-[3rem] border border-white/5 flex flex-col items-center justify-center space-y-4">
                                    <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center">
                                        <Hand className="text-cyan-400 animate-pulse" />
                                    </div>
                                    <p className="text-sm font-medium text-white/50 text-center uppercase tracking-widest">Drag the bottom bar to move</p>
                                </div>
                                <div className="p-10 bg-black/30 rounded-[3rem] border border-white/5 flex flex-col items-center justify-center space-y-4">
                                    <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center">
                                        <Activity className="text-blue-400" />
                                    </div>
                                    <p className="text-sm font-medium text-white/50 text-center uppercase tracking-widest">Pinch in the air to zoom view</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Grab Bar */}
                <div
                    data-gaze-target="true"
                    onMouseDown={startDragging}
                    className={`h-1.5 w-44 self-center mb-8 rounded-full cursor-grab active:cursor-grabbing transition-all duration-300
                    ${isDragging ? 'bg-white/70 shadow-[0_0_25px_rgba(255,255,255,0.4)]' : 'bg-white/20 hover:bg-white/40'}`}
                />
            </div>
        </div>
    );
};

export default VisionWindow;
