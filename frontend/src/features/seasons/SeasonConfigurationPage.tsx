import { useState } from 'react'
import { AxiosError } from 'axios'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getSeasonConfiguration, seasonsQueryKey, type SeasonConfiguration } from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'
import DivisionScheduleSection from './DivisionScheduleSection'
import SeasonSetupSection from './SeasonSetupSection'
import SeasonTeamsSection from './SeasonTeamsSection'
import { seasonDataStaleTime } from './queryOptions'

const sections = [
  ['overview', 'Overview'],
  ['setup', 'Setup'],
  ['teams', 'Teams & rosters'],
  ['schedule', 'Schedule'],
  ['results', 'Results'],
  ['standings', 'Standings'],
] as const
type Section = typeof sections[number][0]

function isSection(value: string | null): value is Section {
  return sections.some(([id]) => id === value)
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as { message?: string } | undefined
    return body?.message ?? 'Could not load season data.'
  }
  return error instanceof Error ? error.message : 'Could not load season data.'
}

function Overview({ configuration, isAdmin }: { configuration: SeasonConfiguration; isAdmin: boolean }) {
  const { season, sports } = configuration
  const divisionCount = sports.reduce((total, sport) => total + sport.divisions.length, 0)
  const workspace = `/seasons/${season.id}/configuration`
  const status = season.season_status
  return (
    <section className="workspace-card">
      <h2>Next steps</h2>
      <p className="muted-help">Guidance for the {status.toLowerCase()} stage. Available actions depend on your role and the season rules.</p>
      <ol className="workflow-list">
        {status === 'PLANNING' ? <>
          <li><Link to={`${workspace}?section=setup`}>Review sports, divisions and statistic types</Link> ({sports.length} sports, {divisionCount} divisions).</li>
          <li><Link to="/seasons">{isAdmin ? 'Move the season to Registration when ready' : 'View the season status'}</Link>.</li>
        </> : null}
        {status === 'REGISTRATION' ? <>
          <li><Link to={`${workspace}?section=setup`}>Review sports, divisions and statistic types</Link>.</li>
          <li><Link to={`${workspace}?section=teams`}>Review teams and complete active rosters</Link>.</li>
          <li><Link to="/seasons">{isAdmin ? 'Move the season to Ongoing when rosters are ready' : 'View the season status'}</Link>.</li>
        </> : null}
        {status === 'ONGOING' ? <>
          <li><Link to={`${workspace}?section=schedule`}>View or schedule games</Link>.</li>
          <li><Link to={`${workspace}?section=results`}>View game results and player statistics</Link>.</li>
          <li><Link to={`${workspace}?section=standings`}>View standings</Link>.</li>
          {isAdmin ? <li><Link to="/seasons">Complete the season when it is finished</Link>.</li> : null}
        </> : null}
        {status === 'COMPLETED' || status === 'ARCHIVED' ? <>
          <li><Link to={`${workspace}?section=results`}>Review game results and player statistics</Link>.</li>
          <li><Link to={`${workspace}?section=standings`}>View final standings</Link>.</li>
          {status === 'COMPLETED' && isAdmin ? <li><Link to="/seasons">Archive the season when appropriate</Link>.</li> : null}
        </> : null}
      </ol>
    </section>
  )
}

function SeasonConfigurationPage() {
  const { seasonId: seasonIdParam } = useParams()
  const seasonId = Number(seasonIdParam)
  const validId = Number.isInteger(seasonId) && seasonId > 0
  const [params, setParams] = useSearchParams()
  const sectionParam = params.get('section')
  const section = isSection(sectionParam) ? sectionParam : 'overview'
  const queryClient = useQueryClient()
  const { data: currentUser } = useCurrentUser()
  const isAdmin = currentUser?.role === 'Administrator'
  const [refreshing, setRefreshing] = useState(false)
  const [refreshStatus, setRefreshStatus] = useState('')
  const queryKey = [...seasonsQueryKey, seasonId, 'configuration']
  const query = useQuery({
    queryKey,
    queryFn: () => getSeasonConfiguration(seasonId),
    enabled: validId,
    staleTime: seasonDataStaleTime,
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
    } catch (error) {
      setRefreshStatus(`Refresh failed: ${errorMessage(error)}`)
    } finally {
      setRefreshing(false)
    }
  }

  if (!validId) return <p role="alert">Invalid season ID.</p>
  if (query.isPending) return <p>Loading season...</p>
  if (query.isError) return <div><p><Link to="/seasons">Back to seasons</Link></p>
    <p role="alert">{errorMessage(query.error)}</p>
    <button type="button" onClick={() => { void query.refetch() }}>Retry</button></div>
  const configuration = query.data
  const sport = configuration.sports.find((item) => String(item.id) === params.get('sport')) ?? configuration.sports[0]
  const division = sport?.divisions.find((item) => String(item.id) === params.get('division')) ?? sport?.divisions[0]

  function selectSport(value: string) {
    setParams({ section, sport: value })
  }

  function selectDivision(value: string) {
    if (sport) setParams({ section, sport: String(sport.id), division: value })
  }

  return (
    <div className="season-workspace">
      <header className="workspace-header">
        <div>
          <p className="breadcrumbs"><Link to="/seasons">Seasons</Link> / {configuration.season.name}</p>
          <h1>{configuration.season.name}</h1>
          <p className="muted-help">{configuration.season.year} · {configuration.season.season_status}</p>
        </div>
        <div>
          <button type="button" disabled={refreshing} onClick={() => { void refreshData() }}>
            {refreshing ? 'Refreshing...' : 'Refresh data'}
          </button>
          {refreshStatus ? <p role="status">{refreshStatus}</p> : null}
        </div>
      </header>
      <nav className="workspace-nav" aria-label="Season sections">
        {sections.map(([id, label]) => (
          <Link key={id} to={`?section=${id}`} aria-current={section === id ? 'page' : undefined}>{label}</Link>
        ))}
      </nav>
      {section === 'overview' ? <Overview configuration={configuration} isAdmin={isAdmin} /> : null}
      {section === 'setup' ? <div className="workspace-card"><SeasonSetupSection seasonId={seasonId} isAdmin={isAdmin} /></div> : null}
      {section !== 'overview' && section !== 'setup' ? (
        <section className="workspace-card">
          <h2>{sections.find(([id]) => id === section)?.[1]}</h2>
          {!configuration.sports.length ? <p>No sports configured yet. <Link to="?section=setup">View setup</Link>.</p> : (
            <div className="workspace-selectors">
              <label>Sport
                <select value={sport?.id ?? ''} onChange={(event) => selectSport(event.target.value)}>
                  {configuration.sports.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </label>
              <label>Division
                <select value={division?.id ?? ''} disabled={!sport?.divisions.length} onChange={(event) => selectDivision(event.target.value)}>
                  {!sport?.divisions.length ? <option value="">No divisions</option> : null}
                  {sport?.divisions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </label>
            </div>
          )}
          {sport && !sport.divisions.length ? <p>No divisions for this sport yet. <Link to="?section=setup">View setup</Link>.</p> : null}
          {sport && division && section === 'teams' ? (
            <SeasonTeamsSection key={division.id} divisionAssignmentId={division.id}
              minimumRosterSize={division.minimum_roster_size} seasonStatus={configuration.season.season_status}
              voterRequired={configuration.season.voter_required}
              registrationStartDate={configuration.season.registration_start_date}
              registrationEndDate={configuration.season.registration_end_date} isAdmin={isAdmin} isActive />
          ) : null}
          {sport && division && (section === 'schedule' || section === 'results' || section === 'standings') ? (
            <DivisionScheduleSection key={`${section}-${division.id}`} seasonId={seasonId} sportId={sport.id}
              divisionAssignmentId={division.id} seasonStatus={configuration.season.season_status}
              isAdmin={isAdmin} mode={section} />
          ) : null}
        </section>
      ) : null}
    </div>
  )
}

export default SeasonConfigurationPage
