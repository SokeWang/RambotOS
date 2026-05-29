import React from 'react';
import { useUI } from '../../context/UIContext';
import { useRambot } from '../../context/RambotContext';
import * as LucideIcons from 'lucide-react';
import { z } from 'zod';
import { defineCatalog } from '@json-render/core';
import { schema } from '@json-render/react/schema';
import { defineRegistry, Renderer, JSONUIProvider } from '@json-render/react';

// ============================================================
// CATALOG DEFINITION
// ============================================================
const catalog = defineCatalog(schema, {
    components: {
        Container: {
            props: z.object({
                className: z.string().optional()
            }).passthrough(),
            description: "A flexible container for layout"
        },
        Carousel: {
            props: z.object({
                className: z.string().optional()
            }).passthrough(),
            description: "A swipeable carousel for multiple items or cards. Place components inside as children."
        },
        Row: {
            props: z.object({
                className: z.string().optional(),
                gap: z.string().optional()
            }).passthrough(),
            description: "A horizontal layout container that displays items side-by-side, with horizontal scrolling if they overflow."
        },
        Text: {
            props: z.object({
                variant: z.string().optional(),
                text: z.string().optional(),
                content: z.string().optional(),
                value: z.string().optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "A text element. Use 'text' or 'content' for the string."
        },
        Button: {
            props: z.object({
                text: z.string().optional(),
                iconName: z.string().optional(),
                className: z.string().optional(),
                actionId: z.string().optional()
            }).passthrough(),
            description: "A clickable button"
        },
        TextInput: {
            props: z.object({
                name: z.string().optional(),
                placeholder: z.string().optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "A text input field for the user to type in. Pressing Enter sends the text to the backend."
        },
        Icon: {
            props: z.object({
                iconName: z.string().optional(),
                className: z.string().optional(),
                size: z.number().optional()
            }).passthrough(),
            description: "A Lucide icon"
        },
        WeatherCard: {
            props: z.object({
                location: z.string().optional(),
                temperature: z.any().optional(),
                condition: z.string().optional(),
                feels_like: z.any().optional(),
                high: z.any().optional(),
                low: z.any().optional(),
                humidity: z.any().optional(),
                wind_speed: z.any().optional(),
                hourly: z.array(z.any()).optional(),
                forecast: z.array(z.any()).optional()
            }).passthrough(),
            description: "Displays weather data"
        },
        Metric: {
            props: z.object({
                label: z.string().optional(),
                value: z.any().optional(),
                unit: z.string().optional(),
                icon: z.string().optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "Displays a single metric"
        },
        FileManager: {
            props: z.object({
                path: z.string().optional(),
                files: z.array(z.any()).optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "Displays a list of files in a directory"
        },
        Image: {
            props: z.object({
                src: z.string(),
                alt: z.string().optional(),
                className: z.string().optional(),
                aspect_ratio: z.string().optional()
            }).passthrough(),
            description: "Displays an image, supports base64 (data:image/...) or URL"
        },
        Video: {
            props: z.object({
                src: z.string(),
                className: z.string().optional(),
                autoPlay: z.boolean().optional(),
                controls: z.boolean().optional(),
                loop: z.boolean().optional(),
                muted: z.boolean().optional()
            }).passthrough(),
            description: "Displays a video, supports local file:// URLs"
        },
        Link: {
            props: z.object({
                href: z.string(),
                label: z.string().optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "An external link. Use 'label' for the link text."
        },
        Map: {
            props: z.object({
                query: z.string().optional(),
                origin: z.string().optional(),
                destination: z.string().optional(),
                zoom: z.number().optional(),
                className: z.string().optional()
            }).passthrough(),
            description: "Displays a navigation map. Use 'query' for single points, or 'origin' and 'destination' for routes."
        }
    },
    actions: {}
});

// ============================================================
// COMPONENT REGISTRY
// ============================================================
const { registry } = defineRegistry(catalog, {
    components: {
        Container: ({ props = {}, children }) => (
            <div className={props.className}>
                {children}
            </div>
        ),
        Carousel: ({ props = {}, children }) => {
            const [currentIndex, setCurrentIndex] = React.useState(0);
            const itemsCount = React.Children.count(children);
            return (
                <div className={`relative w-full max-w-2xl ${props.className || ''}`}>
                    <div className="overflow-hidden rounded-[2rem]">
                        <div 
                            className="flex transition-transform duration-500 ease-in-out"
                            style={{ transform: `translateX(-${currentIndex * 100}%)` }}
                        >
                            {React.Children.map(children, child => (
                                <div className="w-full shrink-0 flex justify-center">
                                    {child}
                                </div>
                            ))}
                        </div>
                    </div>
                    {itemsCount > 1 && (
                        <div className="absolute -bottom-8 left-0 right-0 flex justify-center gap-2">
                            {React.Children.map(children, (_, idx) => (
                                <button 
                                    data-gaze-target="true"
                                    className={`h-2 rounded-full transition-all duration-300 ${idx === currentIndex ? 'bg-cyan-400 w-6' : 'bg-white/20 w-2 hover:bg-white/40'}`}
                                    onClick={() => setCurrentIndex(idx)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            );
        },
        Row: ({ props = {}, children }) => (
            <div className={`grid grid-flow-col auto-cols-fr items-stretch ${props.gap ? `gap-${props.gap}` : 'gap-4'} ${props.className || 'w-full'}`}>
                {React.Children.map(children, child => (
                    <div className="flex flex-col justify-start">
                        {child}
                    </div>
                ))}
            </div>
        ),
        Text: ({ props = {}, children }) => {
            const Tag = props.variant === 'text' ? 'span' : (props.variant || 'p');
            return (
                <Tag className={props.className}>
                    {props.text || props.content || props.value}
                    {children}
                </Tag>
            );
        },
        Button: ({ props = {}, children }) => {
            const Icon = props.iconName ? LucideIcons[props.iconName] : null;
            const { processCommand } = useRambot();
            return (
                <button 
                    data-gaze-target="true" 
                    className={props.className || "px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl hover:bg-blue-500/30 transition-all font-medium"} 
                    onClick={() => {
                        const payload = props.actionId || props.text;
                        if (payload) processCommand(payload);
                    }}
                >
                    {Icon && <Icon className="inline-block mr-2" size={16} />}
                    {props.text && <span>{props.text}</span>}
                    {children}
                </button>
            );
        },
        TextInput: ({ props = {} }) => {
            const [value, setValue] = React.useState('');
            const { processCommand } = useRambot();
            return (
                <input
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && value.trim()) {
                            processCommand(value.trim());
                            setValue('');
                        }
                    }}
                    placeholder={props.placeholder || 'Type here...'}
                    className={`bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500 transition-colors w-full ${props.className || ''}`}
                    data-gaze-target="true"
                />
            );
        },
        Icon: ({ props = {} }) => {
            const IconComp = props.iconName ? LucideIcons[props.iconName] : null;
            return IconComp ? <IconComp className={props.className} size={props.size || 16} /> : null;
        },
        WeatherCard: ({ props = {} }) => {
            // Support legacy "data" wrapper just in case
            const sourceData = props.data || props;
            const { variant = 'default', location = 'Unknown', temperature = '--', condition = '--', feels_like, high, low, humidity, wind_speed, hourly = [] } = sourceData;
            const isCompact = variant === 'compact';
            
            // Interaction States: null, 'loading_q', 'questions', 'loading_a', 'answer'
            const [interactionState, setInteractionState] = React.useState(null);
            const [questions, setQuestions] = React.useState([]);
            const [currentAnswer, setCurrentAnswer] = React.useState('');

            const fetchFromLLM = async (prompt) => {
                const res = await fetch("http://127.0.0.1:8000/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: prompt, sender: "widget_" + Date.now() })
                });
                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let fullText = "";
                while(true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, {stream: true});
                    const lines = chunk.split('\n').filter(l => l.trim());
                    for (let line of lines) {
                        try {
                            const obj = JSON.parse(line);
                            if (obj.reply) fullText = obj.reply; 
                        } catch(e) {}
                    }
                }
                return fullText;
            };

            const startInteraction = async () => {
                if (interactionState !== null) return;
                setInteractionState('loading_q');
                try {
                    const prompt = `基于地点：${location}，气温${high}°C至${low}°C，${condition}。预测用户最想问的2到3个关于生活或出行的简短问题。严格返回纯JSON字符串数组格式，例如：["今天带伞吗？", "适合晨跑吗？", "穿衣建议"]。只输出JSON数组，不要别的废话。`;
                    const text = await fetchFromLLM(prompt);
                    const match = text.match(/\[(.*)\]/s);
                    if (match) {
                        setQuestions(JSON.parse("[" + match[1] + "]"));
                    } else {
                        setQuestions(JSON.parse(text));
                    }
                } catch(e) {
                    setQuestions(["这天气适合穿什么？", "有什么出行建议？"]);
                }
                setInteractionState('questions');
            };

            const askQuestion = async (q) => {
                setInteractionState('loading_a');
                try {
                    const prompt = `地点：${location}，天气：${high}°C至${low}°C，${condition}。请一两句话简短直接回答：${q}`;
                    const ans = await fetchFromLLM(prompt);
                    setCurrentAnswer(ans || "暂时无法生成建议。");
                } catch(e) {
                    setCurrentAnswer("获取由于网络原因失败。");
                }
                setInteractionState('answer');
            };
            
            return (
                <div 
                    onClick={() => { if (!interactionState) startInteraction(); }}
                    className={`w-full ${isCompact ? 'space-y-3' : 'space-y-6 max-w-2xl'} text-white animate-in fade-in slide-in-from-bottom-4 duration-700 relative ${!interactionState ? 'cursor-pointer group-card' : ''}`}
                >
                    <div className={`bg-white/10 ${isCompact ? 'rounded-3xl' : 'rounded-[2rem]'} border border-white/20 flex flex-col justify-between shadow-2xl relative overflow-hidden transition-all duration-300 ${!interactionState ? 'hover:bg-white/20' : ''} min-h-[140px]`}>
                        
                        <div className={`flex items-start justify-between w-full transition-opacity duration-300 ${interactionState ? 'opacity-0 scale-95' : 'opacity-100'} ${isCompact ? 'p-5' : 'p-8'}`}>
                            <div>
                                <p className="text-white/50 text-[10px] uppercase tracking-widest font-mono line-clamp-1">{location}</p>
                                <p className={`${isCompact ? 'text-4xl' : 'text-8xl'} font-thin mt-1 tracking-tighter`}>{temperature}°</p>
                                <p className={`text-white/70 ${isCompact ? 'text-sm' : 'text-xl'} mt-1 line-clamp-1`}>{condition}</p>
                                <p className="text-white/40 text-[10px] mt-1 whitespace-nowrap">H:{high || '--'}° L:{low || '--'}°</p>
                            </div>
                        </div>

                        {interactionState && (
                            <div className="absolute inset-0 z-10 bg-black/70 backdrop-blur-xl flex flex-col items-center justify-center p-4 text-center animate-in fade-in duration-300">
                                <button 
                                    onClick={(e) => { e.stopPropagation(); setInteractionState(null); }}
                                    className="absolute top-2 right-2 text-white/50 hover:text-white hover:bg-white/20 bg-white/10 rounded-full w-6 h-6 flex items-center justify-center text-[10px] z-20 transition-colors"
                                >✕</button>

                                {interactionState === 'loading_q' && (
                                    <div className="flex flex-col items-center gap-2 justify-center h-full">
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span className="text-xs text-white/50">预测问题中...</span>
                                    </div>
                                )}

                                {interactionState === 'questions' && (
                                    <div className="flex flex-col gap-2 w-full mt-4 justify-center h-full max-w-[200px] mx-auto">
                                        <p className="text-[10px] text-white/60 mb-1 uppercase tracking-widest text-left">Suggested for you</p>
                                        {questions.slice(0,3).map((q, i) => (
                                            <button 
                                                key={i}
                                                onClick={(e) => { e.stopPropagation(); askQuestion(q); }}
                                                className="bg-white/10 hover:bg-cyan-400/20 hover:border-cyan-400/40 border border-white/10 rounded-lg py-2 px-3 text-xs w-full transition-all duration-300 text-white/90 text-left line-clamp-1 truncate"
                                            >
                                                {q}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {interactionState === 'loading_a' && (
                                    <div className="flex flex-col items-center gap-2 justify-center h-full">
                                        <div className="w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
                                        <span className="text-xs text-white/50">分析中...</span>
                                    </div>
                                )}

                                {interactionState === 'answer' && (
                                    <div className="flex flex-col items-start text-left w-full h-full justify-between mt-2 pt-2">
                                        <div className="w-full h-full overflow-y-auto pr-1">
                                            <p className="text-white/90 text-xs leading-relaxed">
                                                {currentAnswer}
                                            </p>
                                        </div>
                                        <button 
                                            onClick={(e) => { e.stopPropagation(); setInteractionState('questions'); }}
                                            className="text-cyan-400 text-[10px] mt-2 hover:text-cyan-300 uppercase tracking-wider shrink-0 transition-colors"
                                        >
                                            ← 返回选项
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {hourly.length > 0 && (
                        <div className="bg-white/5 rounded-[2rem] border border-white/10 p-6">
                            <p className="text-white/40 text-xs uppercase tracking-widest font-mono mb-4">Hourly</p>
                            <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
                                {hourly.map((h, i) => (
                                    <div key={i} className="flex flex-col items-center gap-2 min-w-[60px] text-center">
                                        <p className="text-white/50 text-xs font-mono">{h.time}</p>
                                        <p className="text-white text-lg font-light">{h.temp}°</p>
                                        <p className="text-white/40 text-[10px]">{h.condition}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            );
        },
        Metric: ({ props = {} }) => {
            const Icon = props.icon ? LucideIcons[props.icon] : null;
            return (
                <div className={`bg-white/10 rounded-3xl border border-white/10 p-6 flex flex-col items-center justify-center text-center ${props.className}`}>
                    {Icon && <Icon size={32} className="text-cyan-400 mb-3" />}
                    <p className="text-white/50 text-xs uppercase tracking-widest font-mono mb-1">{props.label}</p>
                    <p className="text-4xl font-thin text-white">{props.value}<span className="text-sm text-white/30 ml-1">{props.unit}</span></p>
                </div>
            );
        },
        FileManager: ({ props = {} }) => {
            const { path, files = [], className } = props;
            const getFileIcon = (type, name) => {
                if (type === 'directory' || type === 'folder') return LucideIcons.Folder;
                const ext = name.split('.').pop().toLowerCase();
                if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) return LucideIcons.Image;
                if (['mp4', 'mov', 'avi', 'mkv'].includes(ext)) return LucideIcons.Video;
                if (['mp3', 'wav', 'ogg', 'flac'].includes(ext)) return LucideIcons.Music;
                if (['pdf', 'doc', 'docx', 'txt', 'md'].includes(ext)) return LucideIcons.FileText;
                if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'c', 'cpp', 'html', 'css', 'json'].includes(ext)) return LucideIcons.FileCode;
                if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return LucideIcons.Archive;
                return LucideIcons.File;
            };

            return (
                <div className={`w-full max-w-4xl bg-white/5 rounded-[2.5rem] border border-white/10 overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-1000 ${className || ''}`}>
                    {/* Header */}
                    <div className="bg-white/10 p-6 border-b border-white/10 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-cyan-500/20 rounded-2xl">
                                <LucideIcons.FolderOpen className="text-cyan-400" size={24} />
                            </div>
                            <div>
                                <h3 className="text-white font-medium text-lg">File Manager</h3>
                                <p className="text-white/40 text-xs font-mono truncate max-w-md">{path}</p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button className="p-2 hover:bg-white/10 rounded-xl transition-colors text-white/60"><LucideIcons.Search size={18} /></button>
                            <button className="p-2 hover:bg-white/10 rounded-xl transition-colors text-white/60"><LucideIcons.Grid size={18} /></button>
                            <button className="p-2 hover:bg-white/10 rounded-xl transition-colors text-white/60"><LucideIcons.MoreVertical size={18} /></button>
                        </div>
                    </div>

                    {/* File List */}
                    <div className="p-4 max-h-[500px] overflow-y-auto custom-scrollbar">
                        {files.length === 0 ? (
                            <div className="py-20 flex flex-col items-center justify-center text-white/20">
                                <LucideIcons.Inbox size={48} className="mb-4" />
                                <p>Empty Directory</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {files.map((file, i) => {
                                    const Icon = getFileIcon(file.type, file.name);
                                    return (
                                        <div 
                                            key={i}
                                            data-gaze-target="true"
                                            className="group p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 transition-all duration-300 flex items-center gap-4 cursor-pointer"
                                        >
                                            <div className={`p-3 rounded-2xl group-hover:scale-110 transition-transform duration-500 ${file.type === 'directory' ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                                <Icon size={24} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-white font-medium truncate group-hover:text-cyan-400 transition-colors">{file.name}</p>
                                                <div className="flex items-center gap-3 text-[10px] text-white/30 font-mono mt-1">
                                                    <span>{file.size || (file.type === 'directory' ? '--' : '0 B')}</span>
                                                    <span className="w-1 h-1 rounded-full bg-white/10" />
                                                    <span className="truncate">{file.last_modified || 'Recently'}</span>
                                                </div>
                                            </div>
                                            <LucideIcons.ChevronRight className="text-white/10 group-hover:text-white/40 group-hover:translate-x-1 transition-all" size={16} />
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="bg-white/5 p-4 border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-white/30">
                        <p>{files.length} items</p>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                                <span>System Connected</span>
                            </div>
                        </div>
                    </div>
                </div>
            );
        },
        Image: ({ props = {} }) => {
            const [isExpanded, setIsExpanded] = React.useState(false);
            return (
                <div 
                    className={`relative overflow-hidden group transition-all duration-700 ease-in-out cursor-pointer ${
                        props.className || ''
                    } ${isExpanded ? 'max-w-4xl w-full h-auto' : 'max-h-[300px] w-auto h-auto'}`}
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 z-10" />
                    <img 
                        src={props.src} 
                        alt={props.alt || 'Generated'} 
                        className={`w-full h-full object-contain rounded-3xl border border-white/20 shadow-2xl transition-transform duration-700 ${
                            !isExpanded ? 'group-hover:scale-105' : ''
                        }`}
                        style={{ aspectRatio: props.aspect_ratio }}
                    />
                    {!isExpanded && (
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-500 z-20">
                            <LucideIcons.Maximize2 size={32} className="text-white drop-shadow-lg" />
                        </div>
                    )}
                </div>
            );
        },
        Video: ({ props = {} }) => {
            const videoRef = React.useRef(null);
            const [error, setError] = React.useState(null);

            // Normalize src: ensure file:/// (3 slashes) for absolute paths
            const normalizedSrc = React.useMemo(() => {
                let s = props.src || "";
                // If starts with /, prepend file:// to make it file:///Users/...
                if (s.startsWith("/") && !s.startsWith("//")) {
                    s = "file://" + s;
                }
                // Fix file://Users -> file:///Users
                if (s.startsWith('file://') && !s.startsWith('file:///')) {
                    s = s.replace('file://', 'file:///');
                }
                console.log("RAMBOT_VIDEO_DEBUG_SRC:", s);
                return s;
            }, [props.src]);

            return (
                <div className={`relative overflow-hidden rounded-3xl border border-white/20 shadow-2xl bg-black/40 min-h-[200px] flex items-center justify-center ${props.className || ''}`}>
                    <div className="absolute top-2 left-2 text-[8px] text-white/10 font-mono z-30">V-4.0.2</div>
                    {error ? (
                        <div className="flex flex-col items-center justify-center p-10 text-white/40 text-center">
                            <LucideIcons.AlertTriangle size={48} className="mb-4 text-yellow-500/50" />
                            <p className="font-mono text-xs uppercase tracking-widest mb-2">Media Error</p>
                            <p className="text-xs max-w-xs">{error}</p>
                            <p className="mt-4 text-[10px] opacity-50 font-mono break-all">{normalizedSrc}</p>
                        </div>
                    ) : (
                        <video 
                            ref={videoRef}
                            autoPlay={props.autoPlay ?? true}
                            controls={props.controls ?? true}
                            loop={props.loop ?? true}
                            muted={props.muted ?? true} // Default to muted for autoplay compatibility
                            playsInline
                            className="w-full h-full object-contain rounded-3xl max-h-[600px]"
                            onError={(e) => {
                                const videoElement = e.target;
                                const errorCode = videoElement.error ? videoElement.error.code : 'Unknown';
                                const errorMessage = videoElement.error ? videoElement.error.message : '';
                                console.error("Video error:", errorCode, errorMessage);
                                
                                let detailedError = "The video could not be loaded.";
                                if (errorCode === 1) detailedError = "Fetching process aborted by user.";
                                if (errorCode === 2) detailedError = "Network error while fetching the video.";
                                if (errorCode === 3) detailedError = "Video decoding failed. The format might be unsupported or the file is corrupted.";
                                if (errorCode === 4) detailedError = "Video format or source not supported by the browser engine.";
                                
                                setError(`${detailedError} (Error Code: ${errorCode}${errorMessage ? ` - ${errorMessage}` : ''})`);
                            }}
                            onLoadedMetadata={() => setError(null)}
                        >
                            <source src={normalizedSrc} type="video/mp4" />
                            <source src={normalizedSrc.replace(/\.mp4$/, '.webm')} type="video/webm" />
                            Your browser does not support the video tag.
                        </video>
                    )}
                </div>
            );
        },
        Link: ({ props = {} }) => (
            <a 
                href={props.href} 
                target="_blank" 
                rel="noopener noreferrer" 
                className={`inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30 hover:bg-blue-500/30 transition-all font-medium ${props.className || ''}`}
                data-gaze-target="true"
            >
                <span>{props.label || props.href}</span>
                <LucideIcons.ExternalLink size={14} className="opacity-50" />
            </a>
        ),
        Map: ({ props = {} }) => {
            const { userLocation, requestNativeLocation } = useUI();
            const { query, origin, destination, zoom = 14, className } = props;
            const googleKey = import.meta.env.VITE_GOOGLE_MAPS_KEY;
            const iframeRef = React.useRef(null);

            React.useEffect(() => {
                // Request native location fix on mount (Lazy load)
                if (!userLocation) {
                    requestNativeLocation();
                }

                const sendLocation = () => {
                    if (userLocation && iframeRef.current && iframeRef.current.contentWindow) {
                        iframeRef.current.contentWindow.postMessage({
                            type: 'UPDATE_LOCATION',
                            lat: userLocation.lat,
                            lng: userLocation.lng
                        }, '*');
                    }
                };

                const handleMessage = (e) => {
                    if (e.data && e.data.type === 'REQUEST_LOCATION') {
                        sendLocation();
                    }
                };

                window.addEventListener('message', handleMessage);
                sendLocation(); // Eager push if already ready

                return () => window.removeEventListener('message', handleMessage);
            }, [userLocation]);

            const url = React.useMemo(() => {
                const params = new URLSearchParams();
                if (googleKey) params.set('key', googleKey);
                params.set('zoom', zoom.toString());

                const serializeLoc = (loc) => {
                    // For initial origin calculation, we don't use userLocation synchronously
                    // to avoid iframe reload triggers. PostMessage handles it dynamically.
                    return typeof loc === 'object' ? JSON.stringify(loc) : loc;
                };

                const resOrigin = serializeLoc(origin);
                const resDest = serializeLoc(destination || query);
                
                if (resOrigin) params.set('origin', resOrigin);
                if (resDest) params.set('dest', resDest);
                
                return `./map.html?${params.toString()}`;
            }, [googleKey, zoom, origin, destination, query]);

            return (
                <div className={`relative w-full h-full min-h-[400px] overflow-hidden group ${className || ''}`}>
                    <iframe
                        ref={iframeRef}
                        title="Navigation Map"
                        width="100%"
                        height="100%"
                        frameBorder="0"
                        style={{ 
                            border: 0, 
                            pointerEvents: 'auto',
                            backgroundColor: '#18181b'
                        }}
                        src={url}
                        allowFullScreen
                        allow="geolocation *"
                    ></iframe>
                    
                    {/* Immersive Footer Only */}
                    <div className="absolute bottom-8 right-8 z-20 pointer-events-none flex flex-col items-end gap-2">
                         {userLocation && (
                             <div className="px-3 py-1 bg-cyan-500/20 backdrop-blur-md rounded-full border border-cyan-500/30 flex items-center gap-2 animate-pulse">
                                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                  <span className="text-[8px] font-mono text-cyan-400 uppercase tracking-widest font-bold">High Precision GPS</span>
                             </div>
                         )}
                         <div className="px-4 py-2 bg-black/60 backdrop-blur-md rounded-2xl border border-white/10 flex items-center gap-2 opacity-20 hover:opacity-100 transition-opacity">
                             <LucideIcons.Shield size={12} className="text-white/20" />
                             <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Geo-Engine 5.0 Immersive</span>
                         </div>
                    </div>
                </div>
            );
        }
    }
});

// ============================================================
// GenUIPanel Component
// ============================================================

const GenUIPanel = () => {
    const { genUISchema } = useUI();

    // Check if we only have a Map component to go full immersive
    const isImmersiveMap = React.useMemo(() => {
        if (!genUISchema || !genUISchema.elements) return false;
        const rootElement = genUISchema.elements[genUISchema.root];
        if (!rootElement) return false;
        
        // Either the root is a Map, or it's a Container with only one child which is a Map
        if (rootElement.type === 'Map') return true;
        if (rootElement.type === 'Container' && rootElement.children?.length === 1) {
            const childId = rootElement.children[0];
            const childElement = genUISchema.elements[childId];
            return childElement?.type === 'Map';
        }
        return false;
    }, [genUISchema]);

    return (
        <div className={`w-full h-full overflow-hidden pointer-events-auto ${isImmersiveMap ? 'p-0' : 'p-8'}`}>
            <div className={`w-full h-full flex flex-col items-center justify-center relative overflow-hidden ${isImmersiveMap ? '' : 'bg-black/40 shadow-2xl rounded-[3rem] border border-white/10 p-10'}`}>
                {!isImmersiveMap && <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent blur-3xl rounded-[3rem] pointer-events-none" />}

                <div className="relative z-10 w-full h-full flex flex-col items-center justify-center text-white">
                    {genUISchema ? (
                        <div className="animate-in fade-in zoom-in duration-700 w-full flex flex-col items-center justify-center">
                            {(() => {
                                try {
                                    // Normalize spec: ensure all elements have a children array and props object
                                    const normalizedSpec = JSON.parse(JSON.stringify(genUISchema));
                                    if (!normalizedSpec.elements || typeof normalizedSpec.elements !== 'object') {
                                        normalizedSpec.elements = {};
                                    }
                                    if (normalizedSpec.elements) {
                                        Object.keys(normalizedSpec.elements).forEach(key => {
                                            const el = normalizedSpec.elements[key];
                                            if (!el || typeof el !== 'object') {
                                                normalizedSpec.elements[key] = { type: 'Container', children: [], props: {} };
                                            } else {
                                                if (!Array.isArray(el.children)) el.children = [];
                                                // Prevent circular self-reference
                                                if (el.children.includes(key)) {
                                                    el.children = el.children.filter(id => id !== key);
                                                }
                                                if (!el.props || typeof el.props !== 'object') el.props = {};
                                            }
                                        });
                                    }
                                    
                                    return (
                                        <JSONUIProvider>
                                            <Renderer spec={normalizedSpec} registry={registry} />
                                        </JSONUIProvider>
                                    );
                                } catch (e) {
                                    return (
                                        <div className="p-10 bg-red-500/20 rounded-3xl border border-red-500/50 text-red-200">
                                            <p className="font-bold mb-2">Rendering Error</p>
                                            <p className="text-xs font-mono">{e.message}</p>
                                        </div>
                                    );
                                }
                            })()}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center text-white/40 space-y-6 animate-pulse">
                            <LucideIcons.Layers size={64} className="opacity-50" />
                            <p className="font-mono uppercase tracking-[0.3em] font-bold text-sm text-cyan-400/50">Awaiting Subroutine</p>
                        </div>
                    )}
                </div>
                
                {genUISchema && !genUISchema.root && !genUISchema.type && (
                  <div className="absolute top-4 right-4 text-[10px] font-mono text-yellow-500/50">
                    Malformed Spec (Missing Node Root)
                  </div>
                )}
            </div>
        </div>
    );
};

export default GenUIPanel;
