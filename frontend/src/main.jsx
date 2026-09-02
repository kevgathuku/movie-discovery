import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  return (
    <div style={{ fontFamily: 'sans-serif', textAlign: 'center', marginTop: '50px' }}>
      <h1>Movie Explorer</h1>
      <p>Frontend placeholder skeleton</p>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
