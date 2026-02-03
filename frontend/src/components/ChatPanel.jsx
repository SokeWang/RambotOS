
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Bot, MessageSquare, Paperclip, File, Send, Film, Music, X, Terminal } from 'lucide-react';

// ============================================================================
// OPTIMIZED MESSAGE COMPONENT - Prevents re-renders when message unchanged
// ============================================================================
const ChatMessage = React.memo(({ msg, idx }) => {
    return (
        <div className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-5 rounded-[2rem] ${msg.type === 'user'
                ? 'bg-white/10 border border-white/10 text-white rounded-tr-none'
                : 'bg-black/20 border border-white/5 text-gray-200 rounded-tl-none'
                } shadow-xl backdrop-blur-md`}>
                {msg.attachment && (
                    <div className="mb-3 p-2 bg-black/30 rounded-xl border border-cyan-500/20 flex items-center space-x-3">
                        <Paperclip className="w-3.5 h-3.5 text-cyan-400" />
                        <span className="text-xs text-cyan-200 truncate max-w-[200px]">{msg.attachment.split('/').pop()}</span>
                    </div>
                )}
                <div className="text-base leading-relaxed space-y-2">
                    {Array.isArray(msg.content) ? (
                        msg.content.map((block, i) => {
                            if (block.type === 'text') return <div key={i}>{block.text}</div>;

                            if (block.type === 'image' || block.type === 'image_url') {
                                if (msg.type === 'user' && msg.webcamNeeded === false) return null;

                                const src = block.type === 'image'
                                    ? `data:${block.mime_type || 'image/jpeg'};base64,${block.base64}`
                                    : block.image_url?.url || block.url;
                                return (
                                    <div key={i} className="mt-3 rounded-2xl overflow-hidden border border-white/10 max-h-[400px] flex justify-center bg-black/40 shadow-inner">
                                        <img src={src} alt="Captured" className="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-500" />
                                    </div>
                                );
                            }

                            if (block.type === 'file') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/5 rounded-xl border border-white/10 mt-3 hover:bg-white/10 transition-colors cursor-pointer">
                                        <File className="w-5 h-5 text-cyan-400" />
                                        <span className="text-sm text-cyan-100 truncate">{block.name || 'File'}</span>
                                    </div>
                                );
                            }

                            if (block.type === 'video') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/5 rounded-xl border border-white/10 mt-3">
                                        <Film className="w-5 h-5 text-cyan-400" />
                                        <span className="text-sm text-cyan-100 italic">[Video Analysis]</span>
                                    </div>
                                );
                            }

                            if (block.type === 'audio') {
                                return (
                                    <div key={i} className="flex items-center space-x-3 p-3 bg-white/5 rounded-xl border border-white/10 mt-3">
                                        <Music className="w-5 h-5 text-cyan-400" />
                                        <span className="text-sm text-cyan-100 italic">[Audio Processed]</span>
                                    </div>
                                );
                            }

                            return null;
                        })
                    ) : (
                        typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
                    )}
                </div>

                {msg.tool_calls && msg.tool_calls.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
                        {msg.tool_calls.map((call, i) => (
                            <div key={i} className="bg-black/30 rounded-[1.5rem] p-4 border border-white/5">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="p-1.5 bg-cyan-500/10 rounded-lg">
                                        <Terminal size={12} className="text-cyan-400" />
                                    </div>
                                    <span className="text-[10px] font-bold text-cyan-400/80 uppercase tracking-wider font-mono">
                                        {call.name}
                                    </span>
                                    <div className={`ml-auto w-1.5 h-1.5 rounded-full ${call.status === 'success' ? 'bg-green-500/50' : (call.status === 'error' ? 'bg-red-500/50' : 'bg-cyan-500/50 animate-pulse')}`} />
                                </div>
                                {call.input && (
                                    <div className="font-mono text-[9px] text-white/30 truncate px-1">
                                        IN: {call.input}
                                    </div>
                                )}
                                {call.output && (
                                    <div className="mt-2 bg-white/[0.02] rounded-xl p-3 font-mono text-[10px] text-white/50 max-h-[120px] overflow-y-auto whitespace-pre-wrap border border-white-[0.05] shadow-inner">
                                        {call.output}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

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
function ChatPanel({ chatHistory, processCommand, attachment, triggerSelectFile, clearAttachment }) {
    const [inputValue, setInputValue] = useState('');
    const scrollContainerRef = useRef(null);

    // Memoize messages array to prevent unnecessary re-renders
    const messages = useMemo(() => {
        return Array.isArray(chatHistory) ? chatHistory : [];
    }, [chatHistory]);

    // Auto-scroll effect
    useEffect(() => {
        if (messages.length > 0 && scrollContainerRef.current) {
            const container = scrollContainerRef.current;
            requestAnimationFrame(() => {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth'
                });
            });
        }
    }, [messages.length]);

    // Memoize event handlers to prevent child re-renders
    const handleSend = useCallback(() => {
        if (inputValue.trim() || attachment) {
            processCommand(inputValue);
            setInputValue('');
        }
    }, [inputValue, attachment, processCommand]);

    const handleKeyPress = useCallback((e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    }, [handleSend]);

    const handleInputChange = useCallback((e) => {
        setInputValue(e.target.value);
    }, []);

    const handleStopPropagation = useCallback((e) => {
        e.stopPropagation();
    }, []);

    // Memoize send button state
    const isSendDisabled = useMemo(() => {
        return !inputValue.trim() && !attachment;
    }, [inputValue, attachment]);

    const sendButtonClass = useMemo(() => {
        return `p-3 rounded-2xl transition-all ${inputValue.trim() || attachment
            ? 'bg-cyan-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.4)]'
            : 'bg-white/5 text-white/10 cursor-not-allowed'
            }`;
    }, [inputValue, attachment]);

    return (
        <div className="flex flex-col h-full w-full relative" onClick={handleStopPropagation}>
            {/* Messages Area */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4"
            >
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-cyan-500/30">
                        <MessageSquare className="w-16 h-16 mb-4 opacity-20" />
                        <p className="text-sm font-mono tracking-widest uppercase opacity-40">Encrypted Channel Ready</p>
                    </div>
                )}
                {messages.map((msg, idx) => (
                    <ChatMessage key={`${idx}-${msg.time}`} msg={msg} idx={idx} />
                ))}
            </div>

            {/* Input Area */}
            <div className="p-8 pt-0 z-20 flex flex-col justify-end">
                {attachment && (
                    <div className="mb-4 w-fit bg-cyan-500/10 p-1.5 px-4 rounded-full border border-cyan-500/30 flex items-center space-x-3 animate-fade-in mx-auto backdrop-blur-md">
                        <File className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs text-white/90 font-medium max-w-[250px] truncate">{attachment.split('/').pop()}</span>
                        <button onClick={clearAttachment} className="hover:text-red-400 text-cyan-400 transition-colors">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                )}
                <div className="flex items-center space-x-4 bg-white/5 p-3 rounded-[2rem] border border-white/10 w-full shadow-2xl backdrop-blur-3xl group focus-within:border-white/20 transition-all">
                    <button
                        onClick={triggerSelectFile}
                        className="p-3 rounded-2xl hover:bg-white/10 text-white/40 hover:text-white transition-all"
                        title="Upload System Data"
                    >
                        <Paperclip size={20} />
                    </button>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyPress={handleKeyPress}
                        placeholder="Communication input..."
                        className="flex-1 bg-transparent border-none outline-none text-white placeholder-white/20 px-2 py-2 font-medium text-base"
                    />
                    <button
                        onClick={handleSend}
                        className={sendButtonClass}
                        disabled={isSendDisabled}
                    >
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
}

// Export with React.memo for additional optimization
export default React.memo(ChatPanel);
