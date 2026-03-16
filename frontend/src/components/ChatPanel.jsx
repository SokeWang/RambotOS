
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Bot, MessageSquare, Paperclip, File, Send, Film, Music, X, Terminal, ChevronDown, ChevronRight, Plus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useRambot } from '../context/RambotContext';

// ============================================================================
// CHAT IMAGE COMPONENT - Small thumbnail with click-to-expand
// ============================================================================
const ChatImage = ({ src, alt }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div 
            onClick={() => setIsExpanded(!isExpanded)}
            className={`mt-3 rounded-2xl overflow-hidden border border-white/10 flex justify-center bg-black/40 shadow-inner cursor-pointer transition-all duration-500 ease-in-out group relative ${
                isExpanded ? 'max-h-[600px] w-full' : 'max-h-[120px] w-[180px]'
            }`}
        >
            <img 
                src={src} 
                alt={alt} 
                className={`max-w-full max-h-full object-contain ${
                    !isExpanded ? 'hover:scale-110' : ''
                } transition-transform duration-700`} 
            />
            
            {!isExpanded && (
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="bg-white/20 rounded-full p-2 text-white">
                        <Plus size={16} />
                    </div>
                </div>
            )}
        </div>
    );
};

// ============================================================================
// TOOL GROUP COMPONENT - Horizontal chips when collapsed, vertical details when expanded
// ============================================================================
const ToolGroup = ({ toolCalls }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!toolCalls || toolCalls.length === 0) return null;

    return (
        <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
            <div className="flex flex-wrap gap-2">
                {/* Entire group toggle button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all border ${
                        isExpanded 
                        ? 'bg-white/10 border-white/20 text-white/90' 
                        : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10 hover:text-white'
                    }`}
                >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span className="text-[10px] font-bold uppercase tracking-wider font-mono">
                        {isExpanded ? 'Hide Technical Details' : `${toolCalls.length} Tool ${toolCalls.length > 1 ? 'Calls' : 'Call'}`}
                    </span>
                </button>

                {/* Horizontal chips (only when collapsed) */}
                {!isExpanded && toolCalls.map((call, i) => (
                    <div 
                        key={i} 
                        className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-xl border border-white/10 animate-in fade-in zoom-in-95 duration-200"
                    >
                        <Terminal size={10} className="text-white/70" />
                        <span className="text-[10px] font-mono text-white/70">{call.name}</span>
                        <div className={`w-1 h-1 rounded-full ${
                            call.status === 'success' ? 'bg-green-500/50' : 
                            (call.status === 'error' ? 'bg-red-500/50' : 'bg-cyan-500/50 animate-pulse')
                        }`} />
                    </div>
                ))}
            </div>

            {/* Detailed vertical list (only when expanded) */}
            {isExpanded && (
                <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    {toolCalls.map((call, i) => (
                        <div key={i} className="bg-white/5 rounded-[1.5rem] p-4 border border-white/10 space-y-3 shadow-lg">
                            <div className="flex items-center gap-2">
                                <div className="p-1.5 bg-white/10 rounded-lg border border-white/10">
                                    <Terminal size={12} className="text-white/80" />
                                </div>
                                <span className="text-[10px] font-bold text-white/80 uppercase tracking-wider font-mono">
                                    {call.name}
                                </span>
                                <div className={`ml-auto w-1.5 h-1.5 rounded-full ${
                                    call.status === 'success' ? 'bg-green-500/50' : 
                                    (call.status === 'error' ? 'bg-red-500/50' : 'bg-cyan-500/50 animate-pulse')
                                }`} />
                            </div>
                            
                            {call.input && (
                                <div className="space-y-1">
                                    <div className="text-[9px] text-white/30 font-mono uppercase tracking-tighter px-1">Arguments</div>
                                    <div className="font-mono text-[9px] text-white/50 bg-white/[0.02] rounded-xl p-3 border border-white/5 whitespace-pre-wrap">
                                        {call.input}
                                    </div>
                                </div>
                            )}
                            
                            {call.output && (
                                <div className="space-y-1">
                                    <div className="text-[9px] text-white/30 font-mono uppercase tracking-tighter px-1">Result</div>
                                    <div className="bg-white/[0.02] rounded-xl p-3 font-mono text-[10px] text-white/60 max-h-[200px] overflow-y-auto whitespace-pre-wrap border border-white/5 shadow-inner">
                                        {call.output}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// ============================================================================
// OPTIMIZED MESSAGE COMPONENT - Prevents re-renders when message unchanged
// ============================================================================
const ChatMessage = React.memo(({ msg, idx }) => {
    return (
        <div className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} group transition-transform duration-500 hover:scale-[1.01] hover:-translate-y-0.5`}>
            <div className={`max-w-[85%] p-5 rounded-[2rem] ${msg.type === 'user'
                ? 'bg-white/20 border border-white/20 text-white shadow-xl'
                : 'bg-white/5 border border-white/10 text-gray-100 shadow-lg'
                } transition-shadow duration-500 group-hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)]`}>
                {msg.attachment && (
                    <div className="mb-3 p-2 bg-white/10 rounded-xl border border-white/10 flex items-center space-x-3">
                        <Paperclip className="w-3.5 h-3.5 text-white/70" />
                        <span className="text-xs text-white/90 truncate max-w-[200px]">{msg.attachment.split('/').pop()}</span>
                    </div>
                )}
                <div className="text-base leading-relaxed space-y-2">
                    {Array.isArray(msg.content) ? (
                        msg.content.map((block, i) => {
                            if (block.type === 'text') {
                                return (
                                    <div key={i} className="markdown-content">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {block.text}
                                        </ReactMarkdown>
                                    </div>
                                );
                            }

                            if (block.type === 'image' || block.type === 'image_url') {
                                if (msg.type === 'user' && msg.webcamNeeded === false) return null;

                                const src = block.type === 'image'
                                    ? `data:${block.mime_type || 'image/jpeg'};base64,${block.base64}`
                                    : block.image_url?.url || block.url;
                                return <ChatImage key={i} src={src} alt="Captured" />;
                            }

                            if (block.type === 'file') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/10 rounded-xl border border-white/10 mt-3 hover:bg-white/20 transition-colors cursor-pointer">
                                        <File className="w-5 h-5 text-white/80" />
                                        <span className="text-sm text-white/90 truncate">{block.name || 'File'}</span>
                                    </div>
                                );
                            }

                            if (block.type === 'video') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/10 rounded-xl border border-white/10 mt-3">
                                        <Film className="w-5 h-5 text-white/80" />
                                        <span className="text-sm text-white/90 italic">[Video Analysis]</span>
                                    </div>
                                );
                            }

                            if (block.type === 'audio') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/10 rounded-xl border border-white/10 mt-3">
                                        <Music className="w-5 h-5 text-white/80" />
                                        <span className="text-sm text-white/90 italic">[Audio Processed]</span>
                                    </div>
                                );
                            }

                            return null;
                        })
                    ) : (
                        <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>

                <ToolGroup toolCalls={msg.tool_calls} />

                <span className="text-[10px] opacity-40 block mt-2 text-right font-mono tracking-tighter">
                    {msg.time && new Date(msg.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
        </div>
    );
}, (prevProps, nextProps) => {
    // Only re-render if message content actually changed
    return prevProps.msg === nextProps.msg;
});

ChatMessage.displayName = 'ChatMessage';

// ============================================================================
// MAIN CHAT PANEL COMPONENT - Optimized with useCallback and useMemo
// ============================================================================
function ChatPanel({ chatHistory }) {
    const { loadMoreHistory, hasMoreHistory, historyOffset } = useRambot();
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const scrollContainerRef = useRef(null);
    const lastScrollHeightRef = useRef(0);
    const isPaginationLoadingRef = useRef(false);

    // Memoize messages array to prevent unnecessary re-renders
    const messages = useMemo(() => {
        return Array.isArray(chatHistory) ? chatHistory : [];
    }, [chatHistory]);

    // Handle scroll to detect top reach
    const handleScroll = useCallback((e) => {
        const { scrollTop } = e.currentTarget;
        if (scrollTop < 50 && hasMoreHistory && !isPaginationLoadingRef.current && messages.length >= 20) {
            console.log("Reached top, loading more history...");
            isPaginationLoadingRef.current = true;
            setIsLoadingMore(true);
            lastScrollHeightRef.current = e.currentTarget.scrollHeight;
            loadMoreHistory();
        }
    }, [hasMoreHistory, loadMoreHistory, messages.length]);

    // Reset pagination loading flag when historyOffset changes
    useEffect(() => {
        isPaginationLoadingRef.current = false;
        setIsLoadingMore(false);

        // Scroll Anchoring: If we just loaded more, maintain scroll position
        if (lastScrollHeightRef.current > 0 && scrollContainerRef.current) {
            const container = scrollContainerRef.current;
            const newScrollHeight = container.scrollHeight;
            const heightDiff = newScrollHeight - lastScrollHeightRef.current;
            if (heightDiff > 0) {
                container.scrollTop = heightDiff;
            }
            lastScrollHeightRef.current = 0;
        }
    }, [historyOffset]);

    // Auto-scroll effect for NEW messages
    useEffect(() => {
        if (messages.length > 0 && scrollContainerRef.current) {
            const container = scrollContainerRef.current;

            // Only auto-scroll to bottom if we are NOT in a pagination load
            if (!isPaginationLoadingRef.current && lastScrollHeightRef.current === 0) {
                // Increased threshold to 250 for better reliability during streaming
                const threshold = 250;
                const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
                
                const lastMsg = messages[messages.length - 1];
                const isUserMsg = lastMsg?.type === 'user';

                // Always scroll on user message, or if already near bottom for AI messages
                if (isNearBottom || isUserMsg) {
                    requestAnimationFrame(() => {
                        container.scrollTo({
                            top: container.scrollHeight,
                            behavior: isUserMsg ? 'instant' : 'smooth'
                        });
                    });
                }
            }
        }
    }, [messages]);

    const handleStopPropagation = useCallback((e) => {
        e.stopPropagation();
    }, []);

    return (
        <div className="flex flex-col h-full w-full relative" onClick={handleStopPropagation}>
            {/* Messages Area */}
            <div
                ref={scrollContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4 relative z-10"
                style={{ maskImage: 'linear-gradient(to bottom, transparent, black 4%, black 96%, transparent)', WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 4%, black 96%, transparent)' }}
            >
                {isLoadingMore && (
                    <div className="flex justify-center p-4">
                        <div className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                    </div>
                )}
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-cyan-500/30">
                        <MessageSquare className="w-16 h-16 mb-4 opacity-20" />
                        <p className="text-sm font-mono tracking-widest uppercase opacity-40">Encrypted Channel Ready</p>
                    </div>
                )}
                {messages.map((msg, idx) => {
                    // Stable key: type+time ensures key is unaffected by prepend (idx shifts)
                    const stableKey = msg._id ||
                        `${msg.type}-${msg.time instanceof Date ? msg.time.getTime() : (msg.time || idx)}`;
                    return <ChatMessage key={stableKey} msg={msg} idx={idx} />;
                })}
            </div>
        </div>
    );
}

// Export with React.memo for additional optimization
export default React.memo(ChatPanel);
