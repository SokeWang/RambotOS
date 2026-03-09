import React, { useState, useCallback, useMemo } from 'react';
import { Mic, LayoutGrid, Paperclip, Send, File, X } from 'lucide-react';
import { useRambot } from '../context/RambotContext';
import { useUI } from '../context/UIContext';

export default function Dock({ triggerSystemAction }) {
    const [inputValue, setInputValue] = useState('');
    const { 
        isListening, toggleListening, 
        processCommand, attachment, selectFile, setAttachment 
    } = useRambot();
    const { setShowChatbox, showAppLauncher } = useUI();

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

    const isSendDisabled = useMemo(() => {
        return !inputValue.trim() && !attachment;
    }, [inputValue, attachment]);

    return (
        <div className="flex justify-center w-full mb-4 pointer-events-auto">
            {/* Dock Container with Siri Glow */}
            <div className="relative">
                {/* Apple Intelligence Rainbow Glow (Active when listening) */}
                {isListening && (
                    <>
                        {/* 1. Remote Ambient Glow (Lush, soft background) */}
                        <div className="absolute inset-[-20px] blur-3xl opacity-30 rounded-[5rem] animate-siri-fluid bg-gradient-to-r from-[#5ac8fa] via-[#5856d6] via-[#af52bf] via-[#ff2d55] via-[#ff9500] to-[#5ac8fa] bg-[length:400%_400%]" />

                        {/* 2. The "Outer Ring" (Sharp flowing edge via masking) */}
                        <div
                            className="absolute inset-[-3px] p-[3px] rounded-[3.8rem] animate-siri-fluid bg-gradient-to-r from-[#5ac8fa] via-[#5856d6] via-[#af52bf] via-[#ff2d55] via-[#ff9500] to-[#5ac8fa] bg-[length:400%_400%]"
                            style={{
                                WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                                WebkitMaskComposite: 'xor',
                                maskComposite: 'exclude',
                            }}
                        />
                    </>
                )}

                {/* Dock Nav */}
                <nav className="relative flex items-center gap-3 p-3 bg-white/10 rounded-[3.5rem] border-t border-white/30 border border-white/10 shadow-[0_30px_100px_rgba(0,0,0,0.5)]">

                    {/* AI / Voice Button (The Centerpiece) */}
                    <button
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            toggleListening();
                        }}
                        className={`mx-2 p-5 rounded-full transition-all duration-[400ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] relative overflow-hidden group hover:-translate-y-1 hover:scale-105
                        ${isListening ? 'bg-white/20 shadow-[0_0_30px_rgba(255,255,255,0.3)] scale-110' : 'hover:bg-white/10 shadow-lg'}`}
                    >
                        {isListening && (
                            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/40 via-purple-500/40 to-cyan-400/40 animate-pulse" />
                        )}
                        <div className="relative z-10 flex items-center justify-center">
                            {isListening ? (
                                <div className="flex items-center gap-1.5 h-6">
                                    {[...Array(3)].map((_, i) => (
                                        <div
                                            key={i}
                                            className="w-1.5 bg-white rounded-full animate-bounce shadow-[0_0_10px_white]"
                                            style={{
                                                height: `${70 + Math.random() * 30}%`,
                                                animationDuration: `${0.4 + i * 0.1}s`,
                                                animationDelay: `${i * 0.1}s`
                                            }}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <Mic size={24} className="text-white/40 group-hover:text-white transition-all" />
                            )}
                        </div>
                    </button>

                    {/* App Launcher Toggle */}
                    <button
                        data-gaze-target="true"
                        onClick={(e) => {
                            e.stopPropagation();
                            triggerSystemAction('TOGGLE_LAUNCHER');
                        }}
                        className={`p-2 rounded-full transition-all duration-[400ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] group hover:-translate-y-0.5 hover:scale-110 ${showAppLauncher ? 'bg-white/20 shadow-lg' : 'hover:bg-white/10'}`}>
                        <LayoutGrid size={22} className={`${showAppLauncher ? 'text-white' : 'text-white/40 group-hover:text-white'} transition-colors`} />
                    </button>


                    {/* Input Area (New Integrated) - Expanded Proportion */}
                    <div 
                        data-gaze-target="true"
                        onClick={(e) => {
                            if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                                const input = e.currentTarget.querySelector('input');
                                if (input) input.focus();
                            }
                        }}
                        className="flex items-center gap-3 bg-white/10 rounded-full px-5 py-2 border border-white/10 focus-within:border-white/30 transition-all min-w-[500px] lg:min-w-[700px] shadow-inner cursor-text"
                    >
                        <button
                            onClick={selectFile}
                            className="p-1.5 rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-all"
                        >
                            <Paperclip size={18} />
                        </button>
                        
                        <div className="relative flex-1 flex items-center">
                            {attachment && (
                                <div className="absolute left-0 bg-white/10 px-2 py-0.5 rounded-md border border-white/20 flex items-center gap-2 animate-in fade-in slide-in-from-left-2">
                                    <File size={10} className="text-white/80" />
                                    <span className="text-[10px] text-white/90 font-medium max-w-[80px] truncate">
                                        {attachment.split('/').pop()}
                                    </span>
                                    <button onClick={() => setAttachment(null)} className="text-white/50 hover:text-red-400">
                                        <X size={10} />
                                    </button>
                                </div>
                            )}
                            <input
                                data-gaze-ignore="true"
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={attachment ? "" : "Communication input..."}
                                className={`bg-transparent border-none outline-none text-white placeholder-white/20 px-2 py-1 text-sm w-full font-medium ${attachment ? 'pl-24' : ''}`}
                            />
                        </div>

                        <button
                            onClick={handleSend}
                            disabled={isSendDisabled}
                            className={`p-1.5 rounded-full transition-all duration-[400ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] ${isSendDisabled ? 'text-white/10' : 'text-white/80 hover:scale-110 active:scale-95 hover:-translate-y-0.5'}`}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </nav>
            </div>
        </div>
    );
}
