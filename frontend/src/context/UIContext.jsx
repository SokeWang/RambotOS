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
    const [genUISchema, setGenUISchema] = useState(null);
    const [showAppLauncher, setShowAppLauncher] = useState(false);

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

    // GenUI Mode State
    const [genUIEnabled, setGenUIEnabled] = useState(() => {
        return localStorage.getItem('rambot_genui_enabled') !== 'false'; // Default to true if not set
    });

    // Persistence
    useEffect(() => {
        if (wallpaper) {
            localStorage.setItem('rambot_wallpaper', wallpaper);
        } else {
            localStorage.removeItem('rambot_wallpaper');
        }
    }, [wallpaper]);

    useEffect(() => {
        localStorage.setItem('rambot_genui_enabled', genUIEnabled);
    }, [genUIEnabled]);

    // Listen for GenUI events from BackendBridge
    useEffect(() => {
        const handleGenUI = (e) => {
            const rawSchema = e.detail;
            if (rawSchema) {
                try {
                    console.log("GenUI: handleGenUI received rawSchema type:", typeof rawSchema);
                    let parsedSchema = rawSchema;
                    if (typeof rawSchema === 'string') {
                        try {
                            parsedSchema = JSON.parse(rawSchema);
                            console.log("GenUI: String successfully parsed into object");
                        } catch (pErr) {
                            console.error("GenUI: String received but not valid JSON", rawSchema);
                            return;
                        }
                    }
                    
                    if (parsedSchema && typeof parsedSchema === 'object') {
                        if (!genUIEnabled) {
                            console.log("GenUI: Received schema but GenUI Mode is DISABLED. Ignoring.");
                            return;
                        }

                        console.log("GenUI: Setting schema object:", parsedSchema);
                        setGenUISchema(parsedSchema);
                        
                        // Close chatbox first to avoid race conditions with HUD useEffect
                        setShowChatbox(false);
                        
                        // Set active app to GenUI
                        setActiveApp({ name: 'GenUI', id: 'genui' });
                    } else {
                        console.warn("GenUI: Parsed schema is not an object", parsedSchema);
                    }
                } catch (err) {
                    console.error("GenUI: Error in handleGenUI", err);
                }
            }
        };
        window.addEventListener('GenUIReceived', handleGenUI);
        return () => window.removeEventListener('GenUIReceived', handleGenUI);
    }, []);

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
        activeApp, setActiveApp,
        genUISchema, setGenUISchema,
        showAppLauncher, setShowAppLauncher,
        genUIEnabled, setGenUIEnabled
    }), [
        showChatbox, showCameraSelector,
        processingStep, subtitle, isSubtitleFading,
        cursorMode, windowMode, isSystemReady,
        showCameraBackground, wallpaper, activeApp,
        genUISchema, showAppLauncher, genUIEnabled
    ]);

    return (
        <UIContext.Provider value={value}>
            {children}
        </UIContext.Provider>
    );
};
