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
                className: z.string().optional()
            }).passthrough(),
            description: "A text element"
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
                    {props.text}
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
        }
    }
});

// ============================================================
// GenUIPanel Component
// ============================================================

const GenUIPanel = () => {
    const { genUISchema } = useUI();

    return (
        <div className="w-full h-full p-8 overflow-y-auto custom-scrollbar pointer-events-auto">
            <div className="w-full min-h-full bg-black/40 rounded-[3rem] border border-white/10 p-10 shadow-2xl flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent blur-3xl rounded-[3rem] pointer-events-none" />

                <div className="relative z-10 w-full flex flex-col items-center justify-center text-white">
                    {genUISchema ? (
                        <div className="animate-in fade-in zoom-in duration-700 w-full flex flex-col items-center justify-center">
                            {(() => {
                                try {
                                    return (
                                        <JSONUIProvider>
                                            <Renderer spec={genUISchema} registry={registry} />
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
                            {genUISchema && <div className="text-[8px] text-white/10 max-w-xs truncate">{JSON.stringify(genUISchema)}</div>}
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

