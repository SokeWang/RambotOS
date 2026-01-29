import React, { useState, useEffect, useMemo } from 'react';
import * as Babel from '@babel/standalone';
import * as LucideIcons from 'lucide-react';
import * as FramerMotion from 'framer-motion';
import * as JsonRenderReact from '@json-render/react';
import * as JsonRenderCore from '@json-render/core';

const DynamicGenUI = ({ code }) => {
    const [Component, setComponent] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!code) return;

        try {
            // 1. Transpile JSX/ES6 to ES5 with CommonJS modules
            const transpiled = Babel.transform(code, {
                presets: ['react'],
                plugins: [
                    ['transform-modules-commonjs'],
                    // Mock imports for React and Lucide
                    (babel) => ({
                        visitor: {
                            ImportDeclaration(path) {
                                path.remove();
                            }
                        }
                    })
                ]
            }).code;

            // 2. Create a function that returns the component
            const runtimeCode = `
                const { useState, useEffect, useMemo, useCallback, useRef } = React;
                // Filter out non-component keys from LucideIcons if necessary
                const { ${Object.keys(LucideIcons).filter(k => /^[A-Z]/.test(k)).join(', ')} } = LucideIcons;
                const { motion, AnimatePresence } = FramerMotion;
                const { Renderer, DataProvider, ActionProvider } = JsonRenderReact;
                const { createCatalog } = JsonRenderCore;
                
                const exports = {};
                const module = { exports };
                
                (function(exports, module) {
                    ${transpiled}
                })(exports, module);
                
                return module.exports.default || module.exports;
            `;

            const renderFunc = new Function('React', 'LucideIcons', 'FramerMotion', 'JsonRenderReact', 'JsonRenderCore', runtimeCode);
            const DynamicComponent = renderFunc(React, LucideIcons, FramerMotion, JsonRenderReact, JsonRenderCore);

            if (typeof DynamicComponent !== 'function') {
                throw new Error('Generated code must export a default functional component.');
            }

            setComponent(() => DynamicComponent);
            setError(null);
        } catch (err) {
            console.error('[DynamicGenUI] Transpilation Error:', err);
            setError(err.message);
        }
    }, [code]);

    if (error) {
        return (
            <div className="glass-panel p-4 border border-red-500/50 rounded-xl bg-red-900/20 text-red-400 font-mono text-xs">
                <div className="font-bold mb-2">DYNAMIC RENDER ERROR:</div>
                <div className="whitespace-pre-wrap">{error}</div>
            </div>
        );
    }

    if (!Component) {
        return <div className="animate-pulse text-cyan-300 font-mono text-xs text-center p-4">Assembling Holographic Interface...</div>;
    }

    return (
        <div className="relative pointer-events-auto">
            <Component />
        </div>
    );
};

export default DynamicGenUI;
