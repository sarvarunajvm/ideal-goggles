import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, HashRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Disable context menu in production
if (process.env.NODE_ENV === 'production') {
  document.addEventListener('contextmenu', (e) => e.preventDefault())
}

const Router = process.env.NODE_ENV === 'production' ? HashRouter : BrowserRouter

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>,
)
