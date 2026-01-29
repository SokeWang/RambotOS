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
        setProcessingStep, setSubtitle, setIsSubtitleFading,
        setShowChatbox, setShowLogs,
        setGenUI,
        windowMode, setWindowMode,
        isSystemReady, setIsSystemReady,
        showCameraBackground,
        addLog: uiAddLog
    } = useUI();

    // --- Logic State ---
    const [logs, setLogs] = useState([{ type: 'system', content: '系统初始化完成' }]);
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

    // Save history to localStorage
    useEffect(() => {
        localStorage.setItem('rambot_chat_history', JSON.stringify(chatHistory));
    }, [chatHistory]);
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

    const handleUIResponse = useCallback((uiData) => {
        const { react_code } = uiData;
        if (react_code) {
            setGenUI({ reactCode: react_code });
            setShowChatbox(false);
            addLog('system', 'Custom GenUI Transpiled');
        } else {
            setGenUI({ reactCode: null });
        }
    }, [setGenUI, setShowChatbox, addLog]);

    const onTTSFinished = useCallback(() => {
        if (isVoiceInteraction) {
            console.log("TTS Finished, starting continuous listening...");
            addLog('system', 'TTS结束，开启连续对话 (5s)');
            if (startRecordingRef.current) startRecordingRef.current({ continuous: true });
        }
    }, [addLog, isVoiceInteraction]);

    const backendProps = useBackend(
        addLog,
        setChatHistory,
        setSubtitle,
        setIsSubtitleFading,
        subtitleTimeoutRef,
        (is) => setIsListeningRef.current?.(is), // Break circle with Ref
        handleUIResponse,
        onTTSFinished,
        setAttachment
    );

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

        if (action === 'Chatbox') {
            setShowChatbox(prev => {
                const newState = !prev;
                addLog('system', newState ? '启动通讯模块' : '关闭通讯模块');
                // backendProps.speak(newState ? '加密通讯信道已建立' : '通讯结束');
                return newState;
            });
        } else if (action === 'ClearUI') {
            setGenUI({ component: 'none', props: {} });
            addLog('system', 'UI已清理');
        } else {
            // backendProps.speak(`${action} 指令已激活`);
            addLog('system', `手动操作: ${action}`);
        }
    }, [setShowChatbox, setShowLogs, addLog, backendProps]);

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

        // 立即更新 UI,不等待后端响应
        setChatHistory(prev => [...prev, {
            type: 'user',
            content: userContent,
            time: new Date(),
            attachment: uiAttachmentLabel // Keep this for backward compatibility or simple label
        }]);

        // 立即清除附件
        if (currentAttachment) {
            setAttachment(null);
        }

        setProcessingStep('分析意图...');

        // 异步发送消息,不阻塞 UI
        setTimeout(() => {
            backendProps.sendMessage(text, currentAttachment, capturedImage);
        }, 0);

        // Analysis intent could still happen but we remove chart-specific trigger

        setProcessingStep('执行中');
        setTimeout(() => setProcessingStep(null), 1500);
    }, [cameraActive, captureFrame, attachment, addLog, backendProps, setProcessingStep, setChatHistory]);

    // Wake Word Effect and Control Signal
    useEffect(() => {
        if (backendProps.backend) {
            const onWakeWord = () => {
                console.log("Wake Word Detected! Starting recording... (Global)");
                addLog('system', '唤醒词触发: Rambot');
                setIsVoiceInteraction(true);
                startRecording();
            };

            const onControlSignal = (action, target) => {
                console.log(`Received Control Signal: ${action} ${target}`);
                addLog('system', `AI 控制: ${action} ${target}`);

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
                addLog('system', '核心系统初始化完成');
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

    const value = useMemo(() => ({
        logs, addLog,
        chatHistory, setChatHistory,
        attachment, setAttachment,
        triggerSelectFile: backendProps.selectFile,
        triggerSystemAction,
        toggleWindowMode,
        processCommand,
        // Combined props from hooks
        ...cameraProps,
        ...audioProps,
        ...backendProps
    }), [
        logs, chatHistory, attachment, addLog,
        triggerSystemAction, toggleWindowMode, processCommand,
        cameraProps, audioProps, backendProps
    ]);

    return (
        <RambotContext.Provider value={value}>
            {children}
        </RambotContext.Provider>
    );
};
