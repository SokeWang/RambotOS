import { useState, useEffect, useRef, useCallback } from 'react';

export const useAudio = (addLog, processAudio, captureFrame, backend) => {
    const [isListening, setIsListening] = useState(false);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const startRecordingRef = useRef(null);

    useEffect(() => {
        const startRecording = async (options = {}) => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                chunksRef.current = [];

                // --- VAD (Silence Detection) Setup ---
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                source.connect(analyser);

                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);

                let silenceStart = Date.now();
                let speechStarted = false;
                const SILENCE_THRESHOLD = 5;
                const SILENCE_DURATION = 1500;
                const MAX_DURATION = 100000;
                const CONTINUOUS_TIMEOUT = 5000; // 5s wait for speech
                const startTime = Date.now();
                const isContinuous = options?.continuous || false; // New Option

                // Notify Backend to Pause Wake Word
                const bridge = backend || window.backendBridge;
                if (bridge && bridge.set_listening_state) {
                    bridge.set_listening_state(true);
                }

                const checkSilence = () => {
                    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
                        if (audioContext.state !== 'closed') audioContext.close();
                        return;
                    }

                    analyser.getByteFrequencyData(dataArray);

                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
                    const average = sum / bufferLength;

                    if (average > SILENCE_THRESHOLD) {
                        silenceStart = Date.now();
                        if (!speechStarted) speechStarted = true;
                    } else {
                        // Logic 1: Post-Speech Silence (Stop after speaking)
                        if (speechStarted && (Date.now() - silenceStart > SILENCE_DURATION)) {
                            console.log("VAD: Silence detected (end of speech), stopping...");
                            addLog('system', 'Silence detected, stopping...');
                            if (mediaRecorderRef.current.state === 'recording') {
                                mediaRecorderRef.current.requestData();
                                mediaRecorderRef.current.stop();
                            }
                            return;
                        }

                        // Logic 2: Initial Silence Timeout (Continuous Mode Only)
                        if (isContinuous && !speechStarted && (Date.now() - startTime > CONTINUOUS_TIMEOUT)) {
                            console.log("VAD: Continuous Mode Timeout (No speech detected). Aborting.");
                            addLog('system', 'Wait timeout (5s)');
                            // Abort without saving data
                            if (mediaRecorderRef.current.state === 'recording') {
                                // Stop but don't process? 
                                // Actually stop() triggers onstop which triggers processAudio.
                                // We need a flag to abort processing.
                                mediaRecorderRef.current.abortProcessing = true;
                                mediaRecorderRef.current.stop();
                            }
                            return;
                        }
                    }

                    if (Date.now() - startTime > MAX_DURATION) {
                        console.log("Max duration reached");
                        if (mediaRecorderRef.current.state === 'recording') mediaRecorderRef.current.stop();
                        return;
                    }

                    requestAnimationFrame(checkSilence);
                };

                mediaRecorderRef.current.ondataavailable = (e) => {
                    if (e.data.size > 0) chunksRef.current.push(e.data);
                };

                mediaRecorderRef.current.onstop = () => {
                    if (audioContext.state !== 'closed') audioContext.close();

                    // If aborted (timeout), don't process
                    if (mediaRecorderRef.current.abortProcessing) {
                        console.log("Recording aborted (Timeout).");
                        setIsListening(false);
                        // Notify Backend to Resume Wake Word
                        const bridge = backend || window.backendBridge;
                        if (bridge && bridge.set_listening_state) {
                            bridge.set_listening_state(false);
                        }
                        return;
                    }

                    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const base64data = reader.result;
                        const capturedImage = captureFrame ? captureFrame() : "";

                        // Ensure we pass the source if it's a raw base64 from captureFrame
                        processAudio(base64data, capturedImage);
                    };
                    reader.readAsDataURL(blob);
                    stream.getTracks().forEach(track => track.stop());

                    setIsListening(false);
                    // Notify Backend to Resume Wake Word
                    const bridge = backend || window.backendBridge;
                    if (bridge && bridge.set_listening_state) {
                        bridge.set_listening_state(false);
                    }
                };

                mediaRecorderRef.current.start();
                checkSilence();
                setIsListening(true);
                addLog('system', 'Recording started (autostop after speaking)...');

            } catch (err) {
                console.error("Microphone access failed:", err);
                addLog('error', 'Microphone access failed');
                setIsListening(false);
                // Notify Backend to Resume Wake Word on error
                const bridge = backend || window.backendBridge;
                if (bridge && bridge.set_listening_state) {
                    bridge.set_listening_state(false);
                }
            }
        };

        startRecordingRef.current = startRecording;
    }, [addLog, processAudio, captureFrame, backend]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            addLog('system', 'Recording stopped, recognizing...');
        }
    }, [addLog]);

    const toggleListening = useCallback(() => {
        if (isListening) {
            stopRecording();
        } else {
            if (startRecordingRef.current) {
                startRecordingRef.current();
            }
        }
    }, [isListening, stopRecording]);

    // Expose startRecording for creating a stable ref or direct call if needed (e.g., from wake word)
    const startRecording = useCallback(() => {
        if (startRecordingRef.current) {
            startRecordingRef.current();
        }
    }, []);

    return {
        isListening,
        toggleListening,
        startRecording, // Exported for wake word triggering
        setIsListening
    };
};
