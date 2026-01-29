
import React from 'react';
import { X, Minus } from 'lucide-react';
import { useUI } from '../context/UIContext';

const WindowControls = () => {
    const { setWindowMode, windowMode } = useUI();

    const handleClose = () => {
        if (window.backendBridge) {
            window.backendBridge.close_app();
        }
    };

    const handleMinimize = () => {
        const nextMode = windowMode === 'full' ? 'mini' : 'full';
        setWindowMode(nextMode);
        if (window.backendBridge) {
            window.backendBridge.set_window_state(nextMode);
        }
    };

    return (
        <div className="flex gap-3 p-4 pointer-events-auto">
            {/* Close Button */}
            <button
                onClick={handleClose}
                className="w-8 h-8 rounded-full bg-red-500/20 hover:bg-red-500/40 border border-red-500/30 flex items-center justify-center transition-all group shadow-lg"
                title="Close Application"
            >
                <X size={14} className="text-red-400 group-hover:scale-110" />
            </button>

            {/* Minimize/Shrink Button */}
            <button
                onClick={handleMinimize}
                className="w-8 h-8 rounded-full bg-orange-500/20 hover:bg-orange-500/40 border border-orange-500/30 flex items-center justify-center transition-all group shadow-lg"
                title="Toggle Mini Mode"
            >
                <Minus size={14} className="text-orange-400 group-hover:scale-110" />
            </button>
        </div>
    );
};

export default WindowControls;
