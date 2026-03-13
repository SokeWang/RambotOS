import React from 'react';
import { useUI } from '../../context/UIContext';
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
        Container: ({ props, children }) => (
            <div className={props.className}>
                {children}
            </div>
        ),
        Text: ({ props, children }) => {
            const Tag = props.variant === 'text' ? 'span' : (props.variant || 'p');
            return (
                <Tag className={props.className}>
                    {props.text || props.content || props.value}
                    {children}
                </Tag>
            );
        },
        Button: ({ props, children }) => {
            const Icon = props.iconName ? LucideIcons[props.iconName] : null;
            return (
                <button 
                    data-gaze-target="true" 
                    className={props.className} 
                    onClick={() => console.log(`Action triggered: ${props.actionId || props.text}`)}
                >
                    {Icon && <Icon className="inline-block mr-2" size={16} />}
                    {props.text && <span>{props.text}</span>}
                    {children}
                </button>
            );
        },
        Icon: ({ props }) => {
            const IconComp = props.iconName ? LucideIcons[props.iconName] : null;
            return IconComp ? <IconComp className={props.className} size={props.size || 16} /> : null;
        },
        WeatherCard: ({ props }) => {
            // Support legacy "data" wrapper just in case
            const sourceData = props.data || props;
            const { location = 'Unknown', temperature = '--', condition = '--', feels_like, high, low, humidity, wind_speed, hourly = [], forecast = [] } = sourceData;
            return (
                <div className="w-full max-w-2xl text-white space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="bg-white/10 rounded-[2rem] border border-white/20 p-8 flex items-start justify-between shadow-2xl">
                        <div>
                            <p className="text-white/50 text-sm uppercase tracking-widest font-mono">{location}</p>
                            <p className="text-8xl font-thin mt-2">{temperature}°</p>
                            <p className="text-white/70 text-xl mt-1">{condition}</p>
                            <p className="text-white/40 text-sm mt-2">Feels like {feels_like || (temperature !== '--' ? temperature - 2 : '--')}° · H:{high || (temperature !== '--' ? temperature + 3 : '--')}° L:{low || (temperature !== '--' ? temperature - 4 : '--')}°</p>
                        </div>
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
        Metric: ({ props }) => {
            const Icon = props.icon ? LucideIcons[props.icon] : null;
            return (
                <div className={`bg-white/10 rounded-3xl border border-white/10 p-6 flex flex-col items-center justify-center text-center ${props.className}`}>
                    {Icon && <Icon size={32} className="text-cyan-400 mb-3" />}
                    <p className="text-white/50 text-xs uppercase tracking-widest font-mono mb-1">{props.label}</p>
                    <p className="text-4xl font-thin text-white">{props.value}<span className="text-sm text-white/30 ml-1">{props.unit}</span></p>
                </div>
            );
        },
        FileManager: ({ props }) => {
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
        Image: ({ props }) => {
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
        Video: ({ props }) => {
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
                            <source src={normalizedSrc.replace(/\.mp4$/, '.webm')} type="video/webm" />
                            <source src={normalizedSrc.replace(/\.webm$/, '.mp4')} type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                    )}
                </div>
            );
        },
        Link: ({ props }) => (
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
        Map: ({ props }) => {
            const { userLocation } = useUI();
            const zoom = props.zoom || 14;
            const apiKey = import.meta.env.VITE_GOOGLE_MAPS_KEY;
            const { query, origin, destination, className } = props;
            
            // Resolve "Current Location" to exact GPS coordinates if available
            const resolveLoc = (loc) => {
                if ((loc === "Current Location" || !loc) && userLocation) {
                    return `${userLocation.lat},${userLocation.lng}`;
                }
                return loc;
            };

            const resolvedOrigin = resolveLoc(origin);
            const resolvedDestination = resolveLoc(destination || query);
            
            let src = "";
            let displayTitle = query || destination || "Navigation Map";

            if (apiKey) {
                // Official Embed API
                if (resolvedOrigin && resolvedDestination) {
                    src = `https://www.google.com/maps/embed/v1/directions?key=${apiKey}&origin=${encodeURIComponent(resolvedOrigin)}&destination=${encodeURIComponent(resolvedDestination)}&zoom=${zoom}`;
                } else {
                    src = `https://www.google.com/maps/embed/v1/place?key=${apiKey}&q=${encodeURIComponent(resolvedDestination)}&zoom=${zoom}`;
                }
            } else {
                // Public Fallback - Use maps.google.com for better compatibility
                if (resolvedOrigin && resolvedDestination) {
                    src = `https://maps.google.com/maps?saddr=${encodeURIComponent(resolvedOrigin)}&daddr=${encodeURIComponent(resolvedDestination)}&output=embed&z=${zoom}`;
                } else {
                    src = `https://maps.google.com/maps?q=${encodeURIComponent(resolvedDestination)}&output=embed&z=${zoom}`;
                }
            }

            return (
                <div className={`relative w-full h-full min-h-[400px] overflow-hidden group ${className || ''}`}>
                    <iframe
                        title="Navigation Map"
                        width="100%"
                        height="100%"
                        frameBorder="0"
                        style={{ 
                            border: 0, 
                            filter: apiKey ? 'invert(90%) hue-rotate(180deg) brightness(0.9) contrast(1.1)' : 'none',
                            pointerEvents: 'auto',
                            backgroundColor: '#18181b'
                        }}
                        src={src}
                        allowFullScreen
                        allow="geolocation"
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
                                    // Normalize spec: ensure all elements have a children array
                                    const normalizedSpec = { ...genUISchema };
                                    if (normalizedSpec.elements) {
                                        Object.keys(normalizedSpec.elements).forEach(key => {
                                            if (!normalizedSpec.elements[key].children) {
                                                normalizedSpec.elements[key].children = [];
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

