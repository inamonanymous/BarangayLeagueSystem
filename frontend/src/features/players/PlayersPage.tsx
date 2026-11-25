import { useEffect, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPlayer, getPlayers, getPlayerVoterIds, savePlayerVoterId, setPlayerArchived, updatePlayer, type Player } from '../../shared/api/seasons'
import TableFilters, { emptyTableFilters, matchesTableFilters, type TableFilterColumn } from '../../shared/components/TableFilters'
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

function VoterIds({ player, onSavingChange }: { player: Player; onSavingChange: (saving: boolean) => void }) {
  const queryClient = useQueryClient()
  const [year, setYear] = useState(String(new Date().getFullYear()))
  const [number, setNumber] = useState('')
  const [error, setError] = useState('')
  const query = useQuery({ queryKey: ['player-voter-ids', player.id], queryFn: () => getPlayerVoterIds(player.id) })
  const save = useMutation({
    mutationFn: () => savePlayerVoterId(player.id, { year: Number(year), voter_number: number.trim() }),
    onMutate: () => { setError(''); onSavingChange(true) },
    onSuccess: async () => {
      setNumber('')
      setError('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['player-voter-ids', player.id] }),
        queryClient.invalidateQueries({ queryKey: ['voter-status'] }),
      ])
    },
    onError: (caught) => setError(errorMessage(caught)),
    onSettled: () => onSavingChange(false),
  })
  return <section className="player-modal__voters">
    <h3>Voter IDs</h3>
    <p>IDs are used for seasons with the same year. Changing an ID requires verification again.</p>
    <p>Voter IDs are saved separately from profile changes.</p>
    {query.isPending ? <p>Loading voter IDs...</p> : null}
    {query.isError ? <p role="alert">{errorMessage(query.error)}</p> : null}
    {query.data ? query.data.length ? <ul>{query.data.map((entry) => <li key={entry.year}>{entry.year}: {entry.voter_number}</li>)}</ul> : <p>No voter IDs recorded.</p> : null}
    {!player.is_archived ? <form className="player-modal__voter-form" onChange={() => { if (save.isSuccess) save.reset() }}
      onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
      <label>Season year <input required type="number" min="1" max="2147483647" step="1" value={year} onChange={(event) => setYear(event.target.value)} /></label>
      <label>Voter ID <input required maxLength={100} value={number} onChange={(event) => setNumber(event.target.value)} /></label>
      <button type="submit" disabled={save.isPending}>{save.isPending ? 'Saving...' : 'Save voter ID'}</button>
    </form> : null}
    {save.isSuccess && !error ? <p role="status">Voter ID saved.</p> : null}
    {error ? <p role="alert">{error}</p> : null}
  </section>
}

function PlayerModal({ player, onClose, refreshPlayers }: {
  player: Player
  onClose: () => void
  refreshPlayers: (includeRosters?: boolean) => Promise<unknown>
}) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [draft, setDraft] = useState(player)
  const [voterSaving, setVoterSaving] = useState(false)
  const update = useMutation({
    mutationFn: () => updatePlayer(draft.id, {
      first_name: draft.first_name.trim(),
      middle_name: draft.middle_name,
      last_name: draft.last_name.trim(),
      birthdate: draft.birthdate,
      gender: draft.gender.trim(),
      address: draft.address.trim(),
    }),
    onSuccess: async (saved) => {
      setDraft(saved)
      await refreshPlayers(true)
    },
  })

  useEffect(() => {
    const dialog = dialogRef.current
    dialog?.showModal()
    return () => { if (dialog?.open) dialog.close() }
  }, [])

  const busy = update.isPending || voterSaving
  return <dialog ref={dialogRef} className="player-modal" aria-labelledby="player-modal-title"
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose() }}>
    <div className="player-modal__header">
      <h2 id="player-modal-title">{player.is_archived ? 'Player details' : 'Edit player'}: {player.first_name} {player.last_name}</h2>
      <button type="button" disabled={busy} onClick={onClose} aria-label="Close player details">Close</button>
    </div>
    {player.is_archived ? <p>This player is archived. Restore the profile to edit it or change voter IDs.</p> : null}
    <form className="player-modal__form" onChange={() => { if (update.isSuccess) update.reset() }}
      onSubmit={(event) => { event.preventDefault(); update.mutate() }}>
      <label>First name
        <input required maxLength={100} disabled={player.is_archived} value={draft.first_name} onChange={(event) => setDraft({ ...draft, first_name: event.target.value })} />
      </label>
      <label>Middle name
        <input maxLength={100} disabled={player.is_archived} value={draft.middle_name ?? ''} onChange={(event) => setDraft({ ...draft, middle_name: event.target.value || null })} />
      </label>
      <label>Last name
        <input required maxLength={100} disabled={player.is_archived} value={draft.last_name} onChange={(event) => setDraft({ ...draft, last_name: event.target.value })} />
      </label>
      <label>Birthdate
        <input required type="date" disabled={player.is_archived} value={draft.birthdate} onChange={(event) => setDraft({ ...draft, birthdate: event.target.value })} />
      </label>
      <label>Gender
        <select required disabled={player.is_archived} value={draft.gender} onChange={(event) => setDraft({ ...draft, gender: event.target.value })}>
          <option value="">Select gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
      </label>
      <label className="player-modal__address">Address
        <input required maxLength={1000} disabled={player.is_archived} value={draft.address} onChange={(event) => setDraft({ ...draft, address: event.target.value })} />
      </label>
      {!player.is_archived ? <button type="submit" disabled={busy}>{update.isPending ? 'Saving...' : 'Save profile'}</button> : null}
    </form>
    {update.isError ? <p role="alert">{errorMessage(update.error)}</p> : null}
    {update.isSuccess ? <p role="status">Player profile saved.</p> : null}
    <VoterIds player={player} onSavingChange={setVoterSaving} />
  </dialog>
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
  const [voterYear, setVoterYear] = useState(String(new Date().getFullYear()))
  const [voterNumber, setVoterNumber] = useState('')
  const [error, setError] = useState('')
  const [filters, setFilters] = useState(emptyTableFilters)
  const isAdmin = currentUser?.role === 'Administrator'
  const queryKey = ['players', includeArchived] as const

  const playersQuery = useQuery({
    queryKey,
    queryFn: () => getPlayers(includeArchived),
    enabled: isAdmin,
  })

  function refreshPlayers(includeRosters = false) {
    return Promise.all([
      queryClient.invalidateQueries({ queryKey: ['players'] }),
      ...(includeRosters ? [queryClient.invalidateQueries({ queryKey: ['team-roster'] })] : []),
    ])
  }

  const createMutation = useMutation({
    mutationFn: () => createPlayer({
      first_name: firstName.trim(),
      middle_name: middleName.trim() || null,
      last_name: lastName.trim(),
      birthdate,
      gender: gender.trim(),
      address: address.trim(),
      ...(voterNumber.trim() ? { voter_year: Number(voterYear), voter_number: voterNumber.trim() } : {}),
    }),
    onSuccess: async () => {
      setFirstName('')
      setMiddleName('')
      setLastName('')
      setBirthdate('')
      setGender('')
      setAddress('')
      setVoterNumber('')
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
      await refreshPlayers(true)
    },
    onError: (caught) => setError(errorMessage(caught)),
  })

  const columns: TableFilterColumn<Player>[] = [
    { id: 'player', label: 'Player', value: (player) => [player.first_name, player.middle_name, player.last_name].filter(Boolean).join(' ') },
    { id: 'birthdate', label: 'Birthdate', value: (player) => player.birthdate },
    { id: 'gender', label: 'Gender', value: (player) => player.gender },
    { id: 'address', label: 'Address', value: (player) => player.address },
    { id: 'status', label: 'Status', value: (player) => player.is_archived ? 'Archived' : 'Active' },
    { id: 'actions', label: 'Actions', value: (player) => player.is_archived ? 'View Restore' : 'Edit Archive' },
  ]
  const visiblePlayers = playersQuery.data?.filter((player) => matchesTableFilters(player, columns, filters)) ?? []

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
          <select required value={gender} onChange={(event) => setGender(event.target.value)}>
            <option value="">Select gender</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label style={{ display: 'grid', gap: '0.25rem', gridColumn: '1 / -1' }}>Address
          <input required maxLength={1000} value={address} onChange={(event) => setAddress(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Voter ID (optional)
          <input maxLength={100} value={voterNumber} onChange={(event) => setVoterNumber(event.target.value)} />
        </label>
        <label style={{ display: 'grid', gap: '0.25rem' }}>Voter ID season year
          <input type="number" min="1" max="2147483647" step="1" required={Boolean(voterNumber.trim())} value={voterYear} onChange={(event) => setVoterYear(event.target.value)} />
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
        <>
        <TableFilters name="players" columns={columns} filters={filters} onChange={setFilters}
          visibleCount={visiblePlayers.length} totalCount={playersQuery.data.length} />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
            <thead><tr style={{ textAlign: 'left', borderBottom: '1px solid #cbd5e1' }}>
              <th style={{ padding: '0.65rem' }}>Player</th><th style={{ padding: '0.65rem' }}>Birthdate</th><th style={{ padding: '0.65rem' }}>Gender</th><th style={{ padding: '0.65rem' }}>Address</th><th style={{ padding: '0.65rem' }}>Status</th><th style={{ padding: '0.65rem' }}>Actions</th>
            </tr></thead>
            <tbody>{visiblePlayers.map((player) => (
              <tr key={player.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={{ padding: '0.65rem' }}>{[player.first_name, player.middle_name, player.last_name].filter(Boolean).join(' ')}</td>
                <td style={{ padding: '0.65rem' }}>{player.birthdate}</td>
                <td style={{ padding: '0.65rem' }}>{player.gender}</td>
                <td style={{ padding: '0.65rem' }}>{player.address}</td>
                <td style={{ padding: '0.65rem' }}>{player.is_archived ? 'Archived' : 'Active'}</td>
                <td style={{ padding: '0.65rem' }}>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button type="button" onClick={() => setEditingPlayer(player)}>{player.is_archived ? 'View' : 'Edit'}</button>
                    <button type="button" disabled={archiveMutation.isPending} onClick={() => archiveMutation.mutate({ playerId: player.id, archived: !player.is_archived })}>{player.is_archived ? 'Restore' : 'Archive'}</button>
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        </>
      ) : null}
      {editingPlayer ? <PlayerModal key={editingPlayer.id} player={editingPlayer} onClose={() => setEditingPlayer(null)} refreshPlayers={refreshPlayers} /> : null}
    </div>
  )
}

export default PlayersPage
