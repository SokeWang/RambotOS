import React, { useCallback } from 'react';

/**
 * Input Component - Styled text input with VisionOS aesthetics
 * 
 * @param {Object} props
 * @param {string} props.value - Input value
 * @param {Function} props.onChange - Change handler
 * @param {string} props.placeholder - Placeholder text
 * @param {'text'|'password'|'email'|'number'} props.type - Input type
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onKeyPress - Key press handler
 */
const Input = React.memo(({
    value,
    onChange,
    placeholder = '',
    type = 'text',
    disabled = false,
    className = '',
    onKeyPress,
    ...props
}) => {
    const handleChange = useCallback((e) => {
        if (onChange) {
            onChange(e);
        }
    }, [onChange]);

    return (
        <input
            type={type}
            value={value}
            onChange={handleChange}
            onKeyPress={onKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className={`
                bg-white/5 border border-white/10
                rounded-2xl px-4 py-3
                text-white placeholder-white/30
                outline-none
                transition-all duration-200
                focus:border-white/30 focus:bg-white/10
                disabled:opacity-50 disabled:cursor-not-allowed
                backdrop-blur-md
                ${className}
            `}
            {...props}
        />
    );
});

Input.displayName = 'Input';

export default Input;
