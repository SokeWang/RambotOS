import React from 'react';
import { UIProvider, useUI } from './UIContext';
import { RambotProvider, useRambot } from './RambotContext';

// Re-export for convenience
export { useUI } from './UIContext';
export { useRambot } from './RambotContext';

// Backward compatibility hook
export const useGlobal = () => {
    return {
        ...useUI(),
        ...useRambot()
    };
};

export const GlobalProvider = ({ children }) => {
    return (
        <UIProvider>
            <RambotProvider>
                {children}
            </RambotProvider>
        </UIProvider>
    );
};

