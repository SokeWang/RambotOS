
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: './', // Crucial for file:// protocol loading in Qt
    build: {
        outDir: 'dist',
        content: [
            "./index.html",
            "./src/**/*.{js,ts,jsx,tsx}",
        ],
    },
})
