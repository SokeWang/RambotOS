import React, { useMemo, useCallback, useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Trash2, X } from 'lucide-react';

const MemoryGraph = ({ memories, onDelete }) => {
    const fgRef = useRef();
    const containerRef = useRef();
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [selectedNode, setSelectedNode] = useState(null);
    const [selectedLink, setSelectedLink] = useState(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // Handle container resizing
    useEffect(() => {
        if (containerRef.current) {
            const resizeObserver = new ResizeObserver((entries) => {
                for (let entry of entries) {
                    setDimensions({
                        width: entry.contentRect.width,
                        height: entry.contentRect.height
                    });
                }
            });

            resizeObserver.observe(containerRef.current);
            return () => resizeObserver.disconnect();
        }
    }, []);

    const graphData = useMemo(() => {
        const nodesMap = new Map();
        const links = [];

        memories.forEach(mem => {
            if (mem.subject && mem.predicate && mem.object) {
                // Ignore case by using lowercased keys for grouping
                const sKey = mem.subject.trim().toLowerCase();
                const oKey = mem.object.trim().toLowerCase();

                if (!nodesMap.has(sKey)) {
                    nodesMap.set(sKey, {
                        id: sKey,
                        label: mem.subject.trim(), // Keep original casing for display
                        type: 'subject',
                        color: '#818cf8',
                        memories: []
                    });
                }
                if (!nodesMap.has(oKey)) {
                    nodesMap.set(oKey, {
                        id: oKey,
                        label: mem.object.trim(),
                        type: 'object',
                        color: '#4ade80',
                        memories: []
                    });
                }

                nodesMap.get(sKey).memories.push(mem.id);
                nodesMap.get(oKey).memories.push(mem.id);

                links.push({
                    source: sKey,
                    target: oKey,
                    label: mem.predicate,
                    id: mem.id
                });
            } else if (mem.text || mem.content) {
                const content = mem.text || mem.content;
                const cKey = content.trim().toLowerCase();
                if (!nodesMap.has(cKey)) {
                    nodesMap.set(cKey, {
                        id: cKey,
                        label: content.trim(),
                        type: 'trace',
                        color: '#94a3b8',
                        memories: [mem.id]
                    });
                } else {
                    nodesMap.get(cKey).memories.push(mem.id);
                }
            }
        });

        return {
            nodes: Array.from(nodesMap.values()),
            links: links
        };
    }, [memories]);

    // Handle initial zoom/auto-centering
    useEffect(() => {
        if (fgRef.current && graphData.nodes.length > 0 && dimensions.width > 0) {
            fgRef.current.d3Force('charge').strength(-400); // Slightly less repulsion
            fgRef.current.d3Force('link').distance(150); // Slightly closer links

            setTimeout(() => {
                // Use moderate padding
                fgRef.current.zoomToFit(800, 80);
                
                // Enforce a minimum zoom level after fitting so small graphs aren't tiny, but not huge
                setTimeout(() => {
                    const currentZoom = fgRef.current.zoom();
                    if (currentZoom < 0.8) {
                        fgRef.current.zoom(0.8, 400);
                    }
                }, 850);
            }, 400);
        }
    }, [graphData, dimensions]);

    const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
        const label = node.label; // Use preserved label instead of id
        const baseFontSize = 14;
        ctx.font = `${baseFontSize}px Inter, system-ui, sans-serif`;

        const textWidth = ctx.measureText(label).width;
        const bckgDimensions = [textWidth, baseFontSize].map(n => n + baseFontSize * 0.8);

        const isSelected = selectedNode && selectedNode.id === node.id;

        // --- GLOW EFFECT ---
        ctx.shadowColor = node.color;
        ctx.shadowBlur = isSelected ? 25 : 15;
        ctx.fillStyle = isSelected ? 'rgba(30, 30, 30, 0.95)' : 'rgba(0, 0, 0, 0.9)';
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions, 4);
        } else {
            ctx.rect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
        }
        ctx.fill();

        ctx.shadowBlur = 0;

        // Border
        ctx.strokeStyle = isSelected ? '#ffffff' : node.color;
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.stroke();

        // Text
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, node.x, node.y);

        node.__bckgDimensions = bckgDimensions;
    }, [selectedNode]);

    const nodePointerAreaPaint = useCallback((node, color, ctx) => {
        ctx.fillStyle = color;
        const bckgDimensions = node.__bckgDimensions;
        bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
    }, []);

    const executeDeletion = async () => {
        if (!onDelete) return;
        setIsDeleting(true);
        try {
            if (selectedNode) {
                for (const id of selectedNode.memories) {
                    await onDelete(id);
                }
                setSelectedNode(null);
            } else if (selectedLink) {
                await onDelete(selectedLink.id);
                setSelectedLink(null);
            }
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <div ref={containerRef} className="w-full h-full bg-black/20 rounded-2xl overflow-hidden border border-white/5 relative">
            {dimensions.width > 0 && (
                <ForceGraph2D
                    ref={fgRef}
                    graphData={graphData}
                    width={dimensions.width}
                    height={dimensions.height}
                    nodeLabel="label"
                    linkLabel="label"
                    nodeCanvasObject={nodeCanvasObject}
                    nodePointerAreaPaint={nodePointerAreaPaint}
                    linkColor={link => selectedLink && selectedLink.id === link.id ? '#ffffff' : 'rgba(255, 255, 255, 0.12)'}
                    linkWidth={link => selectedLink && selectedLink.id === link.id ? 2 : 1}
                    linkDirectionalParticles={2}
                    linkDirectionalParticleSpeed={0.005}
                    linkDirectionalParticleWidth={1.5}
                    linkDirectionalParticleColor={() => '#a855f7'}
                    backgroundColor="rgba(0,0,0,0)"
                    showNavInfo={false}
                    onNodeClick={node => {
                        setSelectedNode(node);
                        setSelectedLink(null);
                    }}
                    onLinkClick={link => {
                        setSelectedLink(link);
                        setSelectedNode(null);
                    }}
                    onBackgroundClick={() => {
                        setSelectedNode(null);
                        setSelectedLink(null);
                    }}
                />
            )}

            {/* Selection Overlay */}
            {(selectedNode || selectedLink) && (
                <div className="absolute top-4 right-4 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="bg-black/80 border border-white/10 rounded-2xl p-4 flex items-center space-x-4 shadow-2xl">
                        <div className="flex flex-col">
                            <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1">
                                {selectedNode ? 'Network Node' : 'Logical Relation'}
                            </span>
                            <span className="text-sm font-medium text-white max-w-[200px] truncate">
                                {selectedNode ? selectedNode.label : `${selectedLink.source.label} ➔ ${selectedLink.target.label}`}
                            </span>
                            {selectedNode && (
                                <span className="text-[9px] text-white/30 font-mono mt-1">
                                    {selectedNode.memories.length} neural trace(s)
                                </span>
                            )}
                        </div>
                        <div className="flex items-center space-x-2 border-l border-white/10 pl-4">
                            <button
                                onClick={executeDeletion}
                                disabled={isDeleting}
                                className="p-2.5 bg-red-500/10 hover:bg-red-500/30 text-red-400 rounded-xl transition-all group disabled:opacity-50"
                                title="Delete Immediately"
                            >
                                {isDeleting ? (
                                    <div className="w-5 h-5 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
                                ) : (
                                    <Trash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                )}
                            </button>
                            <button
                                onClick={() => { setSelectedNode(null); setSelectedLink(null); }}
                                disabled={isDeleting}
                                className="p-2.5 hover:bg-white/10 text-white/40 hover:text-white rounded-xl transition-all disabled:opacity-50"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="absolute bottom-6 left-6 p-4 bg-black/70 rounded-2xl border border-white/10 flex flex-col space-y-3 pointer-events-none">
                <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full bg-[#818cf8] shadow-[0_0_10px_#818cf8]" />
                    <span className="text-[11px] uppercase tracking-wider text-white/90 font-mono">Subject</span>
                </div>
                <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full bg-[#4ade80] shadow-[0_0_10px_#4ade80]" />
                    <span className="text-[11px] uppercase tracking-wider text-white/90 font-mono">Object</span>
                </div>
                <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full bg-[#94a3b8] shadow-[0_0_10px_#94a3b8]" />
                    <span className="text-[11px] uppercase tracking-wider text-white/90 font-mono">Trace</span>
                </div>
            </div>
        </div>
    );
};

export default React.memo(MemoryGraph);
