import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { addPlayerToRoster, getAvailablePlayers, getTeamRoster, getVoterStatus, removePlayerFromRoster, updateRosterEntry, verifyRosterVoter, type SeasonStatus } from '../../shared/api/seasons'
import { seasonDataStaleTime } from './queryOptions'

interface TeamRosterSectionProps {
  teamId: number
  teamArchived: boolean
  minimumRosterSize: number
  seasonStatus: SeasonStatus
  voterRequired: boolean
  registrationStartDate: string | null
  registrationEndDate: string | null
  isAdmin: boolean
  isActive: boolean
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

function isAdult(birthdate: string): boolean {
  const today = localDate()
  const age = Number(today.slice(0, 4)) - Number(birthdate.slice(0, 4))
  return age > 18 || (age === 18 && today.slice(5) >= birthdate.slice(5))
}

function RosterVoterVerification({ teamId, playerId, name, isActive }: { teamId: number; playerId: number; name: string; isActive: boolean }) {
  const queryClient = useQueryClient()
  const key = ['voter-status', teamId, String(playerId)] as const
  const query = useQuery({ queryKey: key, queryFn: () => getVoterStatus(teamId, playerId), enabled: isActive })
  const verify = useMutation({
    mutationFn: () => verifyRosterVoter(teamId, playerId),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['voter-status'] }) },
  })
  if (!isActive) return null
  if (query.isPending) return <span>Loading voter eligibility...</span>
  if (query.isError) return <span role="alert">{errorMessage(query.error)}</span>
  const status = query.data
  if (status.verified) return <span>Voter verified</span>
  if (!status.has_voter_id) return <span>Voter ID for {status.year} missing. <Link to="/players">Edit player</Link></span>
  return <span>
    <button type="button" disabled={verify.isPending} onClick={() => {
      if (window.confirm(`Confirm that you checked ${name}'s saved voter ID for ${status.year}?`)) verify.mutate()
    }}>Verify voter ID</button>
    {verify.isError ? <span role="alert">{errorMessage(verify.error)}</span> : null}
  </span>
}

function TeamRosterSection({ teamId, teamArchived, minimumRosterSize, seasonStatus, voterRequired, registrationStartDate, registrationEndDate, isAdmin, isActive }: TeamRosterSectionProps) {
  const queryClient = useQueryClient()
  const rosterKey = ['team-roster', teamId] as const
  const [playerId, setPlayerId] = useState('')
  const [jerseyNumber, setJerseyNumber] = useState('')
  const [voterVerified, setVoterVerified] = useState(false)
  const [error, setError] = useState('')
  const [editingJersey, setEditingJersey] = useState<{ rosterId: number; value: string } | null>(null)
  const rosterQuery = useQuery({ queryKey: rosterKey, queryFn: () => getTeamRoster(teamId), enabled: isActive, staleTime: seasonDataStaleTime })
  const today = localDate()
  const inWindow = !registrationStartDate || !registrationEndDate
    || (today >= registrationStartDate && today <= registrationEndDate)
  const canEdit = isAdmin && !teamArchived && seasonStatus === 'REGISTRATION' && inWindow
  const playersQuery = useQuery({
    queryKey: ['players', 'available', teamId],
    queryFn: () => getAvailablePlayers(teamId),
    enabled: isActive && canEdit,
    staleTime: seasonDataStaleTime,
  })
  const selectedPlayerId = playersQuery.data?.some((player) => String(player.id) === playerId)
    ? playerId : ''
  const voterStatus = useQuery({
    queryKey: ['voter-status', teamId, selectedPlayerId],
    queryFn: () => getVoterStatus(teamId, Number(selectedPlayerId)),
    enabled: isActive && canEdit && Boolean(selectedPlayerId),
    staleTime: 0,
  })
  const activeRosterCount = rosterQuery.data?.filter((entry) => !entry.player.is_archived).length

  const refresh = () => Promise.all([
    queryClient.invalidateQueries({ queryKey: rosterKey }),
    queryClient.invalidateQueries({ queryKey: ['players', 'available'] }),
    queryClient.invalidateQueries({ queryKey: ['voter-status'] }),
  ])
  const addMutation = useMutation({
    mutationFn: () => addPlayerToRoster(teamId, {
      player_id: Number(selectedPlayerId),
      jersey_number: jerseyNumber.trim(),
      voter_verified: voterVerified,
      eligibility_notes: null,
    }),
    onSuccess: async () => {
      setPlayerId('')
      setJerseyNumber('')
      setVoterVerified(false)
      setError('')
      await refresh()
    },
    onError: async (caught) => {
      setError(errorMessage(caught))
      await refresh()
    },
  })
  const updateMutation = useMutation({
    mutationFn: (entry: { rosterId: number; jersey: string }) => updateRosterEntry(teamId, entry.rosterId, entry.jersey),
    onSuccess: async () => {
      setEditingJersey(null)
      setError('')
      await queryClient.invalidateQueries({ queryKey: rosterKey })
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
    <section className="team-roster">
      <h5 className="team-roster__heading">Roster</h5>
      {teamArchived ? (
        <p role="status" className="roster-readiness roster-readiness--muted">Archived team; excluded from roster readiness.</p>
      ) : activeRosterCount !== undefined ? (
        <p
          role="status"
          className={`roster-readiness ${activeRosterCount >= minimumRosterSize ? 'roster-readiness--ready' : 'roster-readiness--incomplete'}`}
        >
          <strong>Roster readiness:</strong> {activeRosterCount}/{minimumRosterSize} active players — {activeRosterCount >= minimumRosterSize
            ? 'Ready'
            : `${minimumRosterSize - activeRosterCount} more needed`}
        </p>
      ) : null}
      {rosterQuery.isPending ? <p>Loading roster...</p> : null}
      {rosterQuery.isError ? <p role="alert">{errorMessage(rosterQuery.error)}</p> : null}
      {rosterQuery.data?.length === 0 ? <p>No players on this roster.</p> : null}
      {rosterQuery.data?.length ? (
        <ul className="roster-entries">
          {rosterQuery.data.map((entry) => (
            <li key={entry.id} className="roster-entry">
              <div className="roster-entry__player">
                <strong>{entry.player.first_name} {entry.player.middle_name ?? ''} {entry.player.last_name}</strong>
                {entry.player.is_archived ? <span className="status-badge status-badge--muted">Archived profile</span> : null}
              </div>
              <div className="roster-entry__actions">
                {editingJersey?.rosterId === entry.id ? (
                  <>
                    <input aria-label="Jersey number" maxLength={10} value={editingJersey.value} onChange={(event) => setEditingJersey({ ...editingJersey, value: event.target.value })} />
                    <button type="button" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate({ rosterId: entry.id, jersey: editingJersey.value })}>Save</button>
                    <button type="button" onClick={() => setEditingJersey(null)}>Cancel</button>
                  </>
                ) : (
                  <>
                    <span className="roster-entry__jersey">Jersey #{entry.jersey_number}</span>
                    {isAdmin && voterRequired && isAdult(entry.player.birthdate) && !teamArchived && !entry.player.is_archived && (seasonStatus === 'REGISTRATION' || seasonStatus === 'ONGOING') ? (
                      <RosterVoterVerification teamId={teamId} playerId={entry.player.id} name={`${entry.player.first_name} ${entry.player.last_name}`} isActive={isActive} />
                    ) : null}
                    {canEdit ? <button type="button" onClick={() => setEditingJersey({ rosterId: entry.id, value: entry.jersey_number })}>Edit number</button> : null}
                    {canEdit ? <button type="button" disabled={removeMutation.isPending} onClick={() => {
                      if (window.confirm(`Remove ${entry.player.first_name} ${entry.player.last_name} from this roster? Their player profile will remain.`)) removeMutation.mutate(entry.id)
                    }}>Remove</button> : null}
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : null}
      {canEdit ? (
        <form onSubmit={(event) => { event.preventDefault(); setError(''); addMutation.mutate() }} className="roster-add-form">
          <label style={{ display: 'grid', gap: '0.25rem' }}>Player
            <select required value={selectedPlayerId} disabled={playersQuery.isFetching || playersQuery.isError} onChange={(event) => { setPlayerId(event.target.value); setVoterVerified(false) }}>
              <option value="">Select player</option>
              {!playersQuery.isFetching && !playersQuery.isError
                ? playersQuery.data?.map((player) => <option key={player.id} value={player.id}>{player.first_name} {player.last_name}</option>)
                : null}
            </select>
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Jersey number
            <input required maxLength={10} value={jerseyNumber} onChange={(event) => setJerseyNumber(event.target.value)} />
          </label>
          {selectedPlayerId && voterStatus.isFetching ? <p>Loading voter eligibility...</p> : null}
          {selectedPlayerId && voterStatus.isError ? <p role="alert">{errorMessage(voterStatus.error)}</p> : null}
          {voterStatus.data?.required ? voterStatus.data.has_voter_id ? voterStatus.data.verified
            ? <p>Voter eligibility already verified for this season.</p>
            : <><p>Review the saved voter ID on the <Link to="/players">Players page</Link>.</p><label><input type="checkbox" checked={voterVerified} onChange={(event) => setVoterVerified(event.target.checked)} /> I checked this player's saved voter ID for {voterStatus.data.year}</label></>
            : <p role="alert">Add the player's voter ID for {voterStatus.data.year} on the <Link to="/players">Players page</Link> before adding them.</p> : null}
          <button type="submit" disabled={addMutation.isPending || playersQuery.isFetching || playersQuery.isError || !selectedPlayerId || voterStatus.isFetching || voterStatus.isError || !voterStatus.data || (voterStatus.data.required && (!voterStatus.data.has_voter_id || (!voterStatus.data.verified && !voterVerified)))}>
            {addMutation.isPending ? 'Adding...' : 'Add player'}
          </button>
          {playersQuery.isFetching ? <p>Loading available players...</p> : null}
          {playersQuery.isError ? <p role="alert">{errorMessage(playersQuery.error)}</p> : null}
          {!playersQuery.isFetching && !playersQuery.isError && playersQuery.data?.length === 0 ? (
            <p>No available players for this sport and season. <Link to="/players">Create player profiles</Link>.</p>
          ) : null}
        </form>
      ) : isAdmin ? (
        <p style={{ color: '#64748b' }}>Roster changes are available only during the season registration period.</p>
      ) : null}
      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
    </section>
  )
}

export default TeamRosterSection
