import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getDivisionGames, getTeamsForDivision, rescheduleGame, scheduleGame, type ScheduledGame, type SeasonStatus } from '../../shared/api/seasons'
import { seasonDataStaleTime } from './queryOptions'

interface Props {
  divisionAssignmentId: number
  seasonStatus: SeasonStatus
  isAdmin: boolean
  isActive: boolean
}

function errorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as { message?: string; errors?: Record<string, string[]> } | undefined
    return (body?.errors ? Object.values(body.errors).flat()[0] : undefined)
      ?? body?.message ?? 'Could not load or schedule games.'
  }
  return 'Could not load or schedule games.'
}

function DivisionScheduleSection({ divisionAssignmentId, seasonStatus, isAdmin, isActive }: Props) {
  const queryClient = useQueryClient()
  const queryKey = ['division-games', divisionAssignmentId] as const
  const [home, setHome] = useState('')
  const [away, setAway] = useState('')
  const [venue, setVenue] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [editingGame, setEditingGame] = useState<ScheduledGame | null>(null)
  const games = useQuery({ queryKey, queryFn: () => getDivisionGames(divisionAssignmentId), enabled: isActive, staleTime: seasonDataStaleTime })
  const teams = useQuery({
    queryKey: ['season-teams', divisionAssignmentId],
    queryFn: () => getTeamsForDivision(divisionAssignmentId),
    enabled: isActive,
    staleTime: seasonDataStaleTime,
  })
  const create = useMutation({
    mutationFn: () => scheduleGame(divisionAssignmentId, {
      home_team_id: Number(home), away_team_id: Number(away),
      venue: venue.trim(), starts_at: startsAt, ends_at: endsAt,
    }),
    onSuccess: async () => {
      setHome('')
      setAway('')
      setVenue('')
      setStartsAt('')
      setEndsAt('')
      await queryClient.invalidateQueries({ queryKey })
    },
  })
  const reschedule = useMutation({
    mutationFn: (game: ScheduledGame) => rescheduleGame(game.id, {
      venue: game.venue.trim(),
      starts_at: game.starts_at,
      ends_at: game.ends_at,
    }),
    onSuccess: async () => {
      setEditingGame(null)
      await queryClient.invalidateQueries({ queryKey })
    },
  })
  const activeTeams = teams.data?.filter((team) => !team.is_archived) ?? []

  function teamName(id: number): string {
    const team = teams.data?.find((item) => item.id === id)
    return team ? `${team.name}${team.is_archived ? ' (archived)' : ''}` : `Team #${id}`
  }

  return (
    <section className="division-schedule">
      <h5>Game schedule</h5>
      <p className="muted-help">Times are local. Games cannot overlap for either team or the same venue.</p>
      {isAdmin && seasonStatus === 'ONGOING' ? (
        <p className="muted-help">Reschedule before the game starts; the new start must also be in the future.</p>
      ) : null}
      {games.isPending || teams.isPending ? <p>Loading schedule...</p> : null}
      {games.isError ? <p role="alert">{errorMessage(games.error)}</p> : null}
      {teams.isError ? <p role="alert">{errorMessage(teams.error)}</p> : null}
      {games.data?.length === 0 ? <p>No games scheduled yet.</p> : null}
      {games.data?.length ? (
        <ul className="schedule-list">
          {games.data.map((game) => (
            <li key={game.id} className="schedule-entry">
              <strong>{teamName(game.home_team_id)} vs {teamName(game.away_team_id)}</strong>
              <span>{new Date(game.starts_at).toLocaleString()} - {new Date(game.ends_at).toLocaleString()}</span>
              <span>Venue: {game.venue}</span>
              {editingGame?.id === game.id && isAdmin && seasonStatus === 'ONGOING' ? (
                <form className="schedule-form" onSubmit={(event) => {
                  event.preventDefault()
                  reschedule.mutate(editingGame)
                }}>
                  <label>Venue
                    <input required maxLength={150} value={editingGame.venue} onChange={(event) => setEditingGame({ ...editingGame, venue: event.target.value })} />
                  </label>
                  <label>Start
                    <input required type="datetime-local" step="1" value={editingGame.starts_at} onChange={(event) => setEditingGame({ ...editingGame, starts_at: event.target.value })} />
                  </label>
                  <label>End
                    <input required type="datetime-local" step="1" value={editingGame.ends_at} onChange={(event) => setEditingGame({ ...editingGame, ends_at: event.target.value })} />
                  </label>
                  <button type="submit" disabled={reschedule.isPending}>
                    {reschedule.isPending ? 'Saving...' : 'Save schedule'}
                  </button>
                  <button type="button" disabled={reschedule.isPending} onClick={() => { setEditingGame(null); reschedule.reset() }}>Cancel</button>
                  {reschedule.isError ? <p role="alert">{errorMessage(reschedule.error)}</p> : null}
                </form>
              ) : isAdmin && seasonStatus === 'ONGOING' ? (
                <button type="button" disabled={reschedule.isPending} onClick={() => { reschedule.reset(); setEditingGame({ ...game }) }}>
                  Reschedule
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {reschedule.isSuccess ? <p role="status">Game rescheduled.</p> : null}
      {isAdmin && seasonStatus !== 'ONGOING' ? <p className="muted-help">Scheduling is available when the season is Ongoing.</p> : null}
      {isAdmin && seasonStatus === 'ONGOING' && !teams.isError ? (
        <>
          {activeTeams.length < 2 && !teams.isPending ? <p>At least two active teams are needed to schedule a game.</p> : null}
          <form className="schedule-form" onSubmit={(event) => { event.preventDefault(); create.mutate() }}>
            <label>Home team
              <select required value={home} onChange={(event) => {
                setHome(event.target.value)
                if (event.target.value === away) setAway('')
              }}>
                <option value="">Select team</option>
                {activeTeams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}
              </select>
            </label>
            <label>Away team
              <select required value={away} onChange={(event) => setAway(event.target.value)}>
                <option value="">Select team</option>
                {activeTeams.filter((team) => String(team.id) !== home).map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}
              </select>
            </label>
            <label>Venue
              <input required maxLength={150} value={venue} onChange={(event) => setVenue(event.target.value)} />
            </label>
            <label>Start
              <input required type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} />
            </label>
            <label>End
              <input required type="datetime-local" value={endsAt} onChange={(event) => setEndsAt(event.target.value)} />
            </label>
            <button type="submit" disabled={create.isPending || activeTeams.length < 2}>
              {create.isPending ? 'Scheduling...' : 'Schedule game'}
            </button>
          </form>
          {create.isError ? <p role="alert">{errorMessage(create.error)}</p> : null}
          {create.isSuccess ? <p role="status">Game scheduled.</p> : null}
        </>
      ) : null}
    </section>
  )
}

export default DivisionScheduleSection
