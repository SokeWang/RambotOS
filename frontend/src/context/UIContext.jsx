import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';

const UIContext = createContext(null);

export const useUI = () => {
    const context = useContext(UIContext);
    if (!context) {
        throw new Error('useUI must be used within a UIProvider');
    }
    return context;
};

export const UIProvider = ({ children }) => {
    // --- UI State ---
    const [showChatbox, setShowChatbox] = useState(false);
    const [showCameraSelector, setShowCameraSelector] = useState(false);
    const [windowMode, setWindowMode] = useState('full'); // 'full' or 'mini'
    const [isSystemReady, setIsSystemReady] = useState(false);
    const [activeApp, setActiveApp] = useState(null);

    // Process/Loading State
    const [processingStep, setProcessingStep] = useState(null);

    // Subtitle State (Visual)
    const [subtitle, setSubtitle] = useState(null);
    const [notification, setNotification] = useState(null);
    const [isSubtitleFading, setIsSubtitleFading] = useState(false);

    // Cursor Control State
    const [cursorMode, setCursorMode] = useState('raw'); // 'raw', 'ema', 'kalman'

    // Camera Background State
    const [showCameraBackground, setShowCameraBackground] = useState(false);

    // Wallpaper State
    const [wallpaper, setWallpaper] = useState(() => {
        return localStorage.getItem('rambot_wallpaper') || null;
    });

    // Persistence
    useEffect(() => {
        if (wallpaper) {
            localStorage.setItem('rambot_wallpaper', wallpaper);
        } else {
            localStorage.removeItem('rambot_wallpaper');
        }
    }, [wallpaper]);

    const value = useMemo(() => ({
        showChatbox, setShowChatbox,
        showCameraSelector, setShowCameraSelector,
        processingStep, setProcessingStep,
        subtitle, setSubtitle,
        isSubtitleFading, setIsSubtitleFading,
        notification, setNotification,
        cursorMode, setCursorMode,
        windowMode, setWindowMode,
        isSystemReady, setIsSystemReady,
        showCameraBackground, setShowCameraBackground,
        wallpaper, setWallpaper,
        activeApp, setActiveApp
    }), [
        showChatbox, showCameraSelector,
        processingStep, subtitle, isSubtitleFading,
        cursorMode, windowMode, isSystemReady,
        showCameraBackground, wallpaper, activeApp
    ]);

    return (
        <UIContext.Provider value={value}>
            {children}
        </UIContext.Provider>
    );
};
