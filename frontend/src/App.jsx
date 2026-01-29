
import React, { useState, useEffect } from 'react';
import HUD from './components/HUD';
import { GlobalProvider, useGlobal } from './context/GlobalContext';
import { useUI } from './context/UIContext';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="w-screen h-screen bg-red-900 text-white p-10 font-mono">
                    <h1>CRITICAL RENDER ERROR</h1>
                    <pre className="mt-4">{this.state.error?.toString()}</pre>
                </div>
            );
        }
        return this.props.children;
    }
}

const AppContent = () => {
    const {
        showChatbox,
        subtitle,
        isSubtitleFading,
        captureRef,
        canvasRef,
        isSystemReady
    } = useGlobal();

    const { showCameraBackground, wallpaper } = useUI();

    // Prevent programmatic or focus-triggered scrolling
    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY !== 0 || window.scrollX !== 0) {
                window.scrollTo(0, 0);
            }
        };
        window.addEventListener('scroll', handleScroll);
        // Force reset on mount
        window.scrollTo(0, 0);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div className="w-full h-full bg-black overflow-hidden relative">

            {/* Hidden Canvas for capture (Global) */}
            <canvas ref={canvasRef} style={{ width: '640px', height: '480px', display: 'none', position: 'absolute', pointerEvents: 'none' }}></canvas>

            {/* 1. Vision Background (Spatial Video) - Global Background */}
            <div className={`absolute inset-0 z-0 transition-[opacity,transform,filter] duration-700 ease-in-out scale-100 blur-none opacity-100 ${!showCameraBackground ? 'opacity-0 scale-95' : 'opacity-100'}`}>
                <video
                    ref={captureRef}
                    className="w-full h-full object-cover scale-x-[-1]"
                    style={{ filter: 'brightness(0.6) contrast(1.15) saturate(1.1)' }}
                    autoPlay
                    muted
                    playsInline
                />
            </div>

            {/* 1.5 Gradient / Custom Wallpaper Background (Shown when camera is off) */}
            <div className={`absolute inset-0 z-0 transition-[opacity,transform] duration-1000 ease-in-out bg-gradient-to-br from-[#0c0c14] via-[#1a1a2e] to-[#0c0c14] ${showCameraBackground ? 'opacity-0 scale-105' : 'opacity-100 scale-100'}`}>
                {wallpaper ? (
                    <img
                        src={wallpaper}
                        alt="Wallpaper"
                        className="w-full h-full object-cover transition-opacity duration-1000"
                    />
                ) : (
                    <>
                        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_50%,_rgba(34,211,238,0.1),_transparent_70%)] animate-pulse" />
                        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full animate-float-slow" />
                        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full animate-float-slow-reverse" />
                    </>
                )}
            </div>

            {/* 2. Interactive Layer (Full Screen) */}
            <div className="relative z-10 w-full h-full flex flex-col overflow-hidden">
                <HUD />

                {/* Subtitle Overlay (VisionOS style) */}
                {!showChatbox && subtitle && (
                    <div className={`absolute bottom-32 left-0 w-full flex justify-center pointer-events-none z-50 ${isSubtitleFading ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'} transition-[opacity,transform] duration-500`}>
                        <div className="max-w-3xl px-8 py-4 bg-black/40 backdrop-blur-3xl rounded-[2rem] border border-white/10 shadow-2xl">
                            <p className="text-white text-lg md:text-xl font-bold text-center leading-relaxed tracking-wide">
                                {subtitle}
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const RambotApp = () => {
    return (
        <GlobalProvider>
            <ErrorBoundary>
                <AppContent />
            </ErrorBoundary>
        </GlobalProvider>
    );
};

export default RambotApp;
