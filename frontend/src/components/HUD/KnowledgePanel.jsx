import React, { useState, useEffect } from 'react';
import { useRambot } from '../../context/RambotContext';
import { Brain, Search, Trash2, Database, Clock, User, Bot, RefreshCw } from 'lucide-react';

export default function KnowledgePanel() {
    const { backend } = useRambot();
    const [memories, setMemories] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchMemories = async () => {
        if (!backend) return;
        setLoading(true);
        try {
            const raw = await backend.get_long_term_memory();
            const data = JSON.parse(raw);
            setMemories(data);
        } catch (e) {
            console.error("Failed to fetch memories:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMemories();
    }, [backend]);

    const handleDelete = async (id) => {
        if (!backend) return;
        const success = await backend.delete_memory(id);
        if (success) {
            setMemories(memories.filter(m => m.id !== id));
        }
    };

    const filteredMemories = memories.filter(m =>
        m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.role.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatDate = (timestamp) => {
        if (!timestamp) return 'Unknown';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    };

    return (
        <div className="flex flex-col h-full text-white font-sans overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/10 bg-white/5">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-purple-500/20 rounded-xl">
                        <Brain className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight">Neural Long-term Memory</h2>
                        <p className="text-xs text-white/40 font-mono uppercase tracking-widest mt-0.5">Neural Long-term Memory Bank</p>
                    </div>
                </div>
                <button
                    onClick={fetchMemories}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors group"
                    title="Refresh"
                >
                    <RefreshCw className={`w-5 h-5 text-white/60 group-hover:text-white ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* View Area */}
            <div className="flex-1 overflow-hidden flex flex-col p-6 space-y-6">
                {/* Search */}
                <div className="relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-purple-400 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search the memory core..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all text-sm placeholder:text-white/20"
                    />
                </div>

                {/* Memories List */}
                <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
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
                    ) : (
                        filteredMemories.map((mem) => (
                            <div
                                key={mem.id}
                                className="group relative bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 hover:border-purple-500/30 transition-all duration-300"
                            >
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex items-center space-x-2">
                                        <div className={`p-1.5 rounded-lg ${mem.role === 'user' ? 'bg-blue-500/20' : 'bg-green-500/20'}`}>
                                            {mem.role === 'user' ? <User className="w-3.5 h-3.5 text-blue-400" /> : <Bot className="w-3.5 h-3.5 text-green-400" />}
                                        </div>
                                        <span className={`text-[10px] font-bold uppercase tracking-widest ${mem.role === 'user' ? 'text-blue-400' : 'text-green-400'}`}>
                                            {mem.role === 'user' ? 'Individual' : 'Synthesized'}
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
                                <p className="text-sm text-white/80 leading-relaxed font-medium">
                                    {mem.content}
                                </p>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Footer Status */}
            {!loading && (
                <div className="p-4 bg-white/5 border-t border-white/10 flex justify-between items-center px-8">
                    <div className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.5)]" />
                        <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Index Synced</span>
                    </div>
                    <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">
                        {filteredMemories.length} Trace(s) Matched
                    </span>
                </div>
            )}
        </div>
    );
}
