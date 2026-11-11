import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { currentUserQueryKey, loginUser } from '../../shared/api/auth'

function LoginPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    setMessage('')

    try {
      const result = await loginUser(username, password)
      queryClient.setQueryData(currentUserQueryKey, result.data)
      setMessage(result.message)
      navigate('/')
    } catch (err: unknown) {
      setError('Login failed. Please check your credentials.')
    }
  }

  return (
    <div style={{ maxWidth: '480px', margin: '0 auto', background: 'white', padding: '2rem', borderRadius: '12px', boxShadow: '0 10px 25px rgba(15, 23, 42, 0.08)' }}>
      <h2 style={{ marginTop: 0 }}>Login</h2>
      <p style={{ color: '#64748b' }}>Use the seeded admin account to sign in.</p>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
        <label>
          <div style={{ marginBottom: '0.35rem' }}>Username</div>
          <input value={username} onChange={(event) => setUsername(event.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5e1' }} />
        </label>

        <label>
          <div style={{ marginBottom: '0.35rem' }}>Password</div>
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5e1' }} />
        </label>

        <button type="submit" style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: '#0f172a', color: 'white', border: 'none', cursor: 'pointer' }}>
          Sign In
        </button>
      </form>

      {message ? <p style={{ color: '#0f766e', marginTop: '1rem' }}>{message}</p> : null}
      {error ? <p style={{ color: '#b91c1c', marginTop: '1rem' }}>{error}</p> : null}
    </div>
  )
}

export default LoginPage
