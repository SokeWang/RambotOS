import { useState, useEffect, useRef, useCallback } from 'react';

export const useBackend = (addLog, setChatHistory, setSubtitle, setIsSubtitleFading, subtitleTimeoutRef,
    setIsListening,
    onAudioEnded,
    setAttachment,
    setNotification
) => {
    const [backend, setBackend] = useState(null);

    // Use Ref to access latest callback without re-running effect
    const onAudioEndedRef = useRef(onAudioEnded);
    const historyRequested = useRef(false);
    useEffect(() => {
        onAudioEndedRef.current = onAudioEnded;
    }, [onAudioEnded]);

    useEffect(() => {
        console.log("Setting up Backend Connection...");

        // Ensure QWebChannel is available
        if (typeof window.QWebChannel === 'undefined') {
            console.error("QWebChannel library not loaded!");
            return;
        }

        // We assume qt.webChannelTransport is injected by the QWebEngine
        if (typeof window.qt !== 'undefined' && window.qt.webChannelTransport) {
            new window.QWebChannel(window.qt.webChannelTransport, function (channel) {
                const backendBridge = channel.objects.backendBridge;
                window.backendBridge = backendBridge; // Expose globally for other hooks
                setBackend(backendBridge);
                addLog('system', 'Backend Bridge Connected');

                // Handle Chat Response
                backendBridge.chatResponse.connect(function (rawResponse) {
                    try {
                        let responseText = rawResponse;
                        let webcamNeeded = false;
                        let toolCalls = [];

                        // Try parsing as JSON
                        if (typeof rawResponse === 'string' && rawResponse.startsWith("{")) {
                            const payload = JSON.parse(rawResponse);
                            responseText = payload.text || "";
                            webcamNeeded = payload.webcam_needed || false;
                            toolCalls = payload.tool_calls || [];
                        } else if (typeof rawResponse !== 'string') {
                            console.warn("Received non-string response:", rawResponse);
                            responseText = String(rawResponse);
                        }

                        let structuredContent;
                        try {
                            if (responseText.trim().startsWith("[")) {
                                structuredContent = JSON.parse(responseText);
                            }
                        } catch (e) { }

                        if (!Array.isArray(structuredContent)) {
                            structuredContent = [{ type: 'text', text: responseText }];
                        }

                        if (responseText && responseText.startsWith("Error")) {
                            addLog('error', responseText);
                        } else {
                            // Update history with webcam_needed and tool_calls
                            setChatHistory(prev => {
                                const currentHistory = Array.isArray(prev) ? prev : [];
                                const updatedHistory = [...currentHistory];

                                // Update last user message's webcamNeeded
                                for (let i = updatedHistory.length - 1; i >= 0; i--) {
                                    if (updatedHistory[i].type === 'user') {
                                        updatedHistory[i] = { ...updatedHistory[i], webcamNeeded };
                                        break;
                                    }
                                }

                                const lastMsg = updatedHistory[updatedHistory.length - 1];
                                if (lastMsg && lastMsg.type === 'ai') {
                                    updatedHistory[updatedHistory.length - 1] = {
                                        ...lastMsg,
                                        content: structuredContent,
                                        tool_calls: toolCalls,
                                        time: new Date()
                                    };
                                } else {
                                    updatedHistory.push({
                                        type: 'ai',
                                        content: structuredContent,
                                        tool_calls: toolCalls,
                                        time: new Date()
                                    });
                                }
                                return updatedHistory;
                            });

                            // Show Subtitle if Chatbox is closed
                            let subtitleText = "";
                            structuredContent.forEach(block => {
                                if (block.type === 'text') subtitleText += block.text + " ";
                            });
                            setSubtitle(subtitleText.trim());

                            setIsSubtitleFading(false);
                            if (subtitleTimeoutRef.current) clearTimeout(subtitleTimeoutRef.current);
                            subtitleTimeoutRef.current = setTimeout(() => {
                                setIsSubtitleFading(true);
                                setTimeout(() => setSubtitle(null), 500);
                            }, 8000);

                        }
                    } catch (e) {
                        console.error("Error parsing chat response:", e, "Raw:", rawResponse);
                        addLog('error', `Frontend Parse Error: ${e.message}`);
                    }
                });

                // Handle File Selection
                backendBridge.attachmentSelected.connect(function (filePath) {
                    console.log("Attachment selected:", filePath);
                    const fileName = filePath.split('/').pop();
                    addLog('system', `Attachment Selected: ${fileName}`);
                    setAttachment(filePath);
                });

                // Handle ASR Result
                if (backendBridge.speechRecognized) {
                    backendBridge.speechRecognized.connect(function (text) {
                        console.log("ASR Recognized:", text);
                        addLog('user', text);

                        setChatHistory(prev => [...prev, {
                            type: 'user',
                            content: [{ type: 'text', text: text }],
                            time: new Date(),
                            attachment: "Voice Layer"
                        }]);

                        setIsListening(false);
                    });
                }

                // Handle Frontend TTS
                if (backendBridge.audioGenerated) {
                    backendBridge.audioGenerated.connect(function (base64Audio) {
                        if (base64Audio) {
                            console.log("Playing audio...");
                            if (backendBridge.set_agent_busy) backendBridge.set_agent_busy(true);

                            const audio = new Audio(base64Audio);

                            audio.onended = () => {
                                console.log("Audio playback finished.");
                                if (backendBridge.set_agent_busy) backendBridge.set_agent_busy(false);
                                if (onAudioEndedRef.current) onAudioEndedRef.current();
                            };

                            audio.play().catch(e => {
                                console.error("Audio playback failed:", e);
                                if (backendBridge.set_agent_busy) backendBridge.set_agent_busy(false);
                            });
                        }
                    });
                }

                // Handle Wake Word
                if (backendBridge.wakeWordDetected) {
                    // logic will be handled in useAudio or App via event listener if possible, 
                    // or we expose a callback registry.
                    // IMPORTANT: The original code called 'startRecordingRef.current()'.
                    // We need a way to trigger startRecording from here.
                }

                // Handle History Loading
                if (backendBridge.historyLoaded) {
                    backendBridge.historyLoaded.connect(function (historyJson) {
                        try {
                            const history = JSON.parse(historyJson);
                            console.log("Loaded history:", history.length);
                            // Process history if needed (e.g. date conversion)
                            const processedHistory = history.map(msg => ({
                                ...msg,
                                time: new Date(msg.time)
                            }));
                            setChatHistory(processedHistory);
                            addLog('system', `Loaded ${history.length} history records`);
                        } catch (e) {
                            console.error("Failed to parse history:", e);
                        }
                    });

                    // Request history immediately after connection
                    setTimeout(() => {
                        if (!historyRequested.current) {
                            console.log("Requesting history...");
                            backendBridge.requestHistory();
                            historyRequested.current = true;
                        }
                    }, 500);
                }

                // Handle Develop Mode
                if (backendBridge.developModeChanged) {
                    backendBridge.developModeChanged.connect(function (enabled) {
                        console.log("Develop Mode Changed:", enabled);
                        addLog('system', `Develop Mode: ${enabled ? 'ON' : 'OFF'}`);
                        // We need a way to update the state in RambotContext
                        if (window.onDevelopModeChange) window.onDevelopModeChange(enabled);
                    });
                }

                // Handle System Notifications
                if (backendBridge.notificationSignal) {
                    backendBridge.notificationSignal.connect(function (message) {
                        console.log("System Notification Received:", message);
                        addLog('system', `[NOTIFY] ${message}`);

                        setNotification(message);

                        // Auto clear after 8 seconds
                        setTimeout(() => {
                            setNotification(null);
                        }, 8000);
                    });
                }
            });
        } else {
            console.log("Qt WebChannel Transport not found (Dev Mode?)");
        }
    }, []);

    const sendMessage = useCallback((text, attachment, capturedImage) => {
        if (backend) {
            backend.chat(text, attachment || "", capturedImage || "");
        } else {
            console.error("Backend not connected");
            addLog('error', 'Backend Disconnected');
        }
    }, [backend, addLog]);

    const processAudio = useCallback((base64Audio, capturedImage) => {
        if (backend) {
            backend.process_audio(base64Audio, capturedImage || "");
        } else {
            console.error("Backend not connected!");
            setIsListening(false);
        }
    }, [backend, setIsListening]);

    const selectFile = useCallback(() => {
        if (backend) {
            backend.select_file();
        } else {
            console.error("Backend not connected for file selection");
        }
    }, [backend]);

    return {
        backend,
        sendMessage,
        processAudio,

        selectFile
    };
};
