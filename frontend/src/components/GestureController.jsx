import React, { useEffect, useRef, useState, useCallback } from 'react';
import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';
import { useUI } from '../context/UIContext';

// Simple Kalman Filter Implementation for 2D Point
class KalmanFilter {
    constructor(R = 1, Q = 1, A = 1, B = 0, C = 1) {
        this.R = R; // Noise covariance
        this.Q = Q; // Process covariance
        this.A = A; // State vector
        this.B = B; // Control vector
        this.C = C; // Measurement vector

        this.cov = NaN;
        this.x = NaN; // Estimated value
    }

    filter(z, u = 0) {
        if (isNaN(this.x)) {
            this.x = (1 / this.C) * z;
            this.cov = (1 / this.C) * this.R * (1 / this.C);
        } else {
            // Predic
            const predX = (this.A * this.x) + (this.B * u);
            const predCov = ((this.A * this.cov) * this.A) + this.Q;

            // Kalman Gain
            const K = predCov * this.C * (1 / ((this.C * predCov * this.C) + this.R));

            // Correction
            this.x = predX + K * (z - (this.C * predX));
            this.cov = predCov - (K * this.C * predCov);
        }
        return this.x;
    }
}

export default function GestureController({ videoStream, backendBridge, onUpdate }) {
    const { cursorMode } = useUI(); // 'raw', 'ema', 'kalman'

    const handLandmarkerRef = useRef(null);
    const lastVideoTimeRef = useRef(-1);
    const requestRef = useRef();
    const [isLoaded, setIsLoaded] = useState(false);

    // Smoothing State References
    const prevPointRef = useRef({ x: null, y: null }); // For EMA
    const kalmanXRef = useRef(new KalmanFilter(0.01, 1)); // Tuned params
    const kalmanYRef = useRef(new KalmanFilter(0.01, 1));

    useEffect(() => {
        const loadLandmarker = async () => {
            try {
                const vision = await FilesetResolver.forVisionTasks(
                    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
                );
                handLandmarkerRef.current = await HandLandmarker.createFromOptions(vision, {
                    baseOptions: {
                        modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
                        delegate: "GPU"
                    },
                    runningMode: "VIDEO",
                    numHands: 1
                });
                setIsLoaded(true);
                console.log("Hand Landmarker Loaded");
            } catch (error) {
                console.error("Error loading HandLandmarker:", error);
            }
        };

        loadLandmarker();

        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (!isLoaded || !videoStream || !handLandmarkerRef.current) return;

        const video = document.createElement('video');
        video.srcObject = videoStream;
        video.play();
        video.muted = true;

        const predict = () => {
            if (video.currentTime !== lastVideoTimeRef.current) {
                lastVideoTimeRef.current = video.currentTime;
                const startTimeMs = performance.now();

                try {
                    const results = handLandmarkerRef.current.detectForVideo(video, startTimeMs);

                    if (results.landmarks && results.landmarks.length > 0) {
                        const landmarks = results.landmarks[0];
                        const indexTip = landmarks[8];
                        const thumbTip = landmarks[4];

                        const distance = Math.sqrt(
                            Math.pow(indexTip.x - thumbTip.x, 2) +
                            Math.pow(indexTip.y - thumbTip.y, 2)
                        );

                        let targetX = 1 - indexTip.x;
                        let targetY = indexTip.y;

                        if (cursorMode === 'ema') {
                            const alpha = 0.2;
                            if (prevPointRef.current.x !== null) {
                                targetX = targetX * alpha + prevPointRef.current.x * (1 - alpha);
                                targetY = targetY * alpha + prevPointRef.current.y * (1 - alpha);
                            }
                            prevPointRef.current = { x: targetX, y: targetY };
                        } else if (cursorMode === 'kalman') {
                            targetX = kalmanXRef.current.filter(targetX);
                            targetY = kalmanYRef.current.filter(targetY);
                        }

                        const screenX = targetX * window.innerWidth;
                        const screenY = targetY * window.innerHeight;
                        const isPinched = distance < 0.05;

                        // Send back to parent (HUD)
                        if (onUpdate) {
                            onUpdate({
                                x: screenX,
                                y: screenY,
                                isPinching: isPinched
                            });
                        }
                    }
                } catch (e) {
                    // ignore interruptions
                }
            }
            requestRef.current = requestAnimationFrame(predict);
        };

        video.addEventListener('loadeddata', predict);

        return () => {
            video.pause();
            video.srcObject = null;
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [isLoaded, videoStream, onUpdate, cursorMode]);

    return null; // No internal rendering
}
