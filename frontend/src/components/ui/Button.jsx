import React from 'react';

/**
 * Button Component - Optimized, reusable button with VisionOS styling
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Button content
 * @param {'primary'|'secondary'|'ghost'|'danger'} props.variant - Button style variant
 * @param {'sm'|'md'|'lg'} props.size - Button size
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.className - Additional CSS classes
 */
const Button = React.memo(({
    children,
    variant = 'primary',
    size = 'md',
    onClick,
    disabled = false,
    className = '',
    ...props
}) => {
    const variants = {
        primary: 'bg-cyan-500 hover:bg-cyan-600 text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_rgba(34,211,238,0.6)]',
        secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20',
        ghost: 'bg-transparent hover:bg-white/10 text-white border border-white/20 hover:border-white/30',
        danger: 'bg-red-500/80 hover:bg-red-600 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
    };

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg'
    };

    return (
        <button
            className={`
                ${variants[variant]}
                ${sizes[size]}
                rounded-2xl font-medium
                transition-all duration-200
                disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
                ${className}
            `}
            onClick={onClick}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
});

Button.displayName = 'Button';

export default Button;
