import React, { useRef } from 'react';
import { Video, Check, Cpu, Camera, Layers, Activity, Image as ImageIcon, Upload, RotateCcw, Mail, Save, MessageSquare } from 'lucide-react';
import { useUI } from '../../context/UIContext';
import { useRambot } from '../../context/RambotContext';

export default function SettingsPanel() {
    const {
        showCameraBackground, setShowCameraBackground,
        cursorMode, setCursorMode,
        wallpaper, setWallpaper,
        genUIEnabled, setGenUIEnabled
    } = useUI();

    const {
        availableCameras, selectedCameraId, setSelectedCameraId
    } = useRambot();

    const [userEmail, setUserEmail] = React.useState('');
    const [telegramId, setTelegramId] = React.useState('');
    const [isSavingEmail, setIsSavingEmail] = React.useState(false);
    const [saveStatus, setSaveStatus] = React.useState(null);
    const [isSavingTelegram, setIsSavingTelegram] = React.useState(false);
    const [tgSaveStatus, setTgSaveStatus] = React.useState(null);
    const [sessions, setSessions] = React.useState([]);
    const [linkTargetSession, setLinkTargetSession] = React.useState('');
    const [linkIdentifier, setLinkIdentifier] = React.useState('');
    const [isLinking, setIsLinking] = React.useState(false);

    React.useEffect(() => {
        if (window.backendBridge) {
            try {
                const profileJson = window.backendBridge.get_user_profile();
                const profile = JSON.parse(profileJson);
                if (profile) {
                    if (profile.email) setUserEmail(profile.email);
                    if (profile.telegram_chat_id) setTelegramId(profile.telegram_chat_id);
                }

                const sessionsJson = window.backendBridge.get_sessions();
                setSessions(JSON.parse(sessionsJson) || []);
            } catch (e) {
                console.error("Failed to load profile:", e);
            }
        }
    }, []);

    const handleBindEmail = () => {
        if (!userEmail || !userEmail.includes('@')) {
            setSaveStatus('error');
            return;
        }

        setIsSavingEmail(true);
        setSaveStatus(null);

        try {
            const success = window.backendBridge.bind_user(userEmail);
            setIsSavingEmail(false);
            setSaveStatus(success ? 'success' : 'error');

            if (success) {
                setTimeout(() => setSaveStatus(null), 3000);
            }
        } catch (e) {
            setIsSavingEmail(false);
            setSaveStatus('error');
        }
    };

    const handleBindTelegram = () => {
        if (!telegramId) {
            setTgSaveStatus('error');
            return;
        }

        setIsSavingTelegram(true);
        setTgSaveStatus(null);

        try {
            const success = window.backendBridge.bind_telegram_id(telegramId);
            setIsSavingTelegram(false);
            setTgSaveStatus(success ? 'success' : 'error');

            if (success) {
                setTimeout(() => setTgSaveStatus(null), 3000);
            }
        } catch (e) {
            setIsSavingTelegram(false);
            setTgSaveStatus('error');
        }
    };

    const handleLinkSession = () => {
        if (!linkTargetSession || !linkIdentifier) return;

        setIsLinking(true);
        const success = window.backendBridge.link_session(linkTargetSession, linkIdentifier);

        if (success) {
            const sessionsJson = window.backendBridge.get_sessions();
            setSessions(JSON.parse(sessionsJson));
            setLinkIdentifier('');
        }
        setIsLinking(false);
    };

    const fileInputRef = useRef(null);

    const filterModes = [
        { id: 'raw', label: 'Raw Sensor', desc: 'Raw sensor data, zero filtering, fastest response', icon: Cpu },
        { id: 'ema', label: 'EMA Filter', desc: 'Exponential Moving Average, balanced and smooth', icon: Layers },
        { id: 'kalman', label: 'Kalman Filter', desc: 'Kalman dynamic prediction, maximum stability', icon: Activity }
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
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">Visual Immersion</h3>
                <div className="flex flex-col gap-4">
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
                                <p className="font-bold text-white text-lg">Background Passthrough</p>
                                <p className="text-xs text-white/40">Enables live camera feed as the system background</p>
                            </div>
                        </div>
                        <div className={`w-14 h-8 rounded-full p-1 transition-colors ${showCameraBackground ? 'bg-cyan-500' : 'bg-white/10'}`}>
                            <div className={`w-6 h-6 rounded-full bg-white shadow-lg transition-transform ${showCameraBackground ? 'translate-x-6' : 'translate-x-0'}`} />
                        </div>
                    </button>

                    {/* GenUI Mode Toggle */}
                    <button
                        onClick={() => setGenUIEnabled(!genUIEnabled)}
                        className={`w-full p-6 rounded-[2.5rem] border transition-all flex items-center justify-between group ${genUIEnabled ? 'bg-purple-500/10 border-purple-500/30' : 'bg-white/5 border-white/10 hover:bg-white/10'
                            }`}
                    >
                        <div className="flex items-center gap-5">
                            <div className={`p-4 rounded-full transition-colors ${genUIEnabled ? 'bg-purple-500/20 text-purple-400' : 'bg-white/5 text-white/40'}`}>
                                <Layers size={24} />
                            </div>
                            <div className="text-left">
                                <p className="font-bold text-white text-lg">GenUI Mode</p>
                                <p className="text-xs text-white/40">Enable AI-generated spatial interface components</p>
                            </div>
                        </div>
                        <div className={`w-14 h-8 rounded-full p-1 transition-colors ${genUIEnabled ? 'bg-purple-500' : 'bg-white/10'}`}>
                            <div className={`w-6 h-6 rounded-full bg-white shadow-lg transition-transform ${genUIEnabled ? 'translate-x-6' : 'translate-x-0'}`} />
                        </div>
                    </button>
                </div>
            </section>

            {/* 1b. Account Identity (New) */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">Account & Identity</h3>
                <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-6 flex flex-col gap-6 font-sans">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-5">
                            <div className="p-4 rounded-full bg-white/5 text-white/40">
                                <Mail size={24} />
                            </div>
                            <div className="text-left">
                                <p className="font-bold text-white text-lg">Master Identity</p>
                                <p className="text-xs text-white/40">Bind your email for cross-channel recognition (Email/OS)</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <input
                            type="email"
                            value={userEmail}
                            onChange={(e) => setUserEmail(e.target.value)}
                            placeholder="your-email@example.com"
                            className="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/50 transition-all font-mono text-sm"
                        />
                        <button
                            onClick={handleBindEmail}
                            disabled={isSavingEmail}
                            className={`px-8 py-4 rounded-2xl font-bold flex items-center gap-3 transition-all ${saveStatus === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                                saveStatus === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                    'bg-cyan-500 hover:bg-cyan-600 text-black shadow-lg shadow-cyan-500/20'
                                }`}
                        >
                            {isSavingEmail ? (
                                <Activity className="animate-spin" size={18} />
                            ) : saveStatus === 'success' ? (
                                <Check size={18} />
                            ) : (
                                <Save size={18} />
                            )}
                            {saveStatus === 'success' ? 'Bound' : isSavingEmail ? 'Saving...' : 'Bind Identity'}
                        </button>
                    </div>
                </div>

                <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-6 flex flex-col gap-6 font-sans mt-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-5">
                            <div className="p-4 rounded-full bg-white/5 text-white/40">
                                <MessageSquare size={24} />
                            </div>
                            <div className="text-left">
                                <p className="font-bold text-white text-lg">Telegram Connection</p>
                                <p className="text-xs text-white/40">Bind your Telegram Chat ID for secure mobile access</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <input
                            type="text"
                            value={telegramId}
                            onChange={(e) => setTelegramId(e.target.value)}
                            placeholder="Your Telegram Chat ID"
                            className="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-all font-mono text-sm"
                        />
                        <button
                            onClick={handleBindTelegram}
                            disabled={isSavingTelegram}
                            className={`px-8 py-4 rounded-2xl font-bold flex items-center gap-3 transition-all ${tgSaveStatus === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                                tgSaveStatus === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                    'bg-blue-500 hover:bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                                }`}
                        >
                            {isSavingTelegram ? (
                                <Activity className="animate-spin" size={18} />
                            ) : tgSaveStatus === 'success' ? (
                                <Check size={18} />
                            ) : (
                                <Save size={18} />
                            )}
                            {tgSaveStatus === 'success' ? 'Linked' : isSavingTelegram ? 'Saving...' : 'Link Telegram'}
                        </button>
                    </div>
                </div>

                <div className="mt-8">
                    <h4 className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] mb-4 ml-4">Unified Sessions (Multi-ID Mapping)</h4>
                    <div className="flex flex-col gap-3">
                        {sessions.map(sess => (
                            <div key={sess.session_id} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm ${sess.session_id === 'master' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-blue-500/10 text-blue-400'}`}>
                                            {sess.name ? sess.name[0] : '?'}
                                        </div>
                                        <div>
                                            <p className="font-bold text-white text-base">{sess.name} {sess.session_id === 'master' ? '(Owner)' : ''}</p>
                                            <p className="text-[10px] text-white/30 font-mono tracking-tighter">SID: {sess.session_id}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setLinkTargetSession(sess.session_id)}
                                        className={`px-4 py-2 rounded-full text-[10px] font-bold transition-all ${linkTargetSession === sess.session_id ? 'bg-blue-500 text-white' : 'bg-white/5 text-white/40 hover:bg-white/10'}`}
                                    >
                                        {linkTargetSession === sess.session_id ? 'Targeted' : 'Link Identifier'}
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {(sess.linked_ids || []).map(id => (
                                        <div key={id} className="px-3 py-1 bg-black/40 border border-white/5 rounded-lg text-[10px] text-white/60 font-mono">
                                            {id.startsWith('telegram_') ? `TG: ${id.replace('telegram_', '')}` : id}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}

                        {linkTargetSession && (
                            <div className="mt-4 p-6 rounded-[2rem] border border-blue-500/30 bg-blue-500/5 flex flex-col gap-4 animate-in slide-in-from-top-2 duration-300">
                                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest text-center">Unify Identity to Session</p>
                                <div className="flex gap-2">
                                    <input
                                        placeholder="Telegram ID or Email to unify"
                                        value={linkIdentifier}
                                        onChange={e => setLinkIdentifier(e.target.value)}
                                        className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-xs font-mono placeholder:text-white/20 focus:outline-none focus:border-blue-500/50"
                                    />
                                    <button
                                        onClick={handleLinkSession}
                                        disabled={isLinking}
                                        className="px-6 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20 font-bold text-xs"
                                    >
                                        {isLinking ? <RotateCcw size={16} className="animate-spin" /> : 'Confirm link'}
                                    </button>
                                    <button
                                        onClick={() => setLinkTargetSession('')}
                                        className="p-3 bg-white/5 hover:bg-white/10 text-white/40 rounded-xl transition-all"
                                    >
                                        Cancel
                                    </button>
                                </div>
                                <p className="text-[10px] text-white/20 text-center italic">Example: Adding a friend's Email to their existing Telegram session</p>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* 2. Personalization (Wallpaper) */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">Personalization</h3>
                <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-6 flex flex-col gap-6 font-sans">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-5">
                            <div className="p-4 rounded-full bg-white/5 text-white/40">
                                <ImageIcon size={24} />
                            </div>
                            <div className="text-left">
                                <p className="font-bold text-white text-lg">System Wallpaper</p>
                                <p className="text-xs text-white/40">Upload a custom image for the desktop background</p>
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
                                <Upload size={14} /> Upload Image
                            </button>
                            {wallpaper && (
                                <button
                                    onClick={() => setWallpaper(null)}
                                    className="p-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-full transition-all border border-red-500/20"
                                    title="Reset Background"
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
                                <p className="text-[10px] font-bold text-white/60 tracking-widest uppercase">Current Wallpaper Preview</p>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* 3. Cursor Smoothing Filters */}
            <section>
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">Cursor Filtering Algorithm</h3>
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
                <h3 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 ml-4">Visual Feed Source (CAM)</h3>
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
                                        <span className="text-sm font-medium text-white/80">{camera.label || `Camera ${idx + 1}`}</span>
                                    </div>
                                    {selectedCameraId === camera.deviceId && <Check size={18} className="text-green-400" />}
                                </button>
                            ))
                        ) : (
                            <div className="h-40 flex flex-col items-center justify-center text-white/20 gap-3">
                                <Camera size={48} />
                                <p className="text-sm font-medium">No available cameras detected</p>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}
