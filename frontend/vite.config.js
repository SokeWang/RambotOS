
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: './', // Crucial for file:// protocol loading in Qt
    build: {
        outDir: 'dist',
        rollupOptions: {
            output: {
                manualChunks: {
                    'vendor': [
                        'react',
                        'react-dom',
                        'framer-motion',
                        'lucide-react',
                        'zod'
                    ],
                }
            }
        },
        chunkSizeWarningLimit: 600,
    },
})
