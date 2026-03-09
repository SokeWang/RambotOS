import React from 'react';

/**
 * VisionGaze - Apple VisionOS Style Gaze feedback with Magnetic Effect
 * Follows the smoothly interpolated gaze position with enhanced visual feedback
 */
const VisionGaze = ({ mousePos, isPinching }) => {
    return (
        <div className="pointer-events-none fixed inset-0 z-[100]">
            {/* 1. Spatial Pointer (The "Dot") - Enhanced */}
            <div
                className="absolute transition-transform duration-150 ease-out flex items-center justify-center"
                style={{
                    left: Math.round(mousePos.x),
                    top: Math.round(mousePos.y),
                    transform: `translate(-50%, -50%) scale(${isPinching ? 0.7 : 1})`,
                    willChange: 'transform, left, top'
                }}
            >
                {/* Core dot - perfectly centered based on parent's translate -50% -50% */}
                <div className="w-2.5 h-2.5 bg-white rounded-full shadow-[0_0_15px_white]" />

                {/* Large blur halo - 400px radial gradient */}
                <div
                    className="absolute w-[400px] h-[400px] bg-white/[0.04] rounded-full blur-3xl pointer-events-none"
                    style={{ opacity: isPinching ? 0.3 : 0.6 }}
                />
            </div>

            {/* 2. Secondary Gaze Feedback Layer */}
            <div
                className="absolute rounded-full transition-opacity duration-300 pointer-events-none"
                style={{
                    width: '500px',
                    height: '500px',
                    left: Math.round(mousePos.x),
                    top: Math.round(mousePos.y),
                    transform: 'translate(-50%, -50%)',
                    background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
                    opacity: isPinching ? 0.2 : 0.4
                }}
            />
        </div>
    );
};

export default VisionGaze;
