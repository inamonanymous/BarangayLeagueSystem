import { useQueryClient } from '@tanstack/react-query'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { CalendarDays, LayoutGrid, LogIn, LogOut, UserPlus, Users } from 'lucide-react'
import { currentUserQueryKey, logoutUser } from '../api/auth'
import { useCurrentUser } from '../../features/auth/useCurrentUser'

function MainLayout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user } = useCurrentUser()

  async function handleLogout() {
    await logoutUser()
    queryClient.removeQueries({ queryKey: currentUserQueryKey })
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fb', color: '#1f2937' }}>
      <header style={{ background: '#0f172a', color: 'white', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.25rem' }}>Barangay League System</h1>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', opacity: 0.8 }}>Sprint 1 authentication</p>
        </div>
        <nav style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <NavLink to="/" style={{ color: 'white', textDecoration: 'none' }}>
            <LayoutGrid size={18} /> Dashboard
          </NavLink>
          <NavLink to="/seasons" style={{ color: 'white', textDecoration: 'none' }}>
            <CalendarDays size={18} /> Seasons
          </NavLink>
          {user?.role === 'Administrator' ? (
            <NavLink to="/users/new" style={{ color: 'white', textDecoration: 'none' }}>
              <UserPlus size={18} /> Add user
            </NavLink>
          ) : null}
          {user?.role === 'Administrator' ? (
            <NavLink to="/players" style={{ color: 'white', textDecoration: 'none' }}>
              <Users size={18} /> Players
            </NavLink>
          ) : null}
          {user ? (
            <>
              <span style={{ color: '#cbd5e1' }}>Hello, {user.username}</span>
              <button onClick={handleLogout} style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <LogOut size={18} /> Logout
              </button>
            </>
          ) : (
            <NavLink to="/login" style={{ color: 'white', textDecoration: 'none' }}>
              <LogIn size={18} /> Login
            </NavLink>
          )}
        </nav>
      </header>

      <main style={{ padding: '2rem' }}>
        <Outlet />
      </main>
    </div>
  )
}

export default MainLayout
