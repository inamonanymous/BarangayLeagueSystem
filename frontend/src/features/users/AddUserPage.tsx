import { useState } from 'react'
import { AxiosError } from 'axios'
import { Navigate } from 'react-router-dom'
import { createUser, type UserRole } from '../../shared/api/auth'
import { useCurrentUser } from '../auth/useCurrentUser'

interface ApiErrorResponse {
  message?: string
}

function AddUserPage() {
  const { data: currentUser, isPending } = useCurrentUser()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('Encoder')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isPending) {
    return <p>Loading account...</p>
  }

  if (!currentUser) {
    return <Navigate to="/" replace />
  }

  if (currentUser.role !== 'Administrator') {
    return <p role="alert">Only administrators can add users.</p>
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setError('')
    setIsSubmitting(true)

    try {
      const result = await createUser(username.trim(), password, role)
      setMessage(`User ${result.data.username} was created as ${result.data.role}.`)
      setUsername('')
      setPassword('')
    } catch (caughtError: unknown) {
      if (caughtError instanceof AxiosError) {
        const response = caughtError.response?.data as ApiErrorResponse | undefined
        setError(response?.message ?? 'Could not create user.')
      } else {
        setError('Could not create user.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section style={{ maxWidth: '560px', background: 'white', padding: '1.5rem', borderRadius: '8px' }}>
      <h2 style={{ marginTop: 0 }}>Add user</h2>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
        <label style={{ display: 'grid', gap: '0.35rem' }}>
          Username
          <input
            required
            minLength={3}
            maxLength={100}
            autoComplete="off"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            style={{ padding: '0.7rem', border: '1px solid #cbd5e1', borderRadius: '4px' }}
          />
        </label>
        <label style={{ display: 'grid', gap: '0.35rem' }}>
          Temporary password
          <input
            required
            type="password"
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            style={{ padding: '0.7rem', border: '1px solid #cbd5e1', borderRadius: '4px' }}
          />
        </label>
        <label style={{ display: 'grid', gap: '0.35rem' }}>
          Role
          <select
            value={role}
            onChange={(event) => setRole(event.target.value as UserRole)}
            style={{ padding: '0.7rem', border: '1px solid #cbd5e1', borderRadius: '4px' }}
          >
            <option value="Encoder">Encoder</option>
            <option value="Viewer">Viewer</option>
            <option value="Administrator">Administrator</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={isSubmitting}
          style={{ padding: '0.7rem 1rem', background: '#0f172a', color: 'white', border: 0, borderRadius: '4px', cursor: isSubmitting ? 'wait' : 'pointer' }}
        >
          {isSubmitting ? 'Creating...' : 'Create user'}
        </button>
      </form>
      {message ? <p role="status" style={{ color: '#0f766e' }}>{message}</p> : null}
      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
    </section>
  )
}

export default AddUserPage