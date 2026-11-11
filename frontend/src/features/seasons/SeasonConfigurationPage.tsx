import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  assignDivisionToSeasonSport,
  assignSportToSeason,
  createCatalogDivision,
  createCatalogSport,
  getCatalogDivisions,
  getCatalogSports,
  getSeasonConfiguration,
  seasonsQueryKey,
  type Division,
  type SeasonConfiguration,
} from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'

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

      <ol aria-label="Season configuration progress" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '0.75rem', margin: 0, padding: 0, listStyle: 'none' }}>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>1. Catalog</strong>
          <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
            {sportsQuery.data?.length ?? 0} sports · {divisionsQuery.data?.length ?? 0} divisions available
          </p>
        </li>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>2. Season sports</strong>
          <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
            {configuration.sports.length} assigned to this season
          </p>
        </li>
        <li style={{ padding: '0.85rem', border: '1px solid #d5d9de', borderRadius: '6px', background: 'white' }}>
          <strong>3. Divisions</strong>
          <p style={{ margin: '0.35rem 0 0', color: '#64748b' }}>
            {assignedDivisionCount} assigned under season sports
          </p>
        </li>
      </ol>

      {!isAdmin ? (
        <p role="status">You are viewing this configuration. An Administrator manages catalog entries and season assignments.</p>
      ) : null}

      {isAdmin && configurationOpen ? (
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

      {error ? <p role="alert" style={{ color: '#b91c1c' }}>{error}</p> : null}
      {!configurationOpen ? (
        <p role="status">
          This season is {configuration.season.season_status.toLowerCase()}. Its configuration is read-only so the season record remains stable for history.
        </p>
      ) : null}

      <section style={{ display: 'grid', gap: '0.75rem' }}>
        <h3 style={{ margin: 0 }}>Sports and divisions</h3>
        {configuration.sports.length === 0 ? <p>No sports are assigned to this season yet.</p> : null}
        {configuration.sports.map((entry) => (
          <article key={entry.id} style={{ padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 0.5rem' }}>{entry.sport.name}</h4>
            {entry.sport.description ? <p style={{ margin: '0 0 0.6rem', color: '#64748b' }}>{entry.sport.description}</p> : null}
            {entry.divisions.length ? (
              <ul style={{ margin: '0.4rem 0', paddingLeft: '1.25rem' }}>
                {entry.divisions.map((division) => (
                  <li key={division.id}>{division.name} · {division.gender_policy} · roster {division.minimum_roster_size}-{division.maximum_roster_size}</li>
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