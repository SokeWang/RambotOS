
import React, { Suspense } from 'react';
import { useUI } from '../../context/UIContext';
import DynamicGenUI from './DynamicGenUI';
import VisionWindow from '../VisionWindow';
import { X } from 'lucide-react';

const GenUI = () => {
    const { genUI, setGenUI } = useUI();
    const { reactCode } = genUI;

    if (!reactCode || reactCode === 'none') return null;

    const handleClose = () => {
        setGenUI({ reactCode: null });
    };

    return (
        <VisionWindow
            name="NEURAL INTERFACE"
            onClose={handleClose}
            windowPos={{ x: 0, y: 0 }} // Default centered
            isDragging={false} // Internal dragging would need more state sharing
            startDragging={() => { }} // Placeholder for now
        >
            <div className="w-full flex flex-col items-center">
                {/* Content Container */}
                <div className="w-full max-h-[60vh] overflow-y-auto custom-scrollbar rounded-3xl p-6">
                    <Suspense fallback={
                        <div className="p-12 text-center bg-white/5 backdrop-blur-md border border-white/10 rounded-[3rem]">
                            <div className="text-white/60 font-black text-xs mb-4 tracking-[0.3em] uppercase">INITIALIZING NEURAL INTERFACE...</div>
                            <div className="h-1.5 w-64 bg-white/10 mx-auto rounded-full overflow-hidden relative">
                                <div className="h-full bg-cyan-400 animate-progress absolute left-0 top-0 shadow-[0_0_15px_rgba(34,211,238,0.5)]"></div>
                            </div>
                        </div>
                    }>
                        <DynamicGenUI code={reactCode} />
                    </Suspense>
                </div>
            </div>
        </VisionWindow>
    );
};

export default GenUI;
