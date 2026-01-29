
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Dock from './Dock';
import MainCanvas from './MainCanvas';
import ChatPanel from './ChatPanel';
import HeaderPanel from './HUD/HeaderPanel';
// import CameraWidget from './CameraWidget';
import GestureController from './GestureController';
import VisionGaze from './VisionGaze';
import VisionWindow from './VisionWindow';
import SettingsPanel from './HUD/SettingsPanel';
import { Cpu } from 'lucide-react';
import { useUI } from '../context/UIContext';
import { useRambot } from '../context/RambotContext';

export default function HUD() {
    // UI State
    const {
        showChatbox,
        setShowChatbox,
        processingStep,
    } = useUI();

    // Rambot Logic State
    const {
        triggerSystemAction,
        processCommand,
        chatHistory,
        attachment,
        triggerSelectFile,
        setAttachment,
        stream,
        cameraActive,
        backend
    } = useRambot();

    // VisionOS Interactive State
    const [mousePos, setMousePos] = useState({ x: -500, y: -500 });
    const [gazePos, setGazePos] = useState({ x: -500, y: -500 }); // Smooth interpolated gaze position
    const [isPinching, setIsPinching] = useState(false);
    const [windowPos, setWindowPos] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [activeApp, setActiveApp] = useState(null);
    const [showDock, setShowDock] = useState(false);
    const revealTimeoutRef = useRef(null);

    const dragOffset = useRef({ x: 0, y: 0 });
    const containerRef = useRef(null);
    const requestRef = useRef();
    const snappedTarget = useRef(null); // Ref to track the currently snapped element
    const isScrollingRef = useRef(false);
    const scrollStateRef = useRef({ startY: 0, startScrollTop: 0, ratio: 1 });

    // Smooth lerp animation for gaze tracking
    const animateGaze = useCallback(() => {
        setGazePos(prev => {
            const lerpFactor = 0.25; // Smoothness factor (0-1)
            const dx = mousePos.x - prev.x;
            const dy = mousePos.y - prev.y;
            // Stop animation when close enough
            if (Math.abs(dx) < 0.1 && Math.abs(dy) < 0.1) return mousePos;
            return {
                x: prev.x + dx * lerpFactor,
                y: prev.y + dy * lerpFactor
            };
        });
        requestRef.current = requestAnimationFrame(animateGaze);
    }, [mousePos]);

    useEffect(() => {
        requestRef.current = requestAnimationFrame(animateGaze);
        return () => cancelAnimationFrame(requestRef.current);
    }, [animateGaze]);

    // Centralized Pointer Logic (Handles both Mouse and Gesture)
    const updatePointerPosition = useCallback((clientX, clientY) => {
        // Dynamic threshold for hysteresis (sticky snap)
        // Entry: 80px, Exit (already snapped): 140px
        const entryThreshold = 80;
        const exitThreshold = 140;
        const isAlreadySnapped = !!snappedTarget.current;
        let currentThreshold = isAlreadySnapped ? exitThreshold : entryThreshold;

        // 1. Target Magnetic detection (Global Selector)
        const targets = document.querySelectorAll('button:not([data-gaze-ignore="true"]), a:not([data-gaze-ignore="true"]), input:not([data-gaze-ignore="true"]), [role="button"]:not([data-gaze-ignore="true"]), [data-gaze-target="true"]');
        let closest = null;
        let closestEl = null;
        let minDistance = currentThreshold;

        targets.forEach(el => {
            const rect = el.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const dist = Math.sqrt(Math.pow(clientX - centerX, 2) + Math.pow(clientY - centerY, 2));

            // Priority: if we are already snapped to THIS element, we give it bias (hysteresis)
            const isExactMatch = snappedTarget.current === el;
            const thresholdAdjustment = isExactMatch ? exitThreshold : entryThreshold;

            if (dist < thresholdAdjustment && dist < minDistance) {
                minDistance = dist;
                closest = { x: centerX, y: centerY };
                closestEl = el;
            }
        });

        // 2. Scrollbar Magnetic detection
        const scrollables = document.querySelectorAll('.overflow-y-auto, .overflow-y-scroll, .custom-scrollbar');
        let snappedToScrollbar = false;

        scrollables.forEach(el => {
            if (el.scrollHeight > el.clientHeight) {
                const rect = el.getBoundingClientRect();

                // Hysteresis for scrollbars too
                const entryZone = 20; // Tighter entry
                const exitZone = 60; // Harder escape
                const isCurrentScrollbar = snappedTarget.current === el && snappedTarget.currentIsScrollbar;
                const activeZone = isCurrentScrollbar ? exitZone : entryZone;

                const isInVerticalZone = clientY >= rect.top && clientY <= rect.bottom;
                const isNearRightEdge = clientX >= rect.right - activeZone && clientX <= rect.right + 10;

                if (isInVerticalZone && isNearRightEdge) {
                    const scrollbarCenterX = rect.right - 6; // Snap to the track
                    const dist = Math.abs(clientX - scrollbarCenterX);

                    if (dist < activeZone && dist < minDistance) {
                        minDistance = dist;
                        closest = { x: scrollbarCenterX, y: clientY }; // Snap X, but follow Y for scrolling
                        closestEl = el;
                        snappedToScrollbar = true;
                    }
                }
            }
        });

        // Store the snapped element and whether it's a scrollbar
        snappedTarget.current = closestEl;
        snappedTarget.currentIsScrollbar = snappedToScrollbar;

        // Use magnetic position if target found, otherwise raw position
        const finalPos = closest ? closest : { x: clientX, y: clientY };
        setMousePos(finalPos);

        if (isDragging) {
            setWindowPos({
                x: clientX - dragOffset.current.x,
                y: clientY - dragOffset.current.y
            });
        }

        // Handle active scrolling
        if (isScrollingRef.current && snappedTarget.current) {
            const dy = clientY - scrollStateRef.current.startY;
            const scrollFactor = snappedTarget.current.scrollHeight / snappedTarget.current.clientHeight;
            snappedTarget.current.scrollTop = scrollStateRef.current.startScrollTop + (dy * scrollFactor);
        }
    }, [isDragging]);

    // Handle updates from GestureController
    const onGestureUpdate = useCallback(({ x, y, isPinching: gesturePinching }) => {
        updatePointerPosition(x, y);

        // Handle "Pinch to Scroll" or "Pinch to Click" logic
        if (gesturePinching && !isPinching) {
            if (snappedTarget.currentIsScrollbar && snappedTarget.current) {
                isScrollingRef.current = true;
                scrollStateRef.current = {
                    startY: y,
                    startScrollTop: snappedTarget.current.scrollTop
                };
            } else if (snappedTarget.current) {
                snappedTarget.current.click();
            }
        } else if (!gesturePinching && isPinching) {
            isScrollingRef.current = false;
        }

        setIsPinching(gesturePinching);
    }, [isPinching, updatePointerPosition]);

    useEffect(() => {
        const handleGlobalMove = (e) => {
            updatePointerPosition(e.clientX, e.clientY);
        };

        const handleGlobalDown = (e) => {
            setIsPinching(true);

            if (snappedTarget.currentIsScrollbar && snappedTarget.current) {
                // Initiate scrollbar drag
                isScrollingRef.current = true;
                scrollStateRef.current = {
                    startY: e.clientY,
                    startScrollTop: snappedTarget.current.scrollTop
                };
            } else if (snappedTarget.current && !snappedTarget.current.contains(e.target)) {
                snappedTarget.current.click();
            }
        };

        const handleGlobalUp = () => {
            setIsPinching(false);
            setIsDragging(false);
            isScrollingRef.current = false;
        };

        window.addEventListener('mousemove', handleGlobalMove);
        window.addEventListener('mousedown', handleGlobalDown);
        window.addEventListener('mouseup', handleGlobalUp);

        return () => {
            window.removeEventListener('mousemove', handleGlobalMove);
            window.removeEventListener('mousedown', handleGlobalDown);
            window.removeEventListener('mouseup', handleGlobalUp);
        };
    }, [updatePointerPosition]);

    // Sync showChatbox with activeApp for spatial window integration
    useEffect(() => {
        if (showChatbox) {
            setActiveApp({ name: 'Chatbox', id: 'Chatbox' });
        } else if (activeApp?.id === 'Chatbox') {
            setActiveApp(null);
            setWindowPos({ x: 0, y: 0 });
        }
    }, [showChatbox]);

    const startDragging = (e) => {
        e.stopPropagation();
        setIsDragging(true);
        dragOffset.current = {
            x: e.clientX - windowPos.x,
            y: e.clientY - windowPos.y
        };
    };

    const handleDockHover = () => {
        if (revealTimeoutRef.current) clearTimeout(revealTimeoutRef.current);
        revealTimeoutRef.current = setTimeout(() => {
            setShowDock(true);
        }, 200); // Reduced delay for better responsiveness
    };

    const handleDockLeave = (force = false) => {
        if (revealTimeoutRef.current) clearTimeout(revealTimeoutRef.current);
        if (force) {
            setShowDock(false);
        } else {
            // Add a small grace period before hiding
            revealTimeoutRef.current = setTimeout(() => {
                setShowDock(false);
            }, 300);
        }
    };

    return (
        <div
            ref={containerRef}
            className="relative w-full h-full overflow-hidden text-white select-none transition-[opacity,brightness,transform] duration-300 ease-out bg-transparent cursor-none"
        >
            {/* 1. Vision Gaze Overlay */}
            <VisionGaze mousePos={gazePos} isPinching={isPinching} />

            {/* 3. Main Interface Layers */}
            <div
                className="relative z-20 w-full h-full transition-[opacity,transform] duration-500 overflow-hidden"
                onClick={(e) => {
                    if (showChatbox) setShowChatbox(false);
                }}
            >
                {/* Header Layer */}
                <header className="absolute top-0 left-0 w-full z-50 pt-8 px-10 pointer-events-none">
                    <div className="pointer-events-auto">
                        <HeaderPanel />
                    </div>
                </header>

                {/* Central Content Section */}
                <main className="relative w-full h-full flex items-center justify-center overflow-hidden z-20">
                    {/* Main Canvas / Grid */}
                    <div className={`w-full h-full transition-[opacity,transform,filter] duration-700 ${activeApp ? 'scale-90 opacity-0 blur-md pointer-events-none' : 'scale-100 opacity-100'}`}>
                        <MainCanvas />
                    </div>

                    {/* Spatial Windows */}
                    {activeApp && (
                        <VisionWindow
                            name={activeApp.id === 'Settings' ? '系统设置' : (activeApp.id === 'Chatbox' ? '神经网络通讯' : activeApp.name)}
                            onClose={() => {
                                setActiveApp(null);
                                setWindowPos({ x: 0, y: 0 });
                                if (activeApp.id === 'Chatbox') setShowChatbox(false);
                            }}
                            windowPos={windowPos}
                            isDragging={isDragging}
                            startDragging={startDragging}
                        >
                            <div className="w-full h-full" onClick={(e) => e.stopPropagation()}>
                                {activeApp.id === 'Chatbox' ? (
                                    <ChatPanel
                                        chatHistory={chatHistory}
                                        processCommand={processCommand}
                                        attachment={attachment}
                                        triggerSelectFile={triggerSelectFile}
                                        clearAttachment={() => setAttachment(null)}
                                    />
                                ) : activeApp.id === 'Settings' ? (
                                    <SettingsPanel />
                                ) : (
                                    <div className="p-12 overflow-y-auto w-full h-full">
                                        <div className="grid grid-cols-2 gap-10">
                                            <div className="p-10 bg-black/30 rounded-[3rem] border border-white/5 flex flex-col items-center justify-center space-y-4">
                                                <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center">
                                                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                                                </div>
                                                <p className="text-sm font-medium text-white/50 text-center uppercase tracking-widest">{activeApp.name} 模块加载中</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </VisionWindow>
                    )}

                    {/* Processing State Overlay */}
                    {processingStep && (
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 text-center pointer-events-none z-[60]">
                            <div className="glass-panel p-6 border border-cyan-500/50 flex flex-col items-center animate-pulse rounded-[2rem]">
                                <Cpu className="w-10 h-10 text-cyan-400 mb-3 animate-spin-slow" />
                                <p className="text-xs text-cyan-200 uppercase tracking-widest font-bold">{processingStep}</p>
                            </div>
                        </div>
                    )}
                </main>

                {/* Footer Layer */}
                <footer
                    className={`absolute bottom-0 left-0 w-full z-40 pb-10 px-10 pointer-events-none flex justify-center transition-all duration-500 ease-out ${showDock ? 'translate-y-0 opacity-100' : 'translate-y-24 opacity-0 scale-95'}`}
                    onMouseEnter={handleDockHover}
                    onMouseLeave={() => handleDockLeave()}
                >
                    <div className="pointer-events-auto">
                        <Dock triggerSystemAction={(action) => {
                            if (action === 'TOGGLE_CHAT') {
                                setShowChatbox(!showChatbox);
                            } else {
                                setActiveApp({ name: action, id: action });
                            }
                            triggerSystemAction(action);
                        }} />
                    </div>
                </footer>

                {/* Dock Reveal Trigger Zone (Increased height for reliability) */}
                <div
                    className="absolute bottom-0 left-0 w-full h-16 z-30"
                    onMouseEnter={handleDockHover}
                    onMouseLeave={() => handleDockLeave()}
                />
            </div>

            {/* Floating Camera View (Moveable) - REMOVED per user request */}
            {/* <CameraWidget
                stream={stream}
                active={cameraActive}
            /> */}

            {/* Gesture Controller (Hand Tracking) */}
            {cameraActive && stream && backend && (
                <GestureController
                    videoStream={stream}
                    backendBridge={backend}
                    onUpdate={onGestureUpdate}
                />
            )}

            {/* Bottom Glow Effect */}
            <div className="pointer-events-none absolute inset-0 z-10 shadow-[inset_0_0_150px_rgba(0,0,0,0.5)] bg-gradient-to-b from-black/10 via-transparent to-black/20" />
        </div>
    );
}
