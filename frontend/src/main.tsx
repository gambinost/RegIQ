import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import DashboardPage from './pages/DashboardPage'
import TriggerPage from './pages/TriggerPage'
import PipelinePage from './pages/PipelinePage'
import ReviewPage from './pages/ReviewPage'

createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/trigger" element={<TriggerPage />} />
      <Route path="/pipeline/:roomId" element={<PipelinePage />} />
      <Route path="/review" element={<ReviewPage />} />
      <Route path="/review/:regId" element={<ReviewPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>,
)
