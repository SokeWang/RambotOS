import React, { createContext, useContext, useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useBackend } from '../hooks/useBackend';
import { useAudio } from '../hooks/useAudio';
import { useCamera } from '../hooks/useCamera';
import { useUI } from './UIContext';

const RambotContext = createContext(null);

export const useRambot = () => {
    const context = useContext(RambotContext);
    if (!context) {
        throw new Error('useRambot must be used within a RambotProvider');
    }
    return context;
};

export const RambotProvider = ({ children }) => {
    const {
        setProcessingStep, setSubtitle, setIsSubtitleFading, setNotification,
        setShowChatbox, setShowLogs,
        windowMode, setWindowMode,
        isSystemReady, setIsSystemReady,
        showCameraBackground,
        addLog: uiAddLog,
        setActiveApp,
        setShowAppLauncher
    } = useUI();

    // --- Logic State ---
    const [logs, setLogs] = useState([{ type: 'system', content: 'System initialization complete' }]);
    const [chatHistory, setChatHistory] = useState(() => {
        try {
            const saved = localStorage.getItem('rambot_chat_history');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {
                    return parsed.map(msg => ({
                        ...msg,
                        time: msg.time ? new Date(msg.time) : new Date()
                    }));
                }
            }
        } catch (e) {
            console.error("Failed to parse cached history:", e);
        }
        return [];
    });
    const [attachment, setAttachment] = useState(null);
    const [historyOffset, setHistoryOffset] = useState(0);
    const [hasMoreHistory, setHasMoreHistory] = useState(true);
    const [isVoiceInteraction, setIsVoiceInteraction] = useState(false);
    const subtitleTimeoutRef = useRef(null);

    const addLog = useCallback((type, content) => {
        setLogs(p => [...p.slice(-4), { type, content }]);
    }, []);

    // --- Hooks Integration ---
    const cameraProps = useCamera(addLog, showCameraBackground);
    const { captureFrame, cameraActive } = cameraProps;

    // --- Refs for circular dependencies ---
    const setIsListeningRef = useRef(null);
    const startRecordingRef = useRef(null);

    const onTTSFinished = useCallback(() => {
        if (isVoiceInteraction) {
            console.log("TTS Finished, starting continuous listening...");
            addLog('system', 'TTS finished, starting continuous conversation (5s)');
            if (startRecordingRef.current) startRecordingRef.current({ continuous: true });
        }
    }, [addLog, isVoiceInteraction]);

    const backendProps = useBackend(
        addLog,
        setChatHistory,
        setSubtitle,
        setIsSubtitleFading,
        subtitleTimeoutRef,
        onTTSFinished,
        setAttachment,
        setNotification,
        setHasMoreHistory
    );

    const loadMoreHistory = useCallback(async () => {
        if (!hasMoreHistory) return;
        const newOffset = historyOffset + 20;
        setHistoryOffset(newOffset);
        
        try {
            const res = await fetch(`http://127.0.0.1:8000/history?session_id=os_user&limit=20&offset=${newOffset}`);
            const messages = await res.json();
            
            const formattedMessages = messages.map(msg => {
                let content = msg.content;
                let tool_calls = [];
                let display_text = "";
                
                if (msg.role === 'ai') {
                    const content_list = Array.isArray(content) ? content : [];
                    let text_content = "";
                    
                    for (let item of content_list) {
                        if (item.type === 'text') {
                            if (item.text.startsWith('__TOOL_CALLS_METADATA__: ')) {
                                try {
                                    tool_calls.push(...JSON.parse(item.text.replace('__TOOL_CALLS_METADATA__: ', '')));
                                } catch(e) {}
                            } else {
                                text_content = item.text;
                            }
                        } else if (item.type === 'tool_calls') {
                            tool_calls.push(...(item.calls || []));
                        }
                    }
                    
                    if (!text_content && content_list.length > 0) {
                        text_content = typeof content === 'string' ? content : JSON.stringify(content);
                    }
                    
                    try {
                        const parsed = JSON.parse(text_content);
                        display_text = parsed.reply || text_content;
                    } catch(e) {
                        display_text = text_content;
                    }
                } else {
                    display_text = content;
                }
                
                return {
                    type: msg.role,
                    content: msg.role === 'ai' ? display_text : content,
                    tool_calls: msg.role === 'ai' ? tool_calls : [],
                    time: new Date(msg.time)
                };
            });

            setChatHistory(prev => [...formattedMessages, ...prev]);
            if (setHasMoreHistory) setHasMoreHistory(formattedMessages.length === 20);
        } catch (e) {
            console.error("Failed to load more history API:", e);
        }
    }, [hasMoreHistory, historyOffset, setHasMoreHistory]);

    // Save history to localStorage
    useEffect(() => {
        localStorage.setItem('rambot_chat_history', JSON.stringify(chatHistory));
    }, [chatHistory]);

    const handleVoiceProcess = useCallback((base64Audio, capturedImage) => {
        setIsVoiceInteraction(true);
        backendProps.processAudio(base64Audio, capturedImage);
    }, [backendProps.processAudio]);

    const audioProps = useAudio(
        addLog,
        handleVoiceProcess,
        captureFrame,
        backendProps.backend
    );
    const { setIsListening, startRecording } = audioProps;

    // Sync ref
    useEffect(() => {
        setIsListeningRef.current = setIsListening;
        startRecordingRef.current = startRecording;
    }, [setIsListening, startRecording]);

    // --- Business Logic Handlers ---
    const triggerSystemAction = useCallback((action) => {
        if (action === 'Chatbox' || action === 'TOGGLE_CHAT') {
            setShowChatbox(prev => {
                const newState = !prev;
                addLog('system', newState ? 'Starting communication module' : 'Closing communication module');
                if (newState) {
                    setHistoryOffset(0);
                    // Fetch top 20
                    fetch('http://127.0.0.1:8000/history?session_id=os_user&limit=20&offset=0')
                        .then(res => res.json())
                        .then(messages => {
                            const formattedMessages = messages.map(msg => {
                                let content = msg.content;
                                let tool_calls = [];
                                let display_text = "";
                                
                                if (msg.role === 'ai') {
                                    const content_list = Array.isArray(content) ? content : [];
                                    let text_content = "";
                                    
                                    for (let item of content_list) {
                                        if (item.type === 'text') {
                                            if (item.text.startsWith('__TOOL_CALLS_METADATA__: ')) {
                                                try {
                                                    tool_calls.push(...JSON.parse(item.text.replace('__TOOL_CALLS_METADATA__: ', '')));
                                                } catch(e) {}
                                            } else {
                                                text_content = item.text;
                                            }
                                        } else if (item.type === 'tool_calls') {
                                            tool_calls.push(...(item.calls || []));
                                        }
                                    }
                                    
                                    if (!text_content && content_list.length > 0) {
                                        text_content = typeof content === 'string' ? content : JSON.stringify(content);
                                    }
                                    
                                    try {
                                        const parsed = JSON.parse(text_content);
                                        display_text = parsed.reply || text_content;
                                    } catch(e) {
                                        display_text = text_content;
                                    }
                                } else {
                                    display_text = content;
                                }
                                
                                return {
                                    type: msg.role,
                                    content: msg.role === 'ai' ? display_text : content,
                                    tool_calls: msg.role === 'ai' ? tool_calls : [],
                                    time: new Date(msg.time)
                                };
                            });
                            setChatHistory(formattedMessages);
                            if (setHasMoreHistory) setHasMoreHistory(formattedMessages.length === 20);
                        }).catch(e => console.error(e));
                }
                return newState;
            });
        } else if (action === 'Settings') {
            setActiveApp({ name: 'System Settings', id: 'Settings' });
            addLog('system', 'Opening System Settings');
        } else if (action === 'TOGGLE_LAUNCHER') {
            setShowAppLauncher(prev => !prev);
            addLog('system', 'Toggling App Launcher');
        } else {
            setActiveApp({ name: action, id: action });
            addLog('system', `Launching App: ${action}`);
        }
    }, [setShowChatbox, setActiveApp, setShowAppLauncher, addLog, backendProps]);

    const toggleWindowMode = useCallback(() => {
        const newMode = windowMode === 'full' ? 'mini' : 'full';
        setWindowMode(newMode);
        if (backendProps.backend && backendProps.backend.set_window_state) {
            backendProps.backend.set_window_state(newMode);
            addLog('system', `Window switched to ${newMode} mode`);
        }
    }, [windowMode, setWindowMode, backendProps.backend, addLog]);

    const processCommand = useCallback(async (text) => {
        setIsVoiceInteraction(false);
        const currentAttachment = attachment; // Capture state at start of function

        const capturedImage = cameraActive ? captureFrame() : null;

        if (cameraActive && !capturedImage) {
            addLog('system', '⚠️ Webcam capture failed, sending text only.');
        } else if (!cameraActive) {
            // Camera is not active, skipping capture
        }

        const uiAttachmentLabel = currentAttachment ? currentAttachment.split('/').pop() : (capturedImage ? "Camera Frame" : null);

        addLog('system', `Sending command with attach=${uiAttachmentLabel || 'none'}`);

        const userContent = [];
        if (text) userContent.push({ type: 'text', text: text });
        if (capturedImage) {
            userContent.push({
                type: 'image',
                base64: capturedImage.includes(',') ? capturedImage.split(',')[1] : capturedImage,
                mime_type: 'image/jpeg'
            });
        }
        if (currentAttachment) {
            userContent.push({
                type: 'file',
                name: currentAttachment.split('/').pop(),
                path: currentAttachment
            });
        }

        // Update UI immediately, do not wait for backend response
        setChatHistory(prev => [...prev, {
            type: 'user',
            content: userContent,
            time: new Date(),
            attachment: uiAttachmentLabel // Keep this for backward compatibility or simple label
        }]);

        // Clear attachment immediately
        if (currentAttachment) {
            setAttachment(null);
        }

        setProcessingStep('Analyzing intent...');

        // Send message asynchronously, do not block UI
        setTimeout(() => {
            backendProps.sendMessage(text, currentAttachment, capturedImage);
        }, 0);

        // Analysis intent could still happen but we remove chart-specific trigger

        setProcessingStep('Executing');
        setTimeout(() => setProcessingStep(null), 1500);
    }, [cameraActive, captureFrame, attachment, addLog, backendProps, setProcessingStep, setChatHistory]);

    // Wake Word Effect and Control Signal
    useEffect(() => {
        if (backendProps.backend) {
            const onWakeWord = () => {
                console.log("Wake Word Detected! Starting recording... (Global)");
                addLog('system', 'Wake word triggered: Rambot');
                setIsVoiceInteraction(true);
                startRecording();
            };

            const onControlSignal = (action, target) => {
                console.log(`Received Control Signal: ${action} ${target}`);
                addLog('system', `AI Control: ${action} ${target}`);

                // Route to triggerSystemAction if it matches existing logic, or handle directly
                // Mapping targets to triggerSystemAction keys
                const targetMap = {
                    'chatbox': 'Chatbox'
                };

                const mappedTarget = targetMap[target.toLowerCase()];

                if (action === 'open') {
                    if (mappedTarget) triggerSystemAction(mappedTarget);
                } else if (action === 'close') {
                    // Removed launchpad closing
                } else if (action === 'toggle') {
                    if (mappedTarget) triggerSystemAction(mappedTarget);
                }
            };

            if (backendProps.backend.wakeWordDetected) {
                backendProps.backend.wakeWordDetected.connect(onWakeWord);
            }
            if (backendProps.backend.controlSignal) {
                backendProps.backend.controlSignal.connect(onControlSignal);
            }

            const onSystemInitialized = () => {
                console.log("System Initialized!");
                addLog('system', 'Core system initialization complete');
                setIsSystemReady(true);
                if (backendProps.backend.say_welcome) {
                    backendProps.backend.say_welcome();
                }
            };

            if (backendProps.backend.initialized) {
                backendProps.backend.initialized.connect(onSystemInitialized);
            }

            return () => {
                try {
                    if (backendProps.backend.wakeWordDetected) {
                        backendProps.backend.wakeWordDetected.disconnect(onWakeWord);
                    }
                    if (backendProps.backend.controlSignal) {
                        backendProps.backend.controlSignal.disconnect(onControlSignal);
                    }
                    if (backendProps.backend.initialized) {
                        backendProps.backend.initialized.disconnect(onSystemInitialized);
                    }
                } catch (e) { /* ignore */ }
            };
        }
    }, [backendProps.backend, startRecording, addLog, triggerSystemAction]);

    // Destructure extra stable fields not yet destructured above
    const { stream, captureRef, canvasRef, availableCameras, selectedCameraId,
        setSelectedCameraId, showCameraSelector, setShowCameraSelector } = cameraProps;
    const { isListening, toggleListening } = audioProps;
    const { backend, sendMessage, processAudio, selectFile } = backendProps;

    const value = useMemo(() => ({
        logs, addLog,
        historyOffset, setHistoryOffset,
        hasMoreHistory, loadMoreHistory,
        chatHistory, setChatHistory,
        attachment, setAttachment,
        triggerSelectFile: selectFile,
        triggerSystemAction,
        toggleWindowMode,
        processCommand,
        // Re-spread for full access in consumers
        ...cameraProps,
        ...audioProps,
        ...backendProps
    }), [
        logs, chatHistory, attachment, addLog,
        historyOffset, hasMoreHistory, loadMoreHistory,
        triggerSystemAction, toggleWindowMode, processCommand,
        // Specific stable values instead of whole hook objects
        captureFrame, cameraActive, stream, captureRef, canvasRef,
        availableCameras, selectedCameraId, setSelectedCameraId,
        showCameraSelector, setShowCameraSelector,
        isListening, toggleListening, startRecording, setIsListening,
        backend, sendMessage, processAudio, selectFile
    ]);

    return (
        <RambotContext.Provider value={value}>
            {children}
        </RambotContext.Provider>
    );
};
