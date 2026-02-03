import React, { useEffect, useCallback } from 'react';
import { X } from 'lucide-react';

/**
 * Modal Component - Full-screen modal with backdrop blur
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Modal open state
 * @param {Function} props.onClose - Close handler
 * @param {React.ReactNode} props.children - Modal content
 * @param {string} props.title - Optional modal title
 * @param {boolean} props.showCloseButton - Show close button (default: true)
 * @param {string} props.className - Additional CSS classes for content
 */
const Modal = React.memo(({
    isOpen,
    onClose,
    children,
    title,
    showCloseButton = true,
    className = ''
}) => {
    // Handle ESC key to close modal
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape' && isOpen && onClose) {
                onClose();
            }
        };

        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [isOpen, onClose]);

    const handleBackdropClick = useCallback((e) => {
        if (e.target === e.currentTarget && onClose) {
            onClose();
        }
    }, [onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xl"
            onClick={handleBackdropClick}
        >
            <div
                className={`
                    bg-black/40 border border-white/10
                    rounded-[2rem] p-8
                    backdrop-blur-3xl shadow-2xl
                    max-w-2xl w-full mx-4
                    animate-fade-in
                    ${className}
                `}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                {(title || showCloseButton) && (
                    <div className="flex items-center justify-between mb-6">
                        {title && (
                            <h2 className="text-2xl font-bold text-white tracking-wide">
                                {title}
                            </h2>
                        )}
                        {showCloseButton && (
                            <button
                                onClick={onClose}
                                className="p-2 rounded-xl hover:bg-white/10 text-white/60 hover:text-white transition-all"
                            >
                                <X size={24} />
                            </button>
                        )}
                    </div>
                )}

                {/* Content */}
                <div className="text-white">
                    {children}
                </div>
            </div>
        </div>
    );
});

Modal.displayName = 'Modal';

export default Modal;
