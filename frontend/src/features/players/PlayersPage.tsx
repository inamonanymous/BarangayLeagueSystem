import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPlayer, getPlayers, setPlayerArchived, updatePlayer, type Player } from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ApiErrorResponse | undefined
    return (response?.errors ? Object.values(response.errors).flat()[0] : undefined)
      ?? response?.message
      ?? 'Could not complete the request.'
  }
  return 'Could not complete the request.'
}

function PlayersPage() {
  const queryClient = useQueryClient()
  const { data: currentUser, isPending: userPending } = useCurrentUser()
  const [includeArchived, setIncludeArchived] = useState(false)
  const [firstName, setFirstName] = useState('')
  const [middleName, setMiddleName] = useState('')
  const [lastName, setLastName] = useState('')
  const [birthdate, setBirthdate] = useState('')
  const [gender, setGender] = useState('')
  const [address, setAddress] = useState('')
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null)
  const [error, setError] = useState('')
  const isAdmin = currentUser?.role === 'Administrator'
  const queryKey = ['players', includeArchived] as const

  const playersQuery = useQuery({
    queryKey,
    queryFn: () => getPlayers(includeArchived),
    enabled: isAdmin,
  })

  function refreshPlayers() {
    return queryClient.invalidateQueries({ queryKey: ['players'] })
  }

  const createMutation = useMutation({
    mutationFn: () => createPlayer({
      first_name: firstName.trim(),
      middle_name: middleName.trim() || null,
      last_name: lastName.trim(),
      birthdate,
      gender: gender.trim(),
      address: address.trim(),
    }),
    onSuccess: async () => {
      setFirstName('')
      setMiddleName('')
      setLastName('')
      setBirthdate('')
      setGender('')
      setAddress('')
      setError('')
      await refreshPlayers()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })
  const updateMutation = useMutation({
    mutationFn: (player: Player) => updatePlayer(player.id, {
      first_name: player.first_name.trim(),
      middle_name: player.middle_name,
      last_name: player.last_name.trim(),
      birthdate: player.birthdate,
      gender: player.gender.trim(),
      address: player.address.trim(),
    }),
    onSuccess: async () => {
      setEditingPlayer(null)
      setError('')
      await refreshPlayers()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })
  const archiveMutation = useMutation({
    mutationFn: ({ playerId, archived }: { playerId: number; archived: boolean }) =>
      setPlayerArchived(playerId, archived),
    onSuccess: async () => {
      setError('')
      await refreshPlayers()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })

  if (userPending) return <p>Loading account...</p>
  if (!isAdmin) return <p role="alert">Only Administrators can manage player records. <a href="/login">Sign in</a>.</p>

  return (
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <header>
        <h2 style={{ margin: '0 0 0.3rem' }}>Players</h2>
        <p style={{ margin: 0, color: '#64748b' }}>Permanent player profiles. Archiving preserves their history.</p>
      </header>

      <form onSubmit={(event) => { event.preventDefault(); setError(''); createMutation.mutate() }} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', maxWidth: '900px', padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
        <h3 style={{ gridColumn: '1 / -1', margin: 0 }}>Add player</h3>
        <label style={{ display: 'grid', gap: '0.25rem' }}>First name
          <input required maxLength={100} value={firstName} onChange={(event) => setFirstName(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Middle name
          <input maxLength={100} value={middleName} onChange={(event) => setMiddleName(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Last name
          <input required maxLength={100} value={lastName} onChange={(event) => setLastName(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Birthdate
          <input required type="date" value={birthdate} onChange={(event) => setBirthdate(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Gender
          <input required maxLength={20} value={gender} onChange={(event) => setGender(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem', gridColumn: '1 / -1' }}>Address
          <input required maxLength={1000} value={address} onChange={(event) => setAddress(event.target.value)} />
        </label>
        <button type="submit" disabled={createMutation.isPending}>{createMutation.isPending ? 'Saving...' : 'Create player'}</button>
      </form>

      <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input type="checkbox" checked={includeArchived} onChange={(event) => setIncludeArchived(event.target.checked)} />
        Show archived profiles
      </label>
      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
      {playersQuery.isPending ? <p>Loading players...</p> : null}
      {playersQuery.isError ? <p role="alert">{errorMessage(playersQuery.error)}</p> : null}
      {playersQuery.data?.length === 0 ? <p>No players found.</p> : null}
      {playersQuery.data?.length ? (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
            <thead><tr style={{ textAlign: 'left', borderBottom: '1px solid #cbd5e1' }}>
              <th style={{ padding: '0.65rem' }}>Player</th><th style={{ padding: '0.65rem' }}>Birthdate</th><th style={{ padding: '0.65rem' }}>Gender</th><th style={{ padding: '0.65rem' }}>Address</th><th style={{ padding: '0.65rem' }}>Status</th><th style={{ padding: '0.65rem' }}>Actions</th>
            </tr></thead>
            <tbody>{playersQuery.data.map((player) => (
              <tr key={player.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={{ padding: '0.65rem' }}>
                  {editingPlayer?.id === player.id ? (
                    <div style={{ display: 'grid', gap: '0.35rem' }}>
                      <input aria-label="First name" value={editingPlayer.first_name} onChange={(event) => setEditingPlayer({ ...editingPlayer, first_name: event.target.value })} />
                      <input aria-label="Middle name" value={editingPlayer.middle_name ?? ''} onChange={(event) => setEditingPlayer({ ...editingPlayer, middle_name: event.target.value || null })} />
                      <input aria-label="Last name" value={editingPlayer.last_name} onChange={(event) => setEditingPlayer({ ...editingPlayer, last_name: event.target.value })} />
                    </div>
                  ) : `${player.first_name} ${player.middle_name ?? ''} ${player.last_name}`}
                </td>
                <td style={{ padding: '0.65rem' }}>{editingPlayer?.id === player.id ? <input aria-label="Birthdate" type="date" value={editingPlayer.birthdate} onChange={(event) => setEditingPlayer({ ...editingPlayer, birthdate: event.target.value })} /> : player.birthdate}</td>
                <td style={{ padding: '0.65rem' }}>{editingPlayer?.id === player.id ? <input aria-label="Gender" value={editingPlayer.gender} onChange={(event) => setEditingPlayer({ ...editingPlayer, gender: event.target.value })} /> : player.gender}</td>
                <td style={{ padding: '0.65rem' }}>{editingPlayer?.id === player.id ? <input aria-label="Address" value={editingPlayer.address} onChange={(event) => setEditingPlayer({ ...editingPlayer, address: event.target.value })} /> : player.address}</td>
                <td style={{ padding: '0.65rem' }}>{player.is_archived ? 'Archived' : 'Active'}</td>
                <td style={{ padding: '0.65rem' }}>
                  {editingPlayer?.id === player.id ? (
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button type="button" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate(editingPlayer)}>Save</button>
                      <button type="button" onClick={() => setEditingPlayer(null)}>Cancel</button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button type="button" disabled={player.is_archived} onClick={() => setEditingPlayer(player)}>Edit</button>
                      <button type="button" disabled={archiveMutation.isPending} onClick={() => archiveMutation.mutate({ playerId: player.id, archived: !player.is_archived })}>{player.is_archived ? 'Restore' : 'Archive'}</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}

export default PlayersPage
