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
    windowScale = 1,
    isDragging,
    startDragging,
    headerActions,
    children
}) => {
    return (
        <div className="absolute inset-0 flex items-start justify-center pt-20 z-50 pointer-events-none">
            {/* Invisible Wrapper for the entire window cluster */}
            <div
                style={{
                    transform: `translate(${windowPos.x}px, ${windowPos.y}px) scale(${windowScale})`,
                    transition: isDragging ? 'none' : 'transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
                }}
                className="pointer-events-none flex flex-col gap-4 w-full max-w-3xl h-full max-h-[500px] animate-in zoom-in-95 fade-in duration-500"
            >
                {/* Detached Floating Header (Pills) */}
                <div className="w-full flex justify-center items-center gap-4 px-4 pointer-events-none z-50 mb-2">
                    {/* Title Pill (Now draggable) */}
                    <div 
                        data-gaze-target="true"
                        onMouseDown={startDragging}
                        className={`pointer-events-auto px-6 py-2 bg-white/10 rounded-full border border-white/20 shadow-xl flex items-center cursor-grab active:cursor-grabbing transition-all
                        ${isDragging ? 'bg-white/30 scale-[1.02]' : 'hover:bg-white/20'}`}
                    >
                        <h2 className="text-[0.95rem] font-medium tracking-wide text-white/90 select-none">{name}</h2>
                    </div>

                    {/* Actions Pill */}
                    <div className="pointer-events-auto flex items-center gap-2 px-1.5 py-1.5 bg-white/10 rounded-full border border-white/20 shadow-xl">
                        {headerActions && <div className="flex items-center gap-2 px-3 border-r border-white/10 mr-1">{headerActions}</div>}
                        <button 
                            onClick={onClose} 
                            className="w-8 h-8 flex items-center justify-center hover:bg-white/20 rounded-full transition-all active:scale-95 group"
                        >
                            <X size={15} className="text-white opacity-70 group-hover:opacity-100 transition-opacity" />
                        </button>
                    </div>
                </div>

                {/* Main Content Card */}
                <div className="window-content-area pointer-events-auto relative w-full flex-1 bg-white/10 rounded-[3.5rem] border border-white/20 shadow-[0_4px_24px_rgba(0,0,0,0.2),0_60px_150px_rgba(0,0,0,0.7)] flex flex-col overflow-hidden">
                    {/* Subtle Dynamic Lighting Overlay */}
                    <div className="absolute inset-0 pointer-events-none rounded-[3.5rem] bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.08)_0%,transparent_60%)] z-50"></div>

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

                </div>
            </div>
        </div>
    );
};

export default VisionWindow;
