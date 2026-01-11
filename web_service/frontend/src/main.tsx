import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found')
}

try {
  const root = createRoot(rootElement)
  
  root.render(
    <StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </StrictMode>
  )
} catch (error) {
  console.error('❌ Error rendering app:', error)
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 20px; font-family: Arial; color: red;">
        <h1>❌ Ошибка загрузки приложения</h1>
        <p>${error instanceof Error ? error.message : String(error)}</p>
        <p>Проверьте консоль браузера (F12) для подробностей.</p>
      </div>
    `
  }
}
