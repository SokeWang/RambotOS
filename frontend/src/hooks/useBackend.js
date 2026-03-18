import { useState, useEffect, useRef, useCallback } from 'react';

export const useBackend = (addLog, setChatHistory, setSubtitle, setIsSubtitleFading, subtitleTimeoutRef,
    onAudioEnded,
    setAttachment,
    setNotification,
    setHasMoreHistory
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
            // Store handlers for cleanup
            const registeredHandlers = {};

            new window.QWebChannel(window.qt.webChannelTransport, function (channel) {
                const backendBridge = channel.objects.backendBridge;
                window.backendBridge = backendBridge; // Expose globally for other hooks
                setBackend(backendBridge);
                addLog('system', 'Backend Bridge Connected');

                // Handle Chat Response
                registeredHandlers.chatResponse = function (rawResponse) {
                    try {
                        let responseText = rawResponse;
                        let webcamNeeded = false;
                        let toolCalls = [];
                        let payload = {};

                        // Try parsing as JSON
                        if (typeof rawResponse === 'string' && rawResponse.startsWith("{")) {
                            try {
                                payload = JSON.parse(rawResponse);
                                responseText = payload.text || "";
                                webcamNeeded = payload.webcam_needed || false;
                                toolCalls = payload.tool_calls || [];
                            } catch (parseError) {
                                console.error("Error parsing JSON response", parseError);
                            }
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
                        
                        // Extract and Handle GenUI Content
                        const genUIContent = payload.gen_ui;
                        console.log('useBackend: Received payload:', payload);
                        if (genUIContent) {
                            console.log('useBackend: GenUI detected in payload, content type:', typeof genUIContent);
                            window.dispatchEvent(new CustomEvent('GenUIReceived', { detail: genUIContent }));
                        }

                        if (responseText && responseText.startsWith("Error")) {
                            addLog('error', responseText);
                        } else {
                            // Update history with webcam_needed and tool_calls
                            if (!payload.is_welcome) {
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
                            }

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
                };
                backendBridge.chatResponse.connect(registeredHandlers.chatResponse);

                // Handle File Selection
                registeredHandlers.attachmentSelected = function (filePath) {
                    console.log("Attachment selected:", filePath);
                    const fileName = filePath.split('/').pop();
                    addLog('system', `Attachment Selected: ${fileName}`);
                    setAttachment(filePath);
                };
                backendBridge.attachmentSelected.connect(registeredHandlers.attachmentSelected);

                // Handle ASR Result
                if (backendBridge.speechRecognized) {
                    registeredHandlers.speechRecognized = function (text) {
                        console.log("ASR Recognized:", text);
                        addLog('user', text);
                        setChatHistory(prev => [...prev, {
                            type: 'user',
                            content: [{ type: 'text', text: text }],
                            time: new Date(),
                            attachment: "Voice Layer"
                        }]);
                    };
                    backendBridge.speechRecognized.connect(registeredHandlers.speechRecognized);
                }

                // Handle Frontend TTS
                if (backendBridge.audioGenerated) {
                    registeredHandlers.audioGenerated = function (base64Audio) {
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
                                console.warn("Audio autoplay blocked by browser or playback failed:", e.message || e);
                                
                                // The browser blocked autoplay. Let's add a global listener to replay on the very next click.
                                const unlockAudio = () => {
                                    audio.play().catch(err => console.error("Still failed after unlock:", err));
                                    if (backendBridge.set_agent_busy) backendBridge.set_agent_busy(false);
                                    document.removeEventListener('click', unlockAudio);
                                    document.removeEventListener('keydown', unlockAudio);
                                };
                                document.addEventListener('click', unlockAudio);
                                document.addEventListener('keydown', unlockAudio);
                                
                                addLog('system', 'Audio autoplay blocked. Click anywhere to play.');
                                // Keep agent busy flag until clicked, or optionally free it if you prefer:
                                // if (backendBridge.set_agent_busy) backendBridge.set_agent_busy(false);
                            });
                        }
                    };
                    backendBridge.audioGenerated.connect(registeredHandlers.audioGenerated);
                }

                if (backendBridge.historyLoaded) {
                    registeredHandlers.historyLoaded = function (historyDataJson) {
                        try {
                            const { messages, offset } = JSON.parse(historyDataJson);
                            console.log(`Loaded history: ${messages.length}, Offset: ${offset}`);

                            const processedHistory = messages.map(msg => ({
                                ...msg,
                                time: new Date(msg.time)
                            }));

                            if (offset === 0) {
                                setChatHistory(processedHistory);
                            } else {
                                // Prepend older messages
                                setChatHistory(prev => [...processedHistory, ...prev]);
                            }
                            if (setHasMoreHistory) setHasMoreHistory(messages.length === 20);
                            addLog('system', `Loaded ${messages.length} history records (Offset: ${offset})`);
                        } catch (e) {
                            console.error("Failed to parse history:", e);
                        }
                    };
                    backendBridge.historyLoaded.connect(registeredHandlers.historyLoaded);
                }

                // Request history immediately after connection via REST API
                setTimeout(() => {
                    if (!historyRequested.current) {
                        console.log("Requesting history via API...");
                        historyRequested.current = true;
                        fetch('http://127.0.0.1:8000/history?session_id=os_user&limit=20&offset=0')
                            .then(res => res.json())
                            .then(messages => {
                                console.log(`Loaded history via API: ${messages.length}`);
                                // Re-format messages for the frontend
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
                                addLog('system', `Loaded ${formattedMessages.length} history records`);
                            })
                            .catch(err => {
                                console.error('Failed to fetch history via API:', err);
                            });
                    }
                }, 500);

                // Notify backend that frontend is ready to receive initialization signals
                setTimeout(() => {
                    if (backendBridge.frontend_ready) {
                        backendBridge.frontend_ready();
                    }
                }, 800);

                // Handle Develop Mode
                if (backendBridge.developModeChanged) {
                    registeredHandlers.developModeChanged = function (enabled) {
                        console.log("Develop Mode Changed:", enabled);
                        addLog('system', `Develop Mode: ${enabled ? 'ON' : 'OFF'}`);
                        if (window.onDevelopModeChange) window.onDevelopModeChange(enabled);
                    };
                    backendBridge.developModeChanged.connect(registeredHandlers.developModeChanged);
                }

                // Handle System Notifications
                if (backendBridge.notificationSignal) {
                    registeredHandlers.notificationSignal = function (message) {
                        console.log("System Notification Received:", message);
                        addLog('system', `[NOTIFY] ${message}`);
                        setNotification(message);
                        // Auto clear after 8 seconds
                        setTimeout(() => {
                            setNotification(null);
                        }, 8000);
                    };
                    backendBridge.notificationSignal.connect(registeredHandlers.notificationSignal);
                }
            });

            // Cleanup: disconnect all registered signal handlers on unmount
            return () => {
                const bridge = window.backendBridge;
                if (!bridge) return;
                try {
                    if (registeredHandlers.chatResponse) bridge.chatResponse.disconnect(registeredHandlers.chatResponse);
                    if (registeredHandlers.attachmentSelected) bridge.attachmentSelected.disconnect(registeredHandlers.attachmentSelected);
                    if (bridge.speechRecognized && registeredHandlers.speechRecognized) bridge.speechRecognized.disconnect(registeredHandlers.speechRecognized);
                    if (bridge.audioGenerated && registeredHandlers.audioGenerated) bridge.audioGenerated.disconnect(registeredHandlers.audioGenerated);
                    if (bridge.historyLoaded && registeredHandlers.historyLoaded) bridge.historyLoaded.disconnect(registeredHandlers.historyLoaded);
                    if (bridge.developModeChanged && registeredHandlers.developModeChanged) bridge.developModeChanged.disconnect(registeredHandlers.developModeChanged);
                    if (bridge.notificationSignal && registeredHandlers.notificationSignal) bridge.notificationSignal.disconnect(registeredHandlers.notificationSignal);
                } catch (e) {
                    console.warn("Signal cleanup error:", e);
                }
            };
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
            // Note: listening state is managed by useAudio, not here
        }
    }, [backend]);

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
