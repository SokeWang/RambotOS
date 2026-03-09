
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Dock from './Dock';
import MainCanvas from './MainCanvas';
import ChatPanel from './ChatPanel';
import HeaderPanel from './HUD/HeaderPanel';
import GestureController from './GestureController';
import VisionGaze from './VisionGaze';
import VisionWindow from './VisionWindow';
import SettingsPanel from './HUD/SettingsPanel';
import SkillsPanel from './HUD/SkillsPanel';
import KnowledgePanel from './HUD/KnowledgePanel';
import HeartbeatPanel from './HUD/HeartbeatPanel';
import GenUIPanel from './HUD/GenUIPanel';
import { Cpu, X, Activity, LayoutGrid, Network, RefreshCw } from 'lucide-react';
import { useUI } from '../context/UIContext';
import { useRambot } from '../context/RambotContext';

export default function HUD() {
    // UI State
    const {
        showChatbox,
        setShowChatbox,
        processingStep,
        activeApp,
        setActiveApp,
        notification,
        setNotification,
        showAppLauncher
    } = useUI();

    // Knowledge View Mode State (Shared with KnowledgePanel)
    const [knowledgeViewMode, setKnowledgeViewMode] = useState('list');
    const [knowledgeRefreshNonce, setKnowledgeRefreshNonce] = useState(0);

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
    const mousePosRef = useRef({ x: -500, y: -500 }); // Ref avoids state-driven RAF restarts
    const [gazePos, setGazePos] = useState({ x: -500, y: -500 });
    const [isPinching, setIsPinching] = useState(false);
    const [windowPos, setWindowPos] = useState({ x: 0, y: 0 });
    const [windowScale, setWindowScale] = useState(1);
    const [isDragging, setIsDragging] = useState(false);

    const dragOffset = useRef({ x: 0, y: 0 });
    const containerRef = useRef(null);
    const requestRef = useRef();
    const snappedTarget = useRef(null);
    const isScrollingRef = useRef(false);
    const scrollStateRef = useRef({ startY: 0, startScrollTop: 0, ratio: 1 });
    const lastZoomDistanceRef = useRef(null);
    const activeRawSurfaceRef = useRef(null);

    // Cached DOM target lists — invalidated only on DOM structure changes
    const cachedTargetsRef = useRef(null);
    const cachedScrollablesRef = useRef(null);

    // Invalidate cache when DOM structure changes (not on every attribute/style update)
    useEffect(() => {
        const observer = new MutationObserver(() => {
            cachedTargetsRef.current = null;
            cachedScrollablesRef.current = null;
        });
        observer.observe(document.body, { childList: true, subtree: true });
        return () => observer.disconnect();
    }, []);

    // Smooth lerp animation for gaze tracking — reads ref, never recreated
    const animateGaze = useCallback(() => {
        setGazePos(prev => {
            const target = mousePosRef.current;
            const lerpFactor = 0.25;
            const dx = target.x - prev.x;
            const dy = target.y - prev.y;
            if (Math.abs(dx) < 0.1 && Math.abs(dy) < 0.1) return target;
            return {
                x: prev.x + dx * lerpFactor,
                y: prev.y + dy * lerpFactor
            };
        });
        requestRef.current = requestAnimationFrame(animateGaze);
    }, []); // No deps — reads ref directly, never rebuilt

    useEffect(() => {
        requestRef.current = requestAnimationFrame(animateGaze);
        return () => cancelAnimationFrame(requestRef.current);
    }, [animateGaze]); // animateGaze is now stable (no deps)

    const updatePointerPosition = useCallback((clientX, clientY) => {
        // Significantly increased exit radius for stronger lock, keeping original entry
        const entryThreshold = 80; // Restored original
        const exitThreshold = 220; // Kept high for strong lock (Was 140)
        const isAlreadySnapped = !!snappedTarget.current;
        let currentThreshold = isAlreadySnapped ? exitThreshold : entryThreshold;

        // Use cached target lists (built once, invalidated by MutationObserver)
        const targets = cachedTargetsRef.current ||
            (cachedTargetsRef.current = document.querySelectorAll(
                'button:not([data-gaze-ignore="true"]), a:not([data-gaze-ignore="true"]), input:not([data-gaze-ignore="true"]), [role="button"]:not([data-gaze-ignore="true"]), [data-gaze-target="true"]'
            ));
        const scrollables = cachedScrollablesRef.current ||
            (cachedScrollablesRef.current = document.querySelectorAll(
                '.overflow-y-auto, .overflow-y-scroll, .custom-scrollbar'
            ));

        let closest = null;
        let closestEl = null;
        let minDistance = currentThreshold;

        targets.forEach(el => {
            const style = window.getComputedStyle(el);
            if (style.pointerEvents === 'none' || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;
            if (el.closest('.pointer-events-none') && !el.closest('.pointer-events-auto')) return;
            if (el.closest('.opacity-0') || el.closest('[style*="opacity: 0"]')) return;

            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const dist = Math.sqrt(Math.pow(clientX - centerX, 2) + Math.pow(clientY - centerY, 2));

            const isExactMatch = snappedTarget.current === el;
            const thresholdAdjustment = isExactMatch ? exitThreshold : entryThreshold;

            if (dist < thresholdAdjustment && dist < minDistance) {
                minDistance = dist;
                closest = { x: centerX, y: centerY };
                closestEl = el;
            }
        });

        let snappedToScrollbar = false;
        scrollables.forEach(el => {
            if (el.scrollHeight > el.clientHeight) {
                const rect = el.getBoundingClientRect();
                const entryZone = 20; // Restored original
                const exitZone = 80; // Harder to accidentally slip off scrollbar (Was 60)
                const isCurrentScrollbar = snappedTarget.current === el && snappedTarget.currentIsScrollbar;
                const activeZone = isCurrentScrollbar ? exitZone : entryZone;

                const isInVerticalZone = clientY >= rect.top && clientY <= rect.bottom;
                const isNearRightEdge = clientX >= rect.right - activeZone && clientX <= rect.right + 10;

                if (isInVerticalZone && isNearRightEdge) {
                    const scrollbarCenterX = rect.right - 6;
                    const dist = Math.abs(clientX - scrollbarCenterX);
                    if (dist < activeZone && dist < minDistance) {
                        minDistance = dist;
                        closest = { x: scrollbarCenterX, y: clientY };
                        closestEl = el;
                        snappedToScrollbar = true;
                    }
                }
            }
        });

        const prevTarget = snappedTarget.current;
        if (prevTarget !== closestEl) {
            // Revert styles for previously snapped target (if not scrollbar)
            if (prevTarget && !prevTarget.currentIsScrollbar) {
                prevTarget.style.transform = '';
                prevTarget.style.filter = '';
                prevTarget.style.boxShadow = '';
            }
            // Apply styles to newly snapped target
            if (closestEl && !snappedToScrollbar) {
                closestEl.style.transition = 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)';
                closestEl.style.transform = 'scale(1.05)';
                closestEl.style.filter = 'brightness(1.2)';
                closestEl.style.boxShadow = '0 0 20px rgba(255,255,255,0.2)';
            }
        }

        snappedTarget.current = closestEl;
        if (closestEl) {
            snappedTarget.currentIsScrollbar = snappedToScrollbar;
        } else {
            snappedTarget.currentIsScrollbar = false;
        }

        const finalPos = closest ? closest : { x: clientX, y: clientY };
        mousePosRef.current = finalPos; // Update ref directly, no state re-render

        if (isDragging) {
            setWindowPos({
                x: clientX - dragOffset.current.x,
                y: clientY - dragOffset.current.y
            });
        }

        if (isScrollingRef.current && snappedTarget.current) {
            const dy = clientY - scrollStateRef.current.startY;
            const scrollFactor = snappedTarget.current.scrollHeight / snappedTarget.current.clientHeight;
            snappedTarget.current.scrollTop = scrollStateRef.current.startScrollTop + (dy * scrollFactor);
        }
    }, [isDragging]);

    // Handle updates from GestureController
    const onGestureUpdate = useCallback(({ hands, x, y, isPinching: gesturePinching }) => {
        updatePointerPosition(x, y);

        // Always dispatch synthetic mousemove so native canvas/D3 listeners can follow the hand pointer
        const moveEvt = new MouseEvent('mousemove', {
            view: window, bubbles: true, cancelable: true,
            clientX: x, clientY: y,
        });
        document.dispatchEvent(moveEvt);

        const elUnderCursor = document.elementFromPoint(x, y);
        const isContentArea = elUnderCursor ? elUnderCursor.closest('.window-content-area') : false;

        // Zoom Logic: If two hands are detected and both are pinching
        if (hands && hands.length >= 2) {
            const h1 = hands[0];
            const h2 = hands[1];

            if (h1.isPinching && h2.isPinching) {
                const currentDist = Math.sqrt(
                    Math.pow(h1.x - h2.x, 2) + Math.pow(h1.y - h2.y, 2)
                );

                if (lastZoomDistanceRef.current !== null) {
                    const delta = currentDist - lastZoomDistanceRef.current;
                    
                    if (isContentArea && elUnderCursor) {
                        // Internal zoom: Dispatch mouse wheel event to scale graph/content
                        if (Math.abs(delta) > 1) {
                            const wheelEvt = new WheelEvent('wheel', {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y,
                                deltaY: -delta * 2 // Translate pinch delta to wheel scroll
                            });
                            elUnderCursor.dispatchEvent(wheelEvt);
                        }
                    } else {
                        // Global zoom: scale the entire spatial window
                        const sensitivity = 0.002;
                        setWindowScale(prev => Math.max(0.3, Math.min(3, prev + delta * sensitivity)));
                    }
                }
                lastZoomDistanceRef.current = currentDist;
                return; // Suppress normal pinching when zooming
            }
        }

        // Reset zoom tracking if not both hands are pinching
        lastZoomDistanceRef.current = null;

        // Handle "Pinch to Scroll", "Pinch to Pan", or "Pinch to Click" logic
        if (gesturePinching && !isPinching) {
            if (snappedTarget.currentIsScrollbar && snappedTarget.current) {
                isScrollingRef.current = true;
                scrollStateRef.current = {
                    startY: y,
                    startScrollTop: snappedTarget.current.scrollTop
                };
            } else if (snappedTarget.current) {
                // Dispatch native mousedown for dragging compatibility
                const mousedownEvt = new MouseEvent('mousedown', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: mousePosRef.current.x, clientY: mousePosRef.current.y
                });
                snappedTarget.current.dispatchEvent(mousedownEvt);
                snappedTarget.current.click();
            } else if (isContentArea && elUnderCursor) {
                // Dispatch native mousedown for pan/drag operations within the content
                const mousedownEvt = new MouseEvent('mousedown', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: x, clientY: y
                });
                elUnderCursor.dispatchEvent(mousedownEvt);
                activeRawSurfaceRef.current = elUnderCursor;
            }
        } else if (!gesturePinching && isPinching) {
            isScrollingRef.current = false;
            
            if (snappedTarget.current && !snappedTarget.currentIsScrollbar) {
                const mouseupEvt = new MouseEvent('mouseup', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: mousePosRef.current.x, clientY: mousePosRef.current.y
                });
                snappedTarget.current.dispatchEvent(mouseupEvt);
            }
            
            // Release arbitrary internal dragging targets (e.g. D3 canvas pan)
            if (activeRawSurfaceRef.current) {
                const mouseupEvt = new MouseEvent('mouseup', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: x, clientY: y
                });
                activeRawSurfaceRef.current.dispatchEvent(mouseupEvt);
                activeRawSurfaceRef.current = null;
            }
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
                // Dispatch synthetic mousedown on the snapped target
                const evt = new MouseEvent('mousedown', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: mousePosRef.current.x, clientY: mousePosRef.current.y
                });
                snappedTarget.current.dispatchEvent(evt);
                // Trigger click behavior
                snappedTarget.current.click();
            }
        };

        const handleGlobalUp = () => {
            setIsPinching(false);
            setIsDragging(false);
            isScrollingRef.current = false;
            if (snappedTarget.current && !snappedTarget.currentIsScrollbar) {
                const upEvt = new MouseEvent('mouseup', {
                    view: window, bubbles: true, cancelable: true,
                    clientX: mousePosRef.current.x, clientY: mousePosRef.current.y
                });
                snappedTarget.current.dispatchEvent(upEvt);
            }
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
        // Only trigger if Chatbox is involved to avoid overwriting other apps like GenUI
        if (showChatbox) {
            if (activeApp?.id !== 'Chatbox') {
                setActiveApp({ name: 'Chatbox', id: 'Chatbox' });
            }
        } else {
            // If chatbox just closed, ONLY clear if Chatbox was indeed the active app
            // We use a functional check if possible or just check current value
            if (activeApp?.id === 'Chatbox') {
                setActiveApp(null);
                setWindowPos({ x: 0, y: 0 });
                setWindowScale(1);
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [showChatbox]); // activeApp intentionally omitted to keep logic unidirectional from showChatbox

    const startDragging = (e) => {
        e.stopPropagation();
        setIsDragging(true);
        dragOffset.current = {
            x: e.clientX - windowPos.x,
            y: e.clientY - windowPos.y
        };
    };


    return (
        <div
            ref={containerRef}
            className="relative w-full h-full overflow-hidden text-white select-none transition-[opacity,brightness,transform] duration-300 ease-out bg-transparent cursor-none"
        >
            {/* 1. Vision Gaze Overlay */}
            <VisionGaze mousePos={gazePos} isPinching={isPinching} />

            {/* 2. System Notifications (Top Right) */}
            <div className="absolute top-10 right-10 z-[100] flex flex-col items-end space-y-4 pointer-events-none">
                {notification && (
                    <div className="animate-in fade-in slide-in-from-right-10 duration-500 ease-out pointer-events-auto">
                        <div className="relative group overflow-hidden">
                            {/* Ambient glow */}
                            <div className="absolute inset-0 bg-blue-500/20 blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />

                            <div className="relative flex items-center space-x-6 px-8 py-5 bg-black/40 rounded-[2.5rem] border border-white/20 shadow-2xl min-w-[320px] max-w-md">
                                <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg">
                                    <Activity className="w-6 h-6 text-white animate-pulse" />
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] font-mono text-blue-400 uppercase tracking-[0.2em] font-bold">System Pulse</span>
                                        <button
                                            onClick={() => setNotification(null)}
                                            className="text-white/20 hover:text-white transition-colors"
                                        >
                                            <X size={14} />
                                        </button>
                                    </div>
                                    <p className="text-white text-sm font-medium leading-relaxed">
                                        {notification}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* 3. Main Interface Layers */}
            <div
                className="relative z-20 w-full h-full transition-[opacity,transform] duration-500 overflow-hidden"
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
                    <div className={`w-full h-full transition-[opacity,transform,filter] duration-700 
                        ${(activeApp || !showAppLauncher) ? 'scale-90 opacity-0 blur-md pointer-events-none' : 'scale-100 opacity-100'}`}>
                        <MainCanvas />
                    </div>

                    {/* Spatial Windows */}
                    {activeApp && (
                        <VisionWindow
                            name={activeApp.id === 'Settings' ? 'System Settings' : (activeApp.id === 'Chatbox' ? 'Neural Communication' : activeApp.name)}
                            onClose={() => {
                                setActiveApp(null);
                                setWindowPos({ x: 0, y: 0 });
                                setWindowScale(1);
                                if (activeApp.id === 'Chatbox') setShowChatbox(false);
                            }}
                            windowPos={windowPos}
                            windowScale={windowScale}
                            isDragging={isDragging}
                            startDragging={startDragging}
                            headerActions={activeApp.id === 'Knowledge' ? (
                                <div className="flex items-center gap-2">
                                    <div className="flex bg-white/5 rounded-lg p-0.5 items-center border border-white/10">
                                        <button
                                            onClick={() => setKnowledgeViewMode('list')}
                                            className={`p-1 rounded-md transition-all ${knowledgeViewMode === 'list' ? 'bg-purple-500/20 text-purple-400' : 'text-white/30 hover:text-white/60'}`}
                                            title="List View"
                                        >
                                            <LayoutGrid className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            onClick={() => setKnowledgeViewMode('graph')}
                                            className={`p-1 rounded-md transition-all ${knowledgeViewMode === 'graph' ? 'bg-purple-500/20 text-purple-400' : 'text-white/30 hover:text-white/60'}`}
                                            title="Graph View"
                                        >
                                            <Network className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                    <button
                                        onClick={() => setKnowledgeRefreshNonce(n => n + 1)}
                                        className="p-1.5 hover:bg-white/10 rounded-full transition-colors group"
                                        title="Refresh"
                                    >
                                        <RefreshCw className="w-4 h-4 text-white/40 group-hover:text-white" />
                                    </button>
                                </div>
                            ) : null}
                        >
                            <div className="w-full h-full" onClick={(e) => e.stopPropagation()}>
                                {activeApp.id === 'Chatbox' ? (
                                    <ChatPanel
                                        chatHistory={chatHistory}
                                    />
                                ) : activeApp.id === 'Settings' ? (
                                    <SettingsPanel />
                                ) : activeApp?.id?.toLowerCase() === 'skills' ? (
                                    <SkillsPanel />
                                ) : activeApp?.id === 'Knowledge' ? (
                                    <KnowledgePanel 
                                        viewMode={knowledgeViewMode} 
                                        refreshNonce={knowledgeRefreshNonce}
                                    />
                                ) : activeApp?.id === 'security' ? (
                                    <HeartbeatPanel />
                                ) : activeApp?.id === 'genui' ? (
                                    <GenUIPanel />
                                ) : (
                                    <div className="p-12 overflow-y-auto w-full h-full">
                                        <div className="grid grid-cols-2 gap-10">
                                            <div className="p-10 bg-black/30 rounded-[3rem] border border-white/5 flex flex-col items-center justify-center space-y-4">
                                                <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center">
                                                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                                                </div>
                                                <p className="text-sm font-medium text-white/50 text-center uppercase tracking-widest">{activeApp.name} Module Loading...</p>
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
                            <div className="bg-white/10 p-6 border border-white/20 flex flex-col items-center animate-pulse rounded-[2.5rem] shadow-2xl">
                                <Cpu className="w-10 h-10 text-white/80 mb-3 animate-spin-slow" />
                                <p className="text-xs text-white/70 uppercase tracking-widest font-bold">{processingStep}</p>
                            </div>
                        </div>
                    )}
                </main>

                {/* Footer Layer (Permanent and Topmost) */}
                <footer
                    className="absolute bottom-0 left-0 w-full z-[1000] pb-6 px-10 pointer-events-none flex justify-center translate-y-0 opacity-100 scale-100"
                >
                    <div className="pointer-events-auto">
                        <Dock triggerSystemAction={(action) => {
                            triggerSystemAction(action);
                        }} />
                    </div>
                </footer>
            </div>


            {/* Gesture Controller (Hand Tracking) */}
            {cameraActive && stream && backend && (
                <GestureController
                    videoStream={stream}
                    backendBridge={backend}
                    onUpdate={onGestureUpdate}
                />
            )}

            {/* Bottom Glow Effect (Removed inset bottom shadow to prevent overlapping app content) */}
            <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-b from-black/10 via-transparent to-black/20" />
        </div>
    );
}
