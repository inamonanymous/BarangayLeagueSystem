import { useCurrentUser } from '../auth/useCurrentUser'

function DashboardPage() {
  const { data: user } = useCurrentUser()

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <section style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 10px 25px rgba(15, 23, 42, 0.08)' }}>
        <h2 style={{ marginTop: 0 }}>Dashboard</h2>
        <p style={{ color: '#64748b', marginBottom: '1rem' }}>
          {user ? `Signed in as ${user.username} with role ${user.role}.` : 'No active session yet.'}
        </p>
        <p style={{ color: '#64748b', marginBottom: 0 }}>This page now reflects the authentication state from the backend.</p>
      </section>
    </div>
  )
}

export default DashboardPage
