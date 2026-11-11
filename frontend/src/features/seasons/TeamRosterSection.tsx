import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { addPlayerToRoster, getPlayers, getTeamRoster, removePlayerFromRoster, updateRosterEntry, type SeasonStatus } from '../../shared/api/seasons'

interface TeamRosterSectionProps {
  teamId: number
  teamArchived: boolean
  seasonStatus: SeasonStatus
  registrationStartDate: string | null
  registrationEndDate: string | null
  isAdmin: boolean
}

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ApiErrorResponse | undefined
    return (response?.errors ? Object.values(response.errors).flat()[0] : undefined)
      ?? response?.message
      ?? 'Could not update roster.'
  }
  return 'Could not update roster.'
}

function localDate(): string {
  const today = new Date()
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
}

function TeamRosterSection({ teamId, teamArchived, seasonStatus, registrationStartDate, registrationEndDate, isAdmin }: TeamRosterSectionProps) {
  const queryClient = useQueryClient()
  const rosterKey = ['team-roster', teamId] as const
  const [playerId, setPlayerId] = useState('')
  const [jerseyNumber, setJerseyNumber] = useState('')
  const [voterVerified, setVoterVerified] = useState(false)
  const [voterNumber, setVoterNumber] = useState('')
  const [error, setError] = useState('')
  const [editingJersey, setEditingJersey] = useState<{ rosterId: number; value: string } | null>(null)
  const rosterQuery = useQuery({ queryKey: rosterKey, queryFn: () => getTeamRoster(teamId) })
  const playersQuery = useQuery({
    queryKey: ['players', 'active'],
    queryFn: () => getPlayers(),
    enabled: isAdmin,
  })
  const today = localDate()
  const inWindow = !registrationStartDate || !registrationEndDate
    || (today >= registrationStartDate && today <= registrationEndDate)
  const canEdit = isAdmin && !teamArchived && seasonStatus === 'REGISTRATION' && inWindow

  const refresh = () => Promise.all([
    queryClient.invalidateQueries({ queryKey: rosterKey }),
    queryClient.invalidateQueries({ queryKey: ['players'] }),
  ])
  const addMutation = useMutation({
    mutationFn: () => addPlayerToRoster(teamId, {
      player_id: Number(playerId),
      jersey_number: jerseyNumber.trim(),
      voter_verified: voterVerified,
      voter_number: voterNumber.trim() || null,
      eligibility_notes: null,
    }),
    onSuccess: async () => {
      setPlayerId('')
      setJerseyNumber('')
      setVoterVerified(false)
      setVoterNumber('')
      setError('')
      await refresh()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })
  const updateMutation = useMutation({
    mutationFn: (entry: { rosterId: number; jersey: string }) => updateRosterEntry(teamId, entry.rosterId, entry.jersey),
    onSuccess: async () => {
      setEditingJersey(null)
      setError('')
      await refresh()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })
  const removeMutation = useMutation({
    mutationFn: (rosterId: number) => removePlayerFromRoster(teamId, rosterId),
    onSuccess: async () => {
      setError('')
      await refresh()
    },
    onError: (caught) => setError(errorMessage(caught)),
  })

  return (
    <section style={{ marginTop: '0.75rem', paddingTop: '0.65rem', borderTop: '1px solid #e2e8f0' }}>
      <h5 style={{ margin: '0 0 0.4rem' }}>Roster</h5>
      {rosterQuery.isPending ? <p>Loading roster...</p> : null}
      {rosterQuery.isError ? <p role="alert">{errorMessage(rosterQuery.error)}</p> : null}
      {rosterQuery.data?.length === 0 ? <p>No players on this roster.</p> : null}
      {rosterQuery.data?.length ? (
        <ul style={{ margin: '0.4rem 0', paddingLeft: '1.2rem' }}>
          {rosterQuery.data.map((entry) => (
            <li key={entry.id} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span>{entry.player.first_name} {entry.player.middle_name ?? ''} {entry.player.last_name}</span>
              {editingJersey?.rosterId === entry.id ? (
                <>
                  <input aria-label="Jersey number" maxLength={10} value={editingJersey.value} onChange={(event) => setEditingJersey({ ...editingJersey, value: event.target.value })} />
                  <button type="button" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate({ rosterId: entry.id, jersey: editingJersey.value })}>Save</button>
                  <button type="button" onClick={() => setEditingJersey(null)}>Cancel</button>
                </>
              ) : (
                <>
                  <span>#{entry.jersey_number}</span>
                  {canEdit ? <button type="button" onClick={() => setEditingJersey({ rosterId: entry.id, value: entry.jersey_number })}>Edit number</button> : null}
                  {canEdit ? <button type="button" disabled={removeMutation.isPending} onClick={() => {
                    if (window.confirm(`Remove ${entry.player.first_name} ${entry.player.last_name} from this roster? Their player profile will remain.`)) removeMutation.mutate(entry.id)
                  }}>Remove</button> : null}
                </>
              )}
            </li>
          ))}
        </ul>
      ) : null}
      {canEdit ? (
        <form onSubmit={(event) => { event.preventDefault(); setError(''); addMutation.mutate() }} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', alignItems: 'end', marginTop: '0.65rem' }}>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Player
            <select required value={playerId} onChange={(event) => setPlayerId(event.target.value)}>
              <option value="">Select player</option>
              {playersQuery.data?.map((player) => <option key={player.id} value={player.id}>{player.first_name} {player.last_name}</option>)}
            </select>
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Jersey number
            <input required maxLength={10} value={jerseyNumber} onChange={(event) => setJerseyNumber(event.target.value)} />
          </label>
          <label style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
            <input type="checkbox" checked={voterVerified} onChange={(event) => setVoterVerified(event.target.checked)} /> Voter registration checked
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Voter number (required for adults)
            <input maxLength={100} value={voterNumber} onChange={(event) => setVoterNumber(event.target.value)} />
          </label>
          <button type="submit" disabled={addMutation.isPending || !playerId}>
            {addMutation.isPending ? 'Adding...' : 'Add player'}
          </button>
          {playersQuery.data?.length === 0 ? <p>No active players. <Link to="/players">Create player profiles</Link>.</p> : null}
        </form>
      ) : isAdmin ? (
        <p style={{ color: '#64748b' }}>Roster changes are available only during the season registration period.</p>
      ) : null}
      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
    </section>
  )
}

export default TeamRosterSection
