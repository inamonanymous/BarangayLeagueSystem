import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getDivisionGames, getSeasonConfiguration, getTeamsForDivision, seasonsQueryKey } from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'
import GameResultControls from './GameResultControls'
import { seasonDataStaleTime } from './queryOptions'

function GameDetailsPage() {
  const { seasonId: seasonParam, divisionId: divisionParam, gameId: gameParam } = useParams()
  const seasonId = Number(seasonParam)
  const divisionId = Number(divisionParam)
  const gameId = Number(gameParam)
  const validIds = [seasonId, divisionId, gameId].every((id) => Number.isInteger(id) && id > 0)
  const [params] = useSearchParams()
  const from = params.get('from') === 'schedule' ? 'schedule' : 'results'
  const { data: user } = useCurrentUser()
  const configuration = useQuery({
    queryKey: [...seasonsQueryKey, seasonId, 'configuration'],
    queryFn: () => getSeasonConfiguration(seasonId),
    enabled: validIds,
    staleTime: seasonDataStaleTime,
  })
  const sport = configuration.data?.sports.find((item) => item.divisions.some((division) => division.id === divisionId))
  const division = sport?.divisions.find((item) => item.id === divisionId)
  const games = useQuery({
    queryKey: ['division-games', divisionId],
    queryFn: () => getDivisionGames(divisionId),
    enabled: Boolean(sport),
    staleTime: seasonDataStaleTime,
  })
  const teams = useQuery({
    queryKey: ['season-teams', divisionId],
    queryFn: () => getTeamsForDivision(divisionId),
    enabled: Boolean(sport),
    staleTime: seasonDataStaleTime,
  })
  const back = `/seasons/${seasonId}/configuration?section=${from}${sport ? `&sport=${sport.id}&division=${divisionId}` : ''}`

  if (!validIds) return <p role="alert">Invalid game location.</p>
  if (configuration.isPending) return <p>Loading season...</p>
  if (configuration.isError) return <div><p role="alert">Could not load the season.</p>
    <button type="button" onClick={() => { void configuration.refetch() }}>Retry</button></div>
  if (!sport || !division) return <div><p role="alert">Division not found in this season.</p><Link to={back}>Back to season</Link></div>
  if (games.isPending || teams.isPending) return <p>Loading game...</p>
  if (games.isError || teams.isError) return <div><p role="alert">Could not load game or team details.</p>
    <button type="button" onClick={() => { void games.refetch(); void teams.refetch() }}>Retry</button></div>
  const game = games.data.find((item) => item.id === gameId)
  if (!game) return <div><p role="alert">Game not found in this division.</p><Link to={back}>Back to {from}</Link></div>
  const teamName = (id: number) => {
    const team = teams.data.find((item) => item.id === id)
    return team ? `${team.name}${team.is_archived ? ' (archived)' : ''}` : `Team #${id}`
  }
  const isAdmin = user?.role === 'Administrator'

  return (
    <div className="season-workspace">
      <p className="breadcrumbs"><Link to="/seasons">Seasons</Link> / <Link to={back}>{configuration.data.season.name} · {from}</Link> / Game</p>
      <section className="workspace-card">
        <p className="muted-help">{sport.name} · {division.name}</p>
        <h1>{teamName(game.home_team_id)} (Home) vs {teamName(game.away_team_id)} (Away)</h1>
        <p>{new Date(game.starts_at).toLocaleString()} – {new Date(game.ends_at).toLocaleString()} · {game.venue}</p>
        <GameResultControls game={game} divisionId={divisionId} isAdmin={isAdmin}
          homeTeamName={teamName(game.home_team_id)} awayTeamName={teamName(game.away_team_id)}
          canEncode={isAdmin || user?.role === 'Encoder'} seasonStatus={configuration.data.season.season_status} />
      </section>
    </div>
  )
}

export default GameDetailsPage
