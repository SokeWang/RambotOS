
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
// Initialize Lucide icons globally if needed - REMOVED as we use lucide-react now
// window.lucide = { createIcons, icons };

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)
