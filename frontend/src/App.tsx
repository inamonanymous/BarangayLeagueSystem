import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './shared/layout/MainLayout'
import DashboardPage from './features/dashboard/DashboardPage'
import LoginPage from './features/auth/LoginPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
