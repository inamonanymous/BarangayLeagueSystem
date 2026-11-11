import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './shared/layout/MainLayout'
import DashboardPage from './features/dashboard/DashboardPage'
import LoginPage from './features/auth/LoginPage'
import AddUserPage from './features/users/AddUserPage'
import SeasonsPage from './features/seasons/SeasonsPage'
import SeasonConfigurationPage from './features/seasons/SeasonConfigurationPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/seasons" element={<SeasonsPage />} />
        <Route path="/seasons/:seasonId/configuration" element={<SeasonConfigurationPage />} />
        <Route path="/users/new" element={<AddUserPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
