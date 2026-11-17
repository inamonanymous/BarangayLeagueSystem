import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getGameStatistics, saveGameStatistics, type GameStatisticsInput } from '../../shared/api/seasons'
import { seasonDataStaleTime } from './queryOptions'

interface Props {
  gameId: number
  canEdit: boolean
  onEditingChange: (editing: boolean) => void
}

function GameStatisticsPanel({ gameId, canEdit, onEditingChange }: Props) {
  const client = useQueryClient()
  const key = ['game-statistics', gameId] as const
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<GameStatisticsInput | null>(null)
  const query = useQuery({ queryKey: key, queryFn: () => getGameStatistics(gameId), enabled: open, staleTime: seasonDataStaleTime })
  const save = useMutation({
    mutationFn: (input: GameStatisticsInput) => saveGameStatistics(gameId, {
      teams: input.teams.map((team) => ({
        ...team,
        players: team.players.map((player) => ({
          ...player, values: Object.fromEntries(Object.entries(player.values).filter(([, value]) => value.trim() !== '')),
        })),
      })),
    }),
    onSuccess: async () => {
      setDraft(null)
      onEditingChange(false)
      await Promise.all([
        client.invalidateQueries({ queryKey: key }),
        client.invalidateQueries({ queryKey: ['sport-statistics-configuration'] }),
      ])
    },
  })
  const message = save.error instanceof AxiosError
    ? (save.error.response?.data as { message?: string } | undefined)?.message ?? 'Could not save player statistics.'
    : 'Could not save player statistics.'

  return (
    <section>
      <button type="button" disabled={draft !== null} onClick={() => setOpen(!open)}>{open ? 'Hide player statistics' : 'View player statistics'}</button>
      {open && query.isPending ? <p>Loading player statistics...</p> : null}
      {open && query.isError ? <p role="alert">Could not load player statistics.</p> : null}
      {open && query.data ? <>
        {!query.data.configuration.types.length ? <p>No sport statistics configured. An Administrator must configure them before finalization.</p> : null}
        {draft ? (
          <form onSubmit={(event) => { event.preventDefault(); save.mutate(draft) }}>
            <p className="muted-help">Mark every rostered player Played or DNP. Complete every required statistic for players who played before finalization.</p>
            {draft.teams.map((team, teamIndex) => {
              const teamData = query.data.teams.find((item) => item.team_id === team.team_id)
              return <fieldset key={team.team_id}>
                <legend>{teamData?.name}</legend>
                {!team.players.length ? <p>No players on this roster.</p> : null}
                {query.data.configuration.allow_team_points ? <label>Unattributed team points
                  <input type="number" min="0" max="2147483647" step="1" value={team.team_points ?? ''} onChange={(event) => {
                    const value = event.target.value
                    setDraft({ teams: draft.teams.map((item, i) => i === teamIndex ? { ...item, team_points: value === '' ? null : Number(value) } : item) })
                  }} />
                </label> : null}
                {team.players.map((player, playerIndex) => {
                  const playerData = teamData?.players.find((item) => item.player_id === player.player_id)
                  const updatePlayer = (change: typeof player) => setDraft({
                    teams: draft.teams.map((item, i) => i === teamIndex ? {
                      ...item, players: item.players.map((entry, j) => j === playerIndex ? change : entry),
                    } : item),
                  })
                  return <fieldset key={player.player_id}>
                    <legend>#{playerData?.jersey_number} {playerData?.name}</legend>
                    <label>Participation <select value={player.status ?? ''} onChange={(event) => {
                      const status = event.target.value === 'PLAYED' ? 'PLAYED' : event.target.value === 'DNP' ? 'DNP' : null
                      updatePlayer({ ...player, status, values: status === 'PLAYED' ? player.values : {} })
                    }}>
                      <option value="">Not marked</option><option value="PLAYED">Played</option><option value="DNP">DNP</option>
                    </select></label>
                    {player.status === 'PLAYED' ? query.data.configuration.types.map((stat) => (
                      <label key={stat.id}>{stat.name}{stat.required ? ' (required)' : ''}
                        <input type="number" step="0.01" min={stat.is_scoring ? '0' : undefined}
                          value={player.values[String(stat.id)] ?? ''} onChange={(event) => updatePlayer({
                            ...player, values: { ...player.values, [String(stat.id)]: event.target.value },
                          })} />
                      </label>
                    )) : null}
                  </fieldset>
                })}
              </fieldset>
            })}
            <button type="submit" disabled={save.isPending}>Save player statistics</button>
            <button type="button" disabled={save.isPending} onClick={() => { setDraft(null); onEditingChange(false) }}>Cancel</button>
            {save.isError ? <p role="alert">{message}</p> : null}
          </form>
        ) : <>
          {query.data.teams.map((team) => <div key={team.team_id}>
            <h6>{team.name}</h6>
            {query.data.configuration.allow_team_points ? <p>Team points: {team.team_points ?? 'not entered'}</p> : null}
            {!team.players.length ? <p>No players on this roster.</p> : <ul>{team.players.map((player) => (
              <li key={player.player_id}>#{player.jersey_number} {player.name}: {player.status ?? 'Not marked'}
                {player.status === 'PLAYED' ? query.data.configuration.types.map((stat) =>
                  ` · ${stat.abbreviation}: ${player.values[String(stat.id)] ?? 'not entered'}`) : null}
              </li>
            ))}</ul>}
          </div>)}
          {canEdit && query.data.configuration.types.length ? <button type="button" onClick={() => {
            save.reset()
            setDraft({ teams: query.data.teams.map((team) => ({
              team_id: team.team_id, team_points: team.team_points,
              players: team.players.map(({ player_id, status, values }) => ({ player_id, status, values: { ...values } })),
            })) })
            onEditingChange(true)
          }}>Enter or edit player statistics</button> : null}
        </>}
      </> : null}
    </section>
  )
}

export default GameStatisticsPanel
