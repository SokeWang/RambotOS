import { useState, useEffect, useRef, useCallback } from 'react';

export const useCamera = (addLog, enabled = true) => {
    const [stream, setStream] = useState(null);
    const [cameraActive, setCameraActive] = useState(false);
    const [availableCameras, setAvailableCameras] = useState([]);
    const [selectedCameraId, setSelectedCameraId] = useState(null);
    const [showCameraSelector, setShowCameraSelector] = useState(false);

    // Hidden refs for capture
    const captureRef = useRef(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!enabled) return;

        const enumerateCameras = async () => {
            try {
                // Request permission to get labels
                await navigator.mediaDevices.getUserMedia({ video: true });

                const devices = await navigator.mediaDevices.enumerateDevices();
                const videoDevices = devices.filter(device => device.kind === 'videoinput');

                console.log(`Found ${videoDevices.length} camera(s):`, videoDevices);
                setAvailableCameras(videoDevices);

                // Use first camera by default
                if (videoDevices.length > 0 && !selectedCameraId) {
                    setSelectedCameraId(videoDevices[0].deviceId);
                }

                addLog('system', `发现 ${videoDevices.length} 个摄像头`);
            } catch (err) {
                console.error("Failed to enumerate cameras:", err);
                addLog('error', '无法枚举摄像头');
            }
        };

        enumerateCameras();
    }, [addLog, enabled]);

    useEffect(() => {
        if (!enabled) {
            if (stream) {
                console.log("Stopping camera stream (disabled by user)");
                stream.getTracks().forEach(track => track.stop());
                setStream(null);
                setCameraActive(false);
                addLog('system', '摄像头已释放');
            }
            return;
        }

        if (!selectedCameraId) return;

        let activeStream = null;

        const startCamera = async () => {
            try {
                console.log("Starting camera:", selectedCameraId);
                addLog('system', '正在启动摄像头...');

                // Stop previous stream if exists
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }

                const constraints = {
                    video: {
                        deviceId: { exact: selectedCameraId },
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };

                const s = await navigator.mediaDevices.getUserMedia(constraints);
                activeStream = s;

                console.log("Camera access granted!");
                setStream(s);

                const cameraName = availableCameras.find(c => c.deviceId === selectedCameraId)?.label || '未知摄像头';
                addLog('system', `✅ ${cameraName}`);

            } catch (err) {
                console.error("Camera access failed:", err.name, err.message);
                addLog('error', `摄像头访问失败: ${err.message}`);
                setCameraActive(false);
            }
        };

        startCamera();

        return () => {
            if (activeStream) {
                console.log("Cleaning up camera stream");
                activeStream.getTracks().forEach(track => track.stop());
            }
        };
    }, [selectedCameraId, availableCameras, addLog, enabled]);

    // Sync stream to hidden capture video
    useEffect(() => {
        if (captureRef.current && stream) {
            captureRef.current.srcObject = stream;

            // 添加loadeddata事件监听，确保视频准备好
            const videoElement = captureRef.current;

            const onLoadedData = () => {
                setCameraActive(true);
                addLog('system', `📹 摄像头就绪 (${videoElement.videoWidth}x${videoElement.videoHeight})`);
            };

            // 如果视频已经ready，立即设置
            if (videoElement.readyState >= 2) {
                onLoadedData();
            } else {
                // 否则等待loadeddata事件
                videoElement.addEventListener('loadeddata', onLoadedData, { once: true });
            }

            captureRef.current.play().catch(e => console.error("Hidden video play failed", e));

            return () => {
                videoElement.removeEventListener('loadeddata', onLoadedData);
            };
        } else if (!stream) {
            // 如果stream被移除，设置cameraActive为false
            setCameraActive(false);
        }
    }, [stream, addLog]);

    const captureFrame = useCallback(() => {
        if (!captureRef.current || !canvasRef.current) {
            console.error("Capture refs missing");
            addLog('error', 'Capture refs missing');
            return null;
        }
        const video = captureRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        // Check readyState (2 = HAVE_CURRENT_DATA, 4 = HAVE_ENOUGH_DATA)
        if (video.readyState < 2 || video.videoWidth === 0) {
            console.warn("Video not ready for capture. ReadyState:", video.readyState, "Size:", video.videoWidth, "x", video.videoHeight);
            addLog('system', `⚠️ Camera not ready (${video.readyState})`);
            return null;
        }

        // Downscale logic: limit width to 640px while maintaining aspect ratio
        const targetWidth = 640;
        const scaleFactor = Math.min(1, targetWidth / video.videoWidth);
        const w = video.videoWidth * scaleFactor;
        const h = video.videoHeight * scaleFactor;

        canvas.width = w;
        canvas.height = h;

        context.drawImage(video, 0, 0, w, h);

        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        console.log(`Captured frame: ${w}x${h}, len: ${dataUrl.length}`);
        return dataUrl;
    }, [addLog]);

    return {
        stream,
        cameraActive,
        availableCameras,
        selectedCameraId,
        setSelectedCameraId,
        showCameraSelector,
        setShowCameraSelector,
        captureRef,
        canvasRef,
        captureFrame
    };
};
