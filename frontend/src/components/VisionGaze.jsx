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
                className="absolute transition-transform duration-150 ease-out"
                style={{
                    left: mousePos.x,
                    top: mousePos.y,
                    transform: `translate(-50%, -50%) scale(${isPinching ? 0.7 : 1})`
                }}
            >
                {/* Core dot */}
                <div className="w-2.5 h-2.5 bg-white rounded-full shadow-[0_0_15px_white]" />

                {/* Large blur halo - 400px radial gradient */}
                <div
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-white/[0.04] rounded-full blur-3xl"
                    style={{ opacity: isPinching ? 0.3 : 0.6 }}
                />
            </div>

            {/* 2. Secondary Gaze Feedback Layer */}
            <div
                className="absolute w-[500px] h-[500px] rounded-full transition-opacity duration-300"
                style={{
                    left: mousePos.x - 250,
                    top: mousePos.y - 250,
                    background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
                    opacity: isPinching ? 0.2 : 0.4
                }}
            />
        </div>
    );
};

export default VisionGaze;
