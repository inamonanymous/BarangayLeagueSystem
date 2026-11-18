import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { CalendarDays, LayoutGrid, LogIn, LogOut, Menu, UserPlus, Users, X } from 'lucide-react'
import { currentUserQueryKey, logoutUser } from '../api/auth'
import { useCurrentUser } from '../../features/auth/useCurrentUser'

function MainLayout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user } = useCurrentUser()
  const [menuOpen, setMenuOpen] = useState(false)
  const [logoutError, setLogoutError] = useState('')

  async function handleLogout() {
    setLogoutError('')
    try {
      await logoutUser()
      queryClient.removeQueries({ queryKey: currentUserQueryKey })
      setMenuOpen(false)
      navigate('/login')
    } catch {
      setLogoutError('Could not log out. Please try again.')
    }
  }

  const closeMenu = () => setMenuOpen(false)
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar__brand">
          <strong>Barangay League</strong>
          <button type="button" className="app-sidebar__toggle" aria-expanded={menuOpen}
            aria-controls="main-navigation" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
            onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
        <nav id="main-navigation" className={`app-sidebar__nav${menuOpen ? ' app-sidebar__nav--open' : ''}`} aria-label="Main navigation">
          <NavLink end to="/" onClick={closeMenu}><LayoutGrid size={18} /> Dashboard</NavLink>
          <NavLink to="/seasons" onClick={closeMenu}><CalendarDays size={18} /> Seasons</NavLink>
          {user?.role === 'Administrator' ? <>
            <NavLink to="/players" onClick={closeMenu}><Users size={18} /> Players</NavLink>
            <NavLink to="/users/new" onClick={closeMenu}><UserPlus size={18} /> Add user</NavLink>
          </> : null}
          <div className="app-sidebar__account">
            {user ? <>
              <span>{user.username} · {user.role}</span>
              <button type="button" onClick={() => { void handleLogout() }}><LogOut size={18} /> Logout</button>
              {logoutError ? <p role="alert">{logoutError}</p> : null}
            </> : <NavLink to="/login" onClick={closeMenu}><LogIn size={18} /> Login</NavLink>}
          </div>
        </nav>
      </aside>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}

export default MainLayout
