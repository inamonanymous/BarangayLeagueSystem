import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createSeasonDivision, createSeasonSport, getSeasonConfiguration,
  removeDivisionFromSeasonSport, removeSportFromSeason, seasonsQueryKey,
  updateSeasonDivision, updateSeasonSport, type ConfiguredDivision,
} from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'
import SelectionTabs, { selectedTabId } from '../../shared/components/SelectionTabs'
import SeasonTeamsSection from './SeasonTeamsSection'
import DivisionScheduleSection from './DivisionScheduleSection'
import StatisticConfigurationEditor from './StatisticConfigurationEditor'
import { seasonDataStaleTime } from './queryOptions'

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorResponse | undefined
    return (body?.errors ? Object.values(body.errors).flat()[0] : undefined)
      ?? body?.message ?? 'Request failed.'
  }
  if (error instanceof Error) return error.message
  return 'Request failed.'
}

function SeasonConfigurationPage() {
  const { seasonId: seasonIdParam } = useParams()
  const seasonId = Number(seasonIdParam)
  const queryClient = useQueryClient()
  const { data: currentUser } = useCurrentUser()
  const isAdmin = currentUser?.role === 'Administrator'
  const [sportName, setSportName] = useState('')
  const [sportDescription, setSportDescription] = useState('')
  const [divisionName, setDivisionName] = useState('')
  const [genderPolicy, setGenderPolicy] = useState<ConfiguredDivision['gender_policy']>('ANY')
  const [minimum, setMinimum] = useState('5')
  const [maximum, setMaximum] = useState('15')
  const [selectedSport, setSelectedSport] = useState<number | null>(null)
  const [selectedDivisions, setSelectedDivisions] = useState<Record<number, number>>({})
  const [editingSport, setEditingSport] = useState<{ id: number; name: string; description: string } | null>(null)
  const [editingDivision, setEditingDivision] = useState<ConfiguredDivision | null>(null)
  const [error, setError] = useState('')
  const [refreshStatus, setRefreshStatus] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const queryKey = [...seasonsQueryKey, seasonId, 'configuration']
  const configurationQuery = useQuery({
    queryKey,
    queryFn: () => getSeasonConfiguration(seasonId),
    enabled: Number.isInteger(seasonId) && seasonId > 0,
    staleTime: seasonDataStaleTime,
  })
  const refresh = () => queryClient.invalidateQueries({ queryKey })
  const onError = (caught: unknown) => setError(errorMessage(caught))
  const onSuccess = async () => { setError(''); await refresh() }
  const createSport = useMutation({
    mutationFn: () => createSeasonSport(seasonId, sportName.trim(), sportDescription.trim()),
    onSuccess: async (sport) => {
      setSportName(''); setSportDescription(''); setSelectedSport(sport.id)
      await onSuccess()
    },
    onError,
  })
  const editSport = useMutation({
    mutationFn: (sport: { id: number; name: string; description: string }) =>
      updateSeasonSport(seasonId, sport.id, sport.name.trim(), sport.description.trim()),
    onSuccess: async () => { setEditingSport(null); await onSuccess() },
    onError,
  })
  const removeSport = useMutation({
    mutationFn: (id: number) => removeSportFromSeason(seasonId, id),
    onSuccess, onError,
  })
  const createDivision = useMutation({
    mutationFn: (sportId: number) => createSeasonDivision(sportId, {
      name: divisionName.trim(), gender_policy: genderPolicy,
      minimum_roster_size: Number(minimum), maximum_roster_size: Number(maximum),
    }),
    onSuccess: async (division) => {
      setDivisionName('')
      setSelectedDivisions((previous) => ({ ...previous, [division.season_sport_id]: division.id }))
      await onSuccess()
    },
    onError,
  })
  const editDivision = useMutation({
    mutationFn: (division: ConfiguredDivision) => updateSeasonDivision(division.season_sport_id, division.id, {
      name: division.name.trim(), gender_policy: division.gender_policy,
      minimum_roster_size: division.minimum_roster_size, maximum_roster_size: division.maximum_roster_size,
    }),
    onSuccess: async () => { setEditingDivision(null); await onSuccess() },
    onError,
  })
  const removeDivision = useMutation({
    mutationFn: ({ sportId, divisionId }: { sportId: number; divisionId: number }) =>
      removeDivisionFromSeasonSport(sportId, divisionId),
    onSuccess, onError,
  })

  async function refreshData() {
    setRefreshing(true)
    setRefreshStatus('')
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey }, { throwOnError: true }),
        ...[['season-teams'], ['team-roster'], ['players', 'available'], ['division-games'], ['division-standings'], ['sport-statistics-configuration'], ['game-statistics']]
          .map((key) => queryClient.invalidateQueries({ queryKey: key }, { throwOnError: true })),
      ])
      setRefreshStatus('Data refreshed.')
    } catch (caught) {
      setRefreshStatus(`Refresh failed: ${errorMessage(caught)}`)
    } finally {
      setRefreshing(false)
    }
  }

  if (!Number.isInteger(seasonId) || seasonId < 1) return <p role="alert">Invalid season ID.</p>
  if (configurationQuery.isPending) return <p>Loading season configuration...</p>
  if (configurationQuery.isError) return (
    <div>
      <p><Link to="/seasons">Back to seasons</Link></p>
      <p role="alert">{errorMessage(configurationQuery.error)}</p>
      <button type="button" onClick={() => { void configurationQuery.refetch() }}>Retry</button>
    </div>
  )
  const configuration = configurationQuery.data
  if (!configuration) return <p role="alert">Season configuration is unavailable.</p>
  const open = configuration.season.season_status === 'PLANNING' || configuration.season.season_status === 'REGISTRATION'
  const activeSportId = selectedTabId(configuration.sports.map((sport) => sport.id), selectedSport)
  const divisionCount = configuration.sports.reduce((count, sport) => count + sport.divisions.length, 0)

  return (
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <section>
        <p><Link to="/seasons">Back to seasons</Link></p>
        <h2>{configuration.season.name} configuration</h2>
        <p>{configuration.season.year} · {configuration.season.season_status}</p>
        <button type="button" disabled={refreshing} onClick={() => { void refreshData() }}>
          {refreshing ? 'Refreshing...' : 'Refresh data'}
        </button>
        {refreshStatus ? <p role="status">{refreshStatus}</p> : null}
        <p className="muted-help">Data is reused for one minute. Use Refresh data to check now.</p>
      </section>
      <ol aria-label="Season setup steps">
        <li>Configure sports and divisions ({configuration.sports.length} sports, {divisionCount} divisions).</li>
        <li>Register teams during Registration.</li>
        <li>Complete active team rosters before moving to Ongoing.</li>
      </ol>
      {!isAdmin ? <p role="status">Only an Administrator can manage season configuration.</p> : null}
      {!open ? <p role="status">Sports and divisions are read-only outside Planning or Registration.</p> : null}
      {error ? <p role="alert">{error}</p> : null}
      {isAdmin && open ? (
        <form onSubmit={(event) => { event.preventDefault(); setError(''); createSport.mutate() }}>
          <h3>Add sport to this season</h3>
          <label>Sport name <input required maxLength={100} value={sportName} onChange={(event) => setSportName(event.target.value)} /></label>
          <label>Description <input value={sportDescription} onChange={(event) => setSportDescription(event.target.value)} /></label>
          <button type="submit" disabled={createSport.isPending}>Create sport</button>
        </form>
      ) : null}
      <section id="season-divisions">
        <h3>Sports and divisions</h3>
        <p className="muted-help">Choose a sport, division, and team to view one roster at a time.</p>
        {!configuration.sports.length ? <p>No sports in this season yet.</p> : null}
        <SelectionTabs label="Sports" selectedId={selectedSport} onSelect={setSelectedSport}
          items={configuration.sports.map((sport) => {
            const activeDivisionId = selectedTabId(sport.divisions.map((division) => division.id), selectedDivisions[sport.id] ?? null)
            return {
              id: sport.id, label: sport.name,
              content: (
                <article style={{ padding: '1rem', background: 'white', border: '1px solid #d5d9de', borderRadius: '6px' }}>
                  {isAdmin && open && editingSport?.id === sport.id ? (
                    <div>
                      <input aria-label="Sport name" value={editingSport.name} onChange={(event) => setEditingSport({ ...editingSport, name: event.target.value })} />
                      <input aria-label="Sport description" value={editingSport.description} onChange={(event) => setEditingSport({ ...editingSport, description: event.target.value })} />
                      <button type="button" disabled={editSport.isPending} onClick={() => editSport.mutate(editingSport)}>Save sport</button>
                      <button type="button" onClick={() => setEditingSport(null)}>Cancel</button>
                    </div>
                  ) : (
                    <>
                      <h4>{sport.name}</h4>
                      {sport.description ? <p>{sport.description}</p> : null}
                      {isAdmin && open ? <>
                        <button type="button" onClick={() => setEditingSport({ id: sport.id, name: sport.name, description: sport.description ?? '' })}>Edit sport</button>
                        <button type="button" disabled={removeSport.isPending} onClick={() => {
                          if (window.confirm(`Remove ${sport.name} and its divisions from this season?`)) removeSport.mutate(sport.id)
                        }}>Remove sport</button>
                      </> : null}
                    </>
                  )}
                  <StatisticConfigurationEditor sportId={sport.id} isAdmin={isAdmin} isActive={sport.id === activeSportId} />
                  {sport.divisions.length ? (
                    <SelectionTabs label={`${sport.name} divisions`} selectedId={selectedDivisions[sport.id] ?? null}
                      onSelect={(id) => setSelectedDivisions((previous) => ({ ...previous, [sport.id]: id }))}
                      items={sport.divisions.map((division) => ({
                        id: division.id, label: division.name,
                        content: (
                          <div>
                            {isAdmin && open && editingDivision?.id === division.id ? (
                              <div>
                                <input aria-label="Division name" value={editingDivision.name} onChange={(event) => setEditingDivision({ ...editingDivision, name: event.target.value })} />
                                <select aria-label="Gender policy" value={editingDivision.gender_policy} onChange={(event) => setEditingDivision({ ...editingDivision, gender_policy: event.target.value as ConfiguredDivision['gender_policy'] })}>
                                  <option value="ANY">Any</option><option value="MALE_ONLY">Male only</option><option value="FEMALE_ONLY">Female only</option><option value="MIXED">Mixed</option>
                                </select>
                                <input aria-label="Minimum roster size" type="number" min="1" value={editingDivision.minimum_roster_size} onChange={(event) => setEditingDivision({ ...editingDivision, minimum_roster_size: Number(event.target.value) })} />
                                <input aria-label="Maximum roster size" type="number" min="1" value={editingDivision.maximum_roster_size} onChange={(event) => setEditingDivision({ ...editingDivision, maximum_roster_size: Number(event.target.value) })} />
                                <button type="button" disabled={editDivision.isPending} onClick={() => editDivision.mutate(editingDivision)}>Save division</button>
                                <button type="button" onClick={() => setEditingDivision(null)}>Cancel</button>
                              </div>
                            ) : <>
                              <span>{division.name} · {division.gender_policy} · roster {division.minimum_roster_size}-{division.maximum_roster_size}</span>
                              {isAdmin && open ? <>
                                <button type="button" onClick={() => setEditingDivision(division)}>Edit division</button>
                                <button type="button" disabled={removeDivision.isPending} onClick={() => {
                                  if (window.confirm(`Remove ${division.name} from ${sport.name}?`)) removeDivision.mutate({ sportId: sport.id, divisionId: division.id })
                                }}>Remove division</button>
                              </> : null}
                            </>}
                            <SeasonTeamsSection divisionAssignmentId={division.id} minimumRosterSize={division.minimum_roster_size}
                              seasonStatus={configuration.season.season_status} registrationStartDate={configuration.season.registration_start_date}
                              registrationEndDate={configuration.season.registration_end_date} isAdmin={isAdmin}
                              isActive={sport.id === activeSportId && division.id === activeDivisionId} />
                            <DivisionScheduleSection divisionAssignmentId={division.id} seasonStatus={configuration.season.season_status}
                              isAdmin={isAdmin} canEncode={isAdmin || currentUser?.role === 'Encoder'} isActive={sport.id === activeSportId && division.id === activeDivisionId} />
                          </div>
                        ),
                      }))}
                    />
                  ) : <p>No divisions in this sport yet.</p>}
                  {isAdmin && open && sport.id === activeSportId ? (
                    <form onSubmit={(event) => { event.preventDefault(); setError(''); createDivision.mutate(sport.id) }}>
                      <h5>Add division to {sport.name}</h5>
                      <label>Division name <input required maxLength={100} value={divisionName} onChange={(event) => setDivisionName(event.target.value)} /></label>
                      <label>Gender policy <select value={genderPolicy} onChange={(event) => setGenderPolicy(event.target.value as ConfiguredDivision['gender_policy'])}>
                        <option value="ANY">Any</option><option value="MALE_ONLY">Male only</option><option value="FEMALE_ONLY">Female only</option><option value="MIXED">Mixed</option>
                      </select></label>
                      <label>Minimum roster <input required type="number" min="1" value={minimum} onChange={(event) => setMinimum(event.target.value)} /></label>
                      <label>Maximum roster <input required type="number" min="1" value={maximum} onChange={(event) => setMaximum(event.target.value)} /></label>
                      <button type="submit" disabled={createDivision.isPending}>Create division</button>
                    </form>
                  ) : null}
                </article>
              ),
            }
          })}
        />
      </section>
    </div>
  )
}

export default SeasonConfigurationPage
