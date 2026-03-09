import React from 'react';

/**
 * Card Component - Glassmorphic card container
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Card content
 * @param {string} props.title - Optional card title
 * @param {'default'|'dark'|'light'} props.variant - Card style variant
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onClick - Optional click handler
 */
const Card = React.memo(({
    children,
    title,
    variant = 'default',
    className = '',
    onClick,
    ...props
}) => {
    const variants = {
        default: 'bg-white/5 border-white/10',
        dark: 'bg-black/20 border-white/5',
        light: 'bg-white/10 border-white/20'
    };

    return (
        <div
            className={`
                ${variants[variant]}
                border rounded-[2rem] p-6 shadow-2xl
                transition-all duration-300
                ${onClick ? 'cursor-pointer hover:bg-white/10 hover:border-white/20' : ''}
                ${className}
            `}
            onClick={onClick}
            {...props}
        >
            {title && (
                <h3 className="text-lg font-bold text-white mb-4 tracking-wide">
                    {title}
                </h3>
            )}
            {children}
        </div>
    );
});

Card.displayName = 'Card';

export default Card;
