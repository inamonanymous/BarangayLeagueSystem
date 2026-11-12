import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  assignDivisionToSeasonSport,
  assignSportToSeason,
  createCatalogDivision,
  createCatalogSport,
  deleteCatalogDivision,
  deleteCatalogSport,
  getCatalogDivisions,
  getCatalogSports,
  getSeasonConfiguration,
  removeDivisionFromSeasonSport,
  removeSportFromSeason,
  seasonsQueryKey,
  updateCatalogDivision,
  updateCatalogSport,
  type Division,
  type SeasonConfiguration,
} from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'
import SeasonTeamsSection from './SeasonTeamsSection'

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorResponse | undefined
    return (body?.errors ? Object.values(body.errors).flat()[0] : undefined)
      ?? body?.message
      ?? 'Request failed.'
  }
  return 'Request failed.'
}

function SeasonConfigurationPage() {
  const { seasonId: seasonIdParam } = useParams()
  const seasonId = Number(seasonIdParam)
  const queryClient = useQueryClient()
  const { data: currentUser } = useCurrentUser()
  const [sportName, setSportName] = useState('')
  const [sportDescription, setSportDescription] = useState('')
  const [divisionName, setDivisionName] = useState('')
  const [genderPolicy, setGenderPolicy] = useState<Division['gender_policy']>('ANY')
  const [minimumRosterSize, setMinimumRosterSize] = useState('5')
  const [maximumRosterSize, setMaximumRosterSize] = useState('15')
  const [selectedSport, setSelectedSport] = useState('')
  const [selectedDivisionBySport, setSelectedDivisionBySport] = useState<Record<number, string>>({})
  const [editingSport, setEditingSport] = useState<{ id: number; name: string; description: string } | null>(null)
  const [editingDivision, setEditingDivision] = useState<Division | null>(null)
  const [error, setError] = useState('')
  const isAdmin = currentUser?.role === 'Administrator'

  const configurationQuery = useQuery({
    queryKey: [...seasonsQueryKey, seasonId, 'configuration'],
    queryFn: () => getSeasonConfiguration(seasonId),
    enabled: Number.isInteger(seasonId) && seasonId > 0,
  })
  const sportsQuery = useQuery({ queryKey: ['catalog', 'sports'], queryFn: getCatalogSports })
  const divisionsQuery = useQuery({ queryKey: ['catalog', 'divisions'], queryFn: getCatalogDivisions })

  function refreshConfiguration() {
    return Promise.all([
      queryClient.invalidateQueries({ queryKey: [...seasonsQueryKey, seasonId, 'configuration'] }),
      queryClient.invalidateQueries({ queryKey: ['catalog'] }),
    ])
  }

  function handleMutationError(mutationError: unknown) {
    setError(errorMessage(mutationError))
  }

  const createSportMutation = useMutation({
    mutationFn: () => createCatalogSport(sportName.trim(), sportDescription.trim()),
    onSuccess: async () => {
      setSportName('')
      setSportDescription('')
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const createDivisionMutation = useMutation({
    mutationFn: () => createCatalogDivision({
      name: divisionName.trim(),
      gender_policy: genderPolicy,
      minimum_roster_size: Number(minimumRosterSize),
      maximum_roster_size: Number(maximumRosterSize),
    }),
    onSuccess: async () => {
      setDivisionName('')
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const updateSportMutation = useMutation({
    mutationFn: (sport: { id: number; name: string; description: string }) =>
      updateCatalogSport(sport.id, sport.name.trim(), sport.description.trim()),
    onSuccess: async () => {
      setEditingSport(null)
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const deleteSportMutation = useMutation({
    mutationFn: deleteCatalogSport,
    onSuccess: async () => {
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const updateDivisionMutation = useMutation({
    mutationFn: (division: Division) => updateCatalogDivision(division.id, {
      name: division.name.trim(),
      gender_policy: division.gender_policy,
      minimum_roster_size: division.minimum_roster_size,
      maximum_roster_size: division.maximum_roster_size,
    }),
    onSuccess: async () => {
      setEditingDivision(null)
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const deleteDivisionMutation = useMutation({
    mutationFn: deleteCatalogDivision,
    onSuccess: async () => {
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const assignSportMutation = useMutation({
    mutationFn: () => assignSportToSeason(seasonId, Number(selectedSport)),
    onSuccess: async () => {
      setSelectedSport('')
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const assignDivisionMutation = useMutation({
    mutationFn: ({ seasonSportId, divisionId }: { seasonSportId: number; divisionId: number }) =>
      assignDivisionToSeasonSport(seasonSportId, divisionId),
    onSuccess: async () => {
      setSelectedDivisionBySport({})
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const removeSportMutation = useMutation({
    mutationFn: (seasonSportId: number) => removeSportFromSeason(seasonId, seasonSportId),
    onSuccess: async () => {
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })
  const removeDivisionMutation = useMutation({
    mutationFn: ({ seasonSportId, assignmentId }: { seasonSportId: number; assignmentId: number }) =>
      removeDivisionFromSeasonSport(seasonSportId, assignmentId),
    onSuccess: async () => {
      setError('')
      await refreshConfiguration()
    },
    onError: handleMutationError,
  })

  const configuration: SeasonConfiguration | undefined = configurationQuery.data
  const configurationOpen = configuration?.season.season_status === 'PLANNING'
    || configuration?.season.season_status === 'REGISTRATION'
  const assignedSportIds = new Set(configuration?.sports.map((entry) => entry.sport_id) ?? [])
  const assignedDivisionCount = configuration?.sports.reduce(
    (count, entry) => count + entry.divisions.length,
    0,
  ) ?? 0

  if (!Number.isInteger(seasonId) || seasonId < 1) {
    return <p role="alert">Invalid season ID.</p>
  }
  if (configurationQuery.isPending) return <p>Loading season configuration...</p>
  if (configurationQuery.isError) return <p role="alert">{errorMessage(configurationQuery.error)}</p>
  if (!configuration) return <p role="alert">Season configuration is unavailable.</p>

  return (
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <section>
        <p><Link to="/seasons">Back to seasons</Link></p>
        <h2 style={{ margin: '0 0 0.35rem' }}>{configuration.season.name} configuration</h2>
        <p style={{ margin: 0, color: '#64748b' }}>
          {configuration.season.year} · {configuration.season.season_status}
        </p>
      </section>

      <ol aria-label="Season setup steps" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', margin: 0, padding: 0, listStyle: 'none' }}>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>1. Configure sports and divisions</strong>
          <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
            {configuration.sports.length} sports and {assignedDivisionCount} divisions assigned.
          </p>
          <a href="#season-divisions">Go to season divisions</a>
        </li>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>2. Register teams</strong>
          {configuration.season.season_status === 'REGISTRATION' ? (
            <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
              {assignedDivisionCount === 0
                ? 'Assign a division first; its Add team action will appear below.'
                : 'Use Add team under each division while the registration window is active.'}
            </p>
          ) : configuration.season.season_status === 'PLANNING' ? (
            <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
              Move the season to Registration before adding teams. <Link to="/seasons">Manage season status</Link>
            </p>
          ) : (
            <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
              Registration is closed. Teams are read-only.
            </p>
          )}
        </li>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>3. Complete team rosters</strong>
          <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
            Each active team shows its roster count and minimum. Complete the minimum before moving to Ongoing.
          </p>
          <a href="#season-divisions">Review team rosters</a>
        </li>
      </ol>

      {!isAdmin ? (
        <p role="status">
          {currentUser
            ? 'You are viewing this configuration. An Administrator manages catalog entries and season assignments.'
            : <>Sign in as an Administrator to manage Sports and Divisions. <Link to="/login">Sign in</Link>.</>}
        </p>
      ) : null}

      {isAdmin ? (
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <form
            onSubmit={(event) => { event.preventDefault(); setError(''); createSportMutation.mutate() }}
            style={{ display: 'grid', gap: '0.75rem', padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}
          >
            <h3 style={{ margin: 0 }}>Add sport to catalog</h3>
            <label style={{ display: 'grid', gap: '0.3rem' }}>Sport name
              <input required maxLength={100} value={sportName} onChange={(event) => setSportName(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.3rem' }}>Description
              <input value={sportDescription} onChange={(event) => setSportDescription(event.target.value)} />
            </label>
            <button type="submit" disabled={createSportMutation.isPending}>
              {createSportMutation.isPending ? 'Saving...' : 'Create sport'}
            </button>
          </form>

          <form
            onSubmit={(event) => { event.preventDefault(); setError(''); createDivisionMutation.mutate() }}
            style={{ display: 'grid', gap: '0.75rem', padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}
          >
            <h3 style={{ margin: 0 }}>Add division to catalog</h3>
            <label style={{ display: 'grid', gap: '0.3rem' }}>Division name
              <input required maxLength={100} value={divisionName} onChange={(event) => setDivisionName(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.3rem' }}>Gender policy
              <select value={genderPolicy} onChange={(event) => setGenderPolicy(event.target.value as Division['gender_policy'])}>
                <option value="ANY">Any</option>
                <option value="MALE_ONLY">Male only</option>
                <option value="FEMALE_ONLY">Female only</option>
                <option value="MIXED">Mixed</option>
              </select>
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
              <label style={{ display: 'grid', gap: '0.3rem' }}>Minimum roster
                <input required type="number" min="1" value={minimumRosterSize} onChange={(event) => setMinimumRosterSize(event.target.value)} />
              </label>
              <label style={{ display: 'grid', gap: '0.3rem' }}>Maximum roster
                <input required type="number" min="1" value={maximumRosterSize} onChange={(event) => setMaximumRosterSize(event.target.value)} />
              </label>
            </div>
            <button type="submit" disabled={createDivisionMutation.isPending}>
              {createDivisionMutation.isPending ? 'Saving...' : 'Create division'}
            </button>
          </form>
        </section>
      ) : null}

      {isAdmin && configurationOpen ? (
        <section style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', alignItems: 'end' }}>
          <label style={{ display: 'grid', gap: '0.3rem' }}>Assign a catalog sport to this season
            <select value={selectedSport} onChange={(event) => setSelectedSport(event.target.value)}>
              <option value="">Select sport</option>
              {sportsQuery.data?.filter((sport) => !assignedSportIds.has(sport.id)).map((sport) => (
                <option key={sport.id} value={sport.id}>{sport.name}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={!selectedSport || assignSportMutation.isPending}
            onClick={() => { setError(''); assignSportMutation.mutate() }}
          >
            {assignSportMutation.isPending ? 'Assigning...' : 'Assign sport'}
          </button>
        </section>
      ) : null}

      {isAdmin ? (
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
            <h3 style={{ marginTop: 0 }}>Sport catalog</h3>
            {sportsQuery.data?.length ? sportsQuery.data.map((sport) => (
              <div key={sport.id} style={{ padding: '0.65rem 0', borderTop: '1px solid #e2e8f0' }}>
                {editingSport?.id === sport.id ? (
                  <div style={{ display: 'grid', gap: '0.5rem' }}>
                    <input aria-label="Sport name" value={editingSport.name} onChange={(event) => setEditingSport({ ...editingSport, name: event.target.value })} />
                    <input aria-label="Sport description" value={editingSport.description} onChange={(event) => setEditingSport({ ...editingSport, description: event.target.value })} />
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button type="button" disabled={updateSportMutation.isPending} onClick={() => updateSportMutation.mutate(editingSport)}>Save</button>
                      <button type="button" onClick={() => setEditingSport(null)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center' }}>
                    <span>{sport.name}{sport.description ? ` · ${sport.description}` : ''}</span>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button type="button" onClick={() => setEditingSport({ id: sport.id, name: sport.name, description: sport.description ?? '' })}>Edit</button>
                      <button type="button" disabled={deleteSportMutation.isPending} onClick={() => {
                        if (window.confirm(`Delete ${sport.name}? This is only allowed if it is not assigned to a season.`)) deleteSportMutation.mutate(sport.id)
                      }}>Delete</button>
                    </div>
                  </div>
                )}
              </div>
            )) : <p>No sports in the catalog.</p>}
          </div>

          <div style={{ padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
            <h3 style={{ marginTop: 0 }}>Division catalog</h3>
            {divisionsQuery.data?.length ? divisionsQuery.data.map((division) => (
              <div key={division.id} style={{ padding: '0.65rem 0', borderTop: '1px solid #e2e8f0' }}>
                {editingDivision?.id === division.id ? (
                  <div style={{ display: 'grid', gap: '0.5rem' }}>
                    <input aria-label="Division name" value={editingDivision.name} onChange={(event) => setEditingDivision({ ...editingDivision, name: event.target.value })} />
                    <select aria-label="Gender policy" value={editingDivision.gender_policy} onChange={(event) => setEditingDivision({ ...editingDivision, gender_policy: event.target.value as Division['gender_policy'] })}>
                      <option value="ANY">Any</option>
                      <option value="MALE_ONLY">Male only</option>
                      <option value="FEMALE_ONLY">Female only</option>
                      <option value="MIXED">Mixed</option>
                    </select>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      <input aria-label="Minimum roster size" type="number" min="1" value={editingDivision.minimum_roster_size} onChange={(event) => setEditingDivision({ ...editingDivision, minimum_roster_size: Number(event.target.value) })} />
                      <input aria-label="Maximum roster size" type="number" min="1" value={editingDivision.maximum_roster_size} onChange={(event) => setEditingDivision({ ...editingDivision, maximum_roster_size: Number(event.target.value) })} />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button type="button" disabled={updateDivisionMutation.isPending} onClick={() => updateDivisionMutation.mutate(editingDivision)}>Save</button>
                      <button type="button" onClick={() => setEditingDivision(null)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center' }}>
                    <span>{division.name} · {division.gender_policy} · roster {division.minimum_roster_size}-{division.maximum_roster_size}</span>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button type="button" onClick={() => setEditingDivision(division)}>Edit</button>
                      <button type="button" disabled={deleteDivisionMutation.isPending} onClick={() => {
                        if (window.confirm(`Delete ${division.name}? This is only allowed if it is not assigned to a season.`)) deleteDivisionMutation.mutate(division.id)
                      }}>Delete</button>
                    </div>
                  </div>
                )}
              </div>
            )) : <p>No divisions in the catalog.</p>}
          </div>
        </section>
      ) : null}

      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
      {!configurationOpen ? (
        <p role="status">
          This season is {configuration.season.season_status.toLowerCase()}. Its configuration is read-only so the season record remains stable for history.
        </p>
      ) : null}

      <section id="season-divisions" style={{ display: 'grid', gap: '0.75rem' }}>
        <h3 style={{ margin: 0 }}>Sports and divisions</h3>
        {configuration.sports.length === 0 ? <p>No sports are assigned to this season yet.</p> : null}
        {configuration.sports.map((entry) => (
          <article key={entry.id} style={{ padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 0.5rem' }}>{entry.sport.name}</h4>
            {entry.sport.description ? <p style={{ margin: '0 0 0.6rem', color: '#64748b' }}>{entry.sport.description}</p> : null}
            {isAdmin && configurationOpen ? (
              <button
                type="button"
                disabled={removeSportMutation.isPending}
                onClick={() => {
                  if (window.confirm(`Remove ${entry.sport.name} and its division assignments from this season? The catalog sport will remain.`)) {
                    removeSportMutation.mutate(entry.id)
                  }
                }}
              >
                Remove from season
              </button>
            ) : null}
            {entry.divisions.length ? (
              <ul style={{ margin: '0.4rem 0', paddingLeft: '1.25rem' }}>
                {entry.divisions.map((division) => (
                  <li key={division.id} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span>{division.name} · {division.gender_policy} · roster {division.minimum_roster_size}-{division.maximum_roster_size}</span>
                    {isAdmin && configurationOpen ? (
                      <button
                        type="button"
                        disabled={removeDivisionMutation.isPending}
                        onClick={() => {
                          if (window.confirm(`Remove ${division.name} from ${entry.sport.name}? The catalog division will remain.`)) {
                            removeDivisionMutation.mutate({ seasonSportId: entry.id, assignmentId: division.assignment_id })
                          }
                        }}
                      >
                        Remove
                      </button>
                    ) : null}
                    <SeasonTeamsSection
                      divisionAssignmentId={division.assignment_id}
                      minimumRosterSize={division.minimum_roster_size}
                      seasonStatus={configuration.season.season_status}
                      registrationStartDate={configuration.season.registration_start_date}
                      registrationEndDate={configuration.season.registration_end_date}
                      isAdmin={isAdmin}
                    />
                  </li>
                ))}
              </ul>
            ) : <p>No divisions assigned.</p>}
            {isAdmin && configurationOpen ? (
              <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'end', flexWrap: 'wrap' }}>
                <label style={{ display: 'grid', gap: '0.3rem' }}>Assign division
                  <select
                    value={selectedDivisionBySport[entry.id] ?? ''}
                    onChange={(event) => setSelectedDivisionBySport((previous) => ({ ...previous, [entry.id]: event.target.value }))}
                  >
                    <option value="">Select division</option>
                    {divisionsQuery.data?.filter((division) => !entry.divisions.some((assigned) => assigned.id === division.id)).map((division) => (
                      <option key={division.id} value={division.id}>{division.name}</option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  disabled={!selectedDivisionBySport[entry.id] || assignDivisionMutation.isPending}
                  onClick={() => {
                    setError('')
                    assignDivisionMutation.mutate({ seasonSportId: entry.id, divisionId: Number(selectedDivisionBySport[entry.id]) })
                  }}
                >
                  Assign division
                </button>
              </div>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  )
}

export default SeasonConfigurationPage