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
    const lastNotifTime = useRef(Date.now() / 1000);
    useEffect(() => {
        onAudioEndedRef.current = onAudioEnded;
    }, [onAudioEnded]);

    useEffect(() => {
        console.log("Setting up Backend Connection...");

        // We assume qt.webChannelTransport is injected by the QWebEngine
        if (typeof window.qt !== 'undefined' && window.qt.webChannelTransport) {
            // Ensure QWebChannel is available
            if (typeof window.QWebChannel === 'undefined') {
                console.error("QWebChannel library not loaded!");
                return;
            }
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
            console.log("Qt WebChannel Transport not found. Initializing Web Browser mode.");
            setBackend({
                isMock: true,
                select_file: () => {
                    alert("Local file selection is not available in pure Web mode. Please use drag-and-drop or upload.");
                },
                set_listening_state: (isListening) => {
                    fetch(`http://127.0.0.1:8000/wakeword/state?paused=${isListening}`, { method: 'POST' })
                        .catch(err => console.error("Failed to update wake word state:", err));
                }
            });
            addLog('system', 'Web Mode Backend Initialized');

            // Establish real-time WebSocket connection for events, wake word, and notifications
            let ws = null;
            let reconnectTimeout = null;
            let isCleanClose = false;

            const connectWebSocket = () => {
                console.log("WebSocket: Connecting to ws://127.0.0.1:8000/ws ...");
                ws = new WebSocket("ws://127.0.0.1:8000/ws");

                ws.onopen = () => {
                    console.log("WebSocket: Connection established!");
                    addLog('system', 'Real-time Event Channel Connected');
                };

                ws.onmessage = (event) => {
                    try {
                        const notif = JSON.parse(event.data);
                        console.log("WebSocket: Received event:", notif);
                        if (notif.message === 'WAKE_WORD_TRIGGERED') {
                            console.log("Wake word triggered! Dispatching WakeWordDetected event.");
                            window.dispatchEvent(new CustomEvent('WakeWordDetected'));
                        } else if (notif.source === 'system') {
                            setNotification(notif.message);
                            setTimeout(() => setNotification(null), 8000);
                        }
                    } catch (e) {
                        console.error("WebSocket: Failed to parse event message:", e);
                    }
                };

                ws.onclose = () => {
                    if (!isCleanClose) {
                        console.log("WebSocket: Connection closed. Reconnecting in 3s...");
                        reconnectTimeout = setTimeout(connectWebSocket, 3000);
                    }
                };

                ws.onerror = (err) => {
                    console.error("WebSocket error:", err);
                    ws.close();
                };
            };

            connectWebSocket();

            return () => {
                isCleanClose = true;
                if (ws) {
                    ws.close();
                }
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                }
            };
        }
    }, []);
 
    const sendMessage = useCallback(async (text, attachment, capturedImage, audioBase64 = null) => {
        if (backend && !backend.isMock) {
            backend.chat(text, attachment || "", capturedImage || "");
            return;
        }
        
        console.log("useBackend: Using Web API fallback to send message...");
        addLog('system', audioBase64 ? 'Sending voice message...' : 'Sending message via Web API...');
        
        try {
            // Append temporary user bubble if it's a voice message
            if (audioBase64) {
                setChatHistory(prev => [...prev, {
                    type: 'user',
                    content: [{ type: 'text', text: '🎤 Voice Message (Recognizing...)' }],
                    time: new Date(),
                    attachment: "Voice Layer"
                }]);
            }

            // Append temporary AI "thinking" message
            setChatHistory(prev => [...prev, {
                type: 'ai',
                content: [{ type: 'text', text: 'Thinking...' }],
                time: new Date()
            }]);
            
            const response = await fetch("http://127.0.0.1:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text || null,
                    sender: "os_user",
                    attachment_base64: attachment || null,
                    webcam_base64: capturedImage || null,
                    audio_base64: audioBase64 || null
                })
            });
            
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedReply = "";
            let toolCalls = [];
            let genUIContent = null;
            let base64Audio = null;
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");
                
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const payload = JSON.parse(line);
                            if (payload.user_transcription) {
                                setChatHistory(prev => {
                                    const list = [...prev];
                                    for (let i = list.length - 1; i >= 0; i--) {
                                        if (list[i].type === 'user') {
                                            list[i] = {
                                                ...list[i],
                                                content: [{ type: 'text', text: payload.user_transcription }]
                                            };
                                            break;
                                        }
                                    }
                                    return list;
                                });
                            }
                            if (payload.reply) {
                                accumulatedReply = payload.reply;
                            }
                            if (payload.tool_calls) {
                                toolCalls = payload.tool_calls;
                            }
                            if (payload.gen_ui) {
                                genUIContent = payload.gen_ui;
                            }
                            if (payload.audio) {
                                base64Audio = payload.audio;
                            }
                            
                            if (payload.reply || payload.tool_calls || payload.gen_ui) {
                                setChatHistory(prev => {
                                    const list = [...prev];
                                    const last = list[list.length - 1];
                                    if (last && last.type === 'ai') {
                                        list[list.length - 1] = {
                                            ...last,
                                            content: [{ type: 'text', text: accumulatedReply }],
                                            tool_calls: toolCalls,
                                            time: new Date()
                                        };
                                    }
                                    return list;
                                });
                            }
                        } catch (e) {
                            // ignore partial JSON parse errors
                        }
                    }
                }
            }
            
            if (genUIContent) {
                window.dispatchEvent(new CustomEvent('GenUIReceived', { detail: genUIContent }));
            }
            
            setSubtitle(accumulatedReply);
            setIsSubtitleFading(false);
            if (subtitleTimeoutRef.current) clearTimeout(subtitleTimeoutRef.current);
            subtitleTimeoutRef.current = setTimeout(() => {
                setIsSubtitleFading(true);
                setTimeout(() => setSubtitle(null), 500);
            }, 8000);
            
            addLog('system', 'Response completed.');

            if (base64Audio) {
                console.log("Playing audio from Web API...");
                const audio = new Audio(base64Audio);
                audio.play().catch(e => console.warn("Autoplay blocked:", e.message || e));
            }
            
        } catch (err) {
            console.error("Web API call failed:", err);
            addLog('error', `Web API failed: ${err.message}`);
            setChatHistory(prev => {
                const list = [...prev];
                const last = list[list.length - 1];
                if (last && last.type === 'ai' && last.content[0].text === 'Thinking...') {
                    list[list.length - 1] = {
                        ...last,
                        content: [{ type: 'text', text: `Failed to connect to backend: ${err.message}` }]
                    };
                }
                return list;
            });
        }
    }, [backend, addLog, setChatHistory, setSubtitle, setIsSubtitleFading, subtitleTimeoutRef]);
 
    const processAudio = useCallback((base64Audio, capturedImage) => {
        if (backend && !backend.isMock) {
            backend.process_audio(base64Audio, capturedImage || "");
        } else {
            console.log("useBackend: Handing over audio message to Web API fallback...");
            sendMessage("", null, capturedImage, base64Audio);
        }
    }, [backend, sendMessage]);
 
    const selectFile = useCallback(() => {
        if (backend && !backend.isMock) {
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
