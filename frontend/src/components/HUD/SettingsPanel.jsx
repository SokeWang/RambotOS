import React, { useRef } from 'react';
import { Video, Check, Cpu, Camera, Layers, Activity, Image as ImageIcon, Upload, RotateCcw } from 'lucide-react';
import { useUI } from '../../context/UIContext';
import { useRambot } from '../../context/RambotContext';

export default function SettingsPanel() {
    const {
        showCameraBackground, setShowCameraBackground,
        cursorMode, setCursorMode,
        wallpaper, setWallpaper
    } = useUI();

    const {
        availableCameras, selectedCameraId, setSelectedCameraId
    } = useRambot();

    const fileInputRef = useRef(null);

    const filterModes = [
        { id: 'raw', label: 'Raw Sensor', desc: '无平滑滤波，最快响应', icon: Cpu },
        { id: 'ema', label: 'EMA Filter', desc: '指数移动平均，均衡顺滑', icon: Layers },
        { id: 'kalman', label: 'Kalman Filter', desc: '卡尔曼动态预测，极致稳定', icon: Activity }
    ];

    const handleWallpaperUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setWallpaper(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full overflow-y-auto p-8 gap-10 animate-in fade-in duration-500 custom-scrollbar">
            {/* 1. Camera Immersion Toggle */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">视觉沉浸</h3>
                <button
                    onClick={() => setShowCameraBackground(!showCameraBackground)}
                    className={`w-full p-6 rounded-[2.5rem] border transition-all flex items-center justify-between group ${showCameraBackground ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-white/5 border-white/10 hover:bg-white/10'
                        }`}
                >
                    <div className="flex items-center gap-5">
                        <div className={`p-4 rounded-full transition-colors ${showCameraBackground ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-white/40'}`}>
                            <Video size={24} />
                        </div>
                        <div className="text-left">
                            <p className="font-bold text-white text-lg">背景图像穿透</p>
                            <p className="text-xs text-white/40">开启以在背景中显示实时摄像头画面</p>
                        </div>
                    </div>
                    <div className={`w-14 h-8 rounded-full p-1 transition-colors ${showCameraBackground ? 'bg-cyan-500' : 'bg-white/10'}`}>
                        <div className={`w-6 h-6 rounded-full bg-white shadow-lg transition-transform ${showCameraBackground ? 'translate-x-6' : 'translate-x-0'}`} />
                    </div>
                </button>
            </section>

            {/* 2. Personalization (Wallpaper) */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">个性化定制</h3>
                <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-6 flex flex-col gap-6 font-sans">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-5">
                            <div className="p-4 rounded-full bg-white/5 text-white/40">
                                <ImageIcon size={24} />
                            </div>
                            <div className="text-left">
                                <p className="font-bold text-white text-lg">系统壁纸</p>
                                <p className="text-xs text-white/40">上传自定义图片作为背景图像</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleWallpaperUpload}
                                accept="image/*"
                                className="hidden"
                            />
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-full text-xs font-bold transition-all flex items-center gap-2 border border-white/10"
                            >
                                <Upload size={14} /> 上传图片
                            </button>
                            {wallpaper && (
                                <button
                                    onClick={() => setWallpaper(null)}
                                    className="p-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-full transition-all border border-red-500/20"
                                    title="重置背景"
                                >
                                    <RotateCcw size={14} />
                                </button>
                            )}
                        </div>
                    </div>
                    {wallpaper && (
                        <div className="relative w-full h-32 rounded-2xl overflow-hidden border border-white/10">
                            <img src={wallpaper} alt="Preview" className="w-full h-full object-cover" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-4">
                                <p className="text-[10px] font-bold text-white/60 tracking-widest uppercase">当前壁纸预览</p>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* 3. Cursor Smoothing Filters */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">光标滤波算法</h3>
                <div className="grid grid-cols-3 gap-4">
                    {filterModes.map((mode) => {
                        const Icon = mode.icon;
                        return (
                            <button
                                key={mode.id}
                                onClick={() => setCursorMode(mode.id)}
                                className={`p-6 rounded-[2.5rem] border transition-all flex flex-col items-center gap-3 text-center group ${cursorMode === mode.id ? 'bg-white/20 border-white/40' : 'bg-white/5 border-white/10 hover:bg-white/10'
                                    }`}
                            >
                                <div className={`p-3 rounded-full ${cursorMode === mode.id ? 'bg-white/20 text-white' : 'bg-white/5 text-white/40'}`}>
                                    <Icon size={20} />
                                </div>
                                <div>
                                    <p className="font-bold text-sm text-white">{mode.label}</p>
                                    <p className="text-[10px] text-white/30 mt-1 leading-tight">{mode.desc}</p>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </section>

            {/* 4. Camera Device Selection */}
            <section className="flex flex-col min-h-0">
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">视野来源 (CAM)</h3>
                <div className="bg-black/30 rounded-[3rem] border border-white/10 overflow-hidden flex flex-col max-h-[300px]">
                    <div className="overflow-y-auto p-4 space-y-2 custom-scrollbar">
                        {availableCameras.length > 0 ? (
                            availableCameras.map((camera, idx) => (
                                <button
                                    key={camera.deviceId}
                                    onClick={() => setSelectedCameraId(camera.deviceId)}
                                    className={`w-full p-5 rounded-[2rem] transition-all flex items-center justify-between group ${selectedCameraId === camera.deviceId ? 'bg-white/10 border border-white/20' : 'hover:bg-white/5 border border-transparent'
                                        }`}
                                >
                                    <div className="flex items-center gap-4">
                                        <Camera size={18} className={selectedCameraId === camera.deviceId ? 'text-cyan-400' : 'text-white/30'} />
                                        <span className="text-sm font-medium text-white/80">{camera.label || `摄像头 ${idx + 1}`}</span>
                                    </div>
                                    {selectedCameraId === camera.deviceId && <Check size={18} className="text-green-400" />}
                                </button>
                            ))
                        ) : (
                            <div className="h-40 flex flex-col items-center justify-center text-white/20 gap-3">
                                <Camera size={48} />
                                <p className="text-sm font-medium">未检测到可用摄像头</p>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}
