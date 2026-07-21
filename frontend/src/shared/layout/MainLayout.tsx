import { Outlet, NavLink } from 'react-router-dom'
import { LayoutGrid, LogIn } from 'lucide-react'

function MainLayout() {
  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fb', color: '#1f2937' }}>
      <header style={{ background: '#0f172a', color: 'white', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.25rem' }}>Barangay League System</h1>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', opacity: 0.8 }}>Sprint 0 foundation</p>
        </div>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          <NavLink to="/" style={{ color: 'white', textDecoration: 'none' }}>
            <LayoutGrid size={18} /> Dashboard
          </NavLink>
          <NavLink to="/login" style={{ color: 'white', textDecoration: 'none' }}>
            <LogIn size={18} /> Login
          </NavLink>
        </nav>
      </header>

      <main style={{ padding: '2rem' }}>
        <Outlet />
      </main>
    </div>
  )
}

export default MainLayout
