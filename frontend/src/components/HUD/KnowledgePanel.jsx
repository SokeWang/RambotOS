import React, { useState, useEffect, useMemo } from 'react';
import { useRambot } from '../../context/RambotContext';
import { Brain, Search, Trash2, Database, Clock, User, Bot, RefreshCw, LayoutGrid, Network } from 'lucide-react';

const MemoryGraph = React.lazy(() => import('./MemoryGraph'));

export default function KnowledgePanel({ viewMode = 'list', refreshNonce = 0 }) {
    const { backend } = useRambot();
    const [memories, setMemories] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchMemories = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://127.0.0.1:8000/memory");
            if (res.ok) {
                const data = await res.json();
                setMemories(data);
            } else {
                setMemories([]);
            }
        } catch (e) {
            console.error("Failed to fetch memories:", e);
            setMemories([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMemories();
    }, [backend, refreshNonce]);

    const handleDelete = async (id) => {
        try {
            const res = await fetch(`http://127.0.0.1:8000/memory/${id}`, { method: 'DELETE' });
            if (res.ok) {
                setMemories(memories.filter(m => m.id !== id));
            }
        } catch (e) {
            console.error("Failed to delete memory:", e);
        }
    };

    const filteredMemories = useMemo(() => {
        return memories.filter(m => {
            const text = m.text || m.content || "";
            const role = m.role || "fact";
            const subject = m.subject || "";
            const predicate = m.predicate || "";
            const obj = m.object || "";

            const search = searchQuery.toLowerCase();
            return (
                text.toLowerCase().includes(search) ||
                role.toLowerCase().includes(search) ||
                subject.toLowerCase().includes(search) ||
                predicate.toLowerCase().includes(search) ||
                obj.toLowerCase().includes(search)
            );
        });
    }, [memories, searchQuery]);

    const formatDate = (timestamp) => {
        if (!timestamp) return 'Unknown';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    };

    return (
        <div className="flex flex-col h-full text-white font-sans overflow-hidden bg-white/5">

            {/* View Area */}
            <div className="flex-1 overflow-hidden flex flex-col">
                {/* Search (Hide in Graph Mode to maximize space) */}
                {viewMode !== 'graph' && (
                    <div className="relative group px-6 pt-6">
                        <Search className="absolute left-10 top-1/2 -translate-y-1/2 mt-3 w-5 h-5 text-white/30 group-focus-within:text-purple-400 transition-colors" />
                        <input
                            type="text"
                            placeholder="Search the memory core..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all text-sm placeholder:text-white/20"
                        />
                    </div>
                )}

                {/* Content Area */}
                <div className={`flex-1 overflow-hidden ${viewMode !== 'graph' ? 'mt-6' : ''}`}>
                    {loading ? (
                        <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
                            <div className="w-12 h-12 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                            <p className="text-sm font-mono tracking-widest uppercase">Synchronizing Neural Data...</p>
                        </div>
                    ) : filteredMemories.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-30 text-center px-12">
                            <Database className="w-16 h-16" />
                            <p className="text-sm font-mono tracking-widest uppercase">No relevant neural traces found in the memory bank.</p>
                        </div>
                    ) : viewMode === 'graph' ? (
                        <React.Suspense fallback={
                            <div className="h-full flex items-center justify-center">
                                <RefreshCw className="w-8 h-8 text-purple-500 animate-spin" />
                            </div>
                        }>
                            <MemoryGraph memories={filteredMemories} onDelete={handleDelete} />
                        </React.Suspense>
                    ) : (
                        <div className="h-full overflow-y-auto px-6 pb-6 custom-scrollbar relative">
                            {/* Mask gradient at bottom to softly fade out text if user wants, but currently we just let it bleed */}
                            <div className="space-y-4 pr-2">
                                {filteredMemories.map((mem) => (
                                    <div
                                        key={mem.id}
                                        className="group relative bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 hover:border-purple-500/30 transition-all duration-300"
                                    >
                                        <div className="flex justify-between items-start mb-3">
                                            <div className="flex items-center space-x-2">
                                                <div className={`p-1.5 rounded-lg ${(mem.role === 'user' || !mem.subject) ? 'bg-blue-500/20' : 'bg-purple-500/20'}`}>
                                                    {(mem.role === 'user' || !mem.subject) ? <User className="w-3.5 h-3.5 text-blue-400" /> : <Database className="w-3.5 h-3.5 text-purple-400" />}
                                                </div>
                                                <span className={`text-[10px] font-bold uppercase tracking-widest ${(mem.role === 'user' || !mem.subject) ? 'text-blue-400' : 'text-purple-400'}`}>
                                                    {mem.role === 'user' ? 'Logged Event' : (mem.subject ? 'Extracted Fact' : 'Memory Trace')}
                                                </span>
                                            </div>
                                            <div className="flex items-center space-x-3">
                                                <div className="flex items-center space-x-1.5 text-white/20 font-mono text-[9px]">
                                                    <Clock className="w-3 h-3" />
                                                    <span>{formatDate(mem.timestamp)}</span>
                                                </div>
                                                <button
                                                    onClick={() => handleDelete(mem.id)}
                                                    className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg transition-all text-white/20 hover:text-red-400"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                        {mem.subject && mem.predicate && mem.object ? (
                                            <div className="flex flex-wrap items-center gap-2 p-3 bg-white/5 rounded-xl border border-white/5">
                                                <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded text-xs font-mono">{mem.subject}</span>
                                                <span className="text-white/30 text-[10px] uppercase font-bold tracking-tighter">{mem.predicate}</span>
                                                <span className="px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-xs font-mono">{mem.object}</span>
                                            </div>
                                        ) : (
                                            <p className="text-sm text-white/80 leading-relaxed font-medium">
                                                {mem.text || mem.content}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
}
