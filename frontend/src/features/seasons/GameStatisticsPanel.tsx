import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getGameStatistics, saveGameStatistics, type GameStatisticsInput, type StatisticType } from '../../shared/api/seasons'
import SelectionTabs from '../../shared/components/SelectionTabs'
import { seasonDataStaleTime } from './queryOptions'

interface Props {
  gameId: number
  homeTeamId: number
  awayTeamId: number
  canEdit: boolean
  onEditingChange: (editing: boolean) => void
}

function statisticCents(raw: string | undefined, isScoring: boolean): bigint | null {
  const match = raw?.trim().match(/^([+-]?)(?:(\d+)(?:\.(\d*))?|\.(\d+))(?:e([+-]?\d+))?$/i)
  if (!match) return null
  const fraction = match[3] ?? match[4] ?? ''
  let digits = `${match[2] ?? ''}${fraction}`.replace(/^0+/, '')
  if (!digits) return 0n
  if (isScoring && match[1] === '-') return null
  const exponent = Number(match[5] ?? '0')
  if (!Number.isSafeInteger(exponent)) return null
  const shift = exponent - fraction.length + 2
  if (shift < 0) {
    const excess = -shift
    if (excess > digits.length || !digits.endsWith('0'.repeat(excess))) return null
    digits = digits.slice(0, -excess)
  } else {
    if (digits.length + shift > 10) return null
    digits += '0'.repeat(shift)
  }
  const cents = BigInt(digits || '0')
  if (cents > 9999999999n) return null
  return match[1] === '-' ? -cents : cents
}

function PlayerTotalsRow({ players, types }: {
  players: GameStatisticsInput['teams'][number]['players']
  types: StatisticType[]
}) {
  return <tfoot><tr>
    <th scope="row" colSpan={3}>Player total</th>
    {types.map((stat) => {
      let total = 0n
      let count = 0
      let incomplete = false
      for (const player of players) {
        if (player.status === null) {
          incomplete = true
        } else if (player.status === 'PLAYED') {
          const cents = statisticCents(player.values[String(stat.id)], stat.is_scoring)
          if (cents === null) {
            incomplete = true
          } else {
            total += cents
            count += 1
          }
        }
      }
      const absolute = total < 0n ? -total : total
      const fraction = (absolute % 100n).toString().padStart(2, '0').replace(/0+$/, '')
      const formatted = `${total < 0n ? '-' : ''}${absolute / 100n}${fraction ? `.${fraction}` : ''}`
      return <td key={stat.id}>{count ? formatted : '—'}{incomplete ? ' (partial)' : ''}</td>
    })}
  </tr></tfoot>
}

function GameStatisticsPanel({ gameId, homeTeamId, awayTeamId, canEdit, onEditingChange }: Props) {
  const client = useQueryClient()
  const key = ['game-statistics', gameId] as const
  const [open, setOpen] = useState(true)
  const [draft, setDraft] = useState<GameStatisticsInput | null>(null)
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const [validationError, setValidationError] = useState('')
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
      <h2>Player statistics</h2>
      <button type="button" aria-expanded={open} disabled={draft !== null} onClick={() => setOpen(!open)}>{open ? 'Hide player statistics' : 'View player statistics'}</button>
      {open && query.isPending ? <p>Loading player statistics...</p> : null}
      {open && query.isError ? <p role="alert">Could not load player statistics.</p> : null}
      {open && query.data ? <>
        {!query.data.configuration.types.length ? <p>No sport statistics configured. An Administrator must configure them before finalization.</p> : null}
        {query.data.configuration.types.length ? <p className="muted-help">Player totals add entered values for players marked Played. Partial totals have missing or invalid values, or unmarked players. Unattributed team points are separate.</p> : null}
        {draft ? (
          <form className="box-score-form" noValidate onChangeCapture={() => setValidationError('')} onSubmit={(event) => {
            event.preventDefault()
            const invalid = Array.from(event.currentTarget.querySelectorAll('input, select'))
              .find((element) => element instanceof HTMLInputElement && !element.validity.valid)
            if (invalid instanceof HTMLInputElement) {
              const teamId = Number(invalid.closest('[data-team-id]')?.getAttribute('data-team-id'))
              const teamName = query.data.teams.find((team) => team.team_id === teamId)?.name ?? 'Team'
              const player = invalid.closest('[data-player-name]')?.getAttribute('data-player-name')
              const field = invalid.getAttribute('data-stat-name') ?? invalid.closest('label')?.textContent?.trim() ?? 'Statistic'
              setSelectedTeamId(teamId)
              setValidationError(`${teamName}${player && player !== teamName ? ` - ${player}` : ''} - ${field}: ${invalid.validationMessage}`)
              return
            }
            setValidationError('')
            save.mutate(draft)
          }}>
            <p className="muted-help">Mark every rostered player Played or DNP. Columns marked * are required for players who played before finalization.</p>
            <p className="muted-help">Switch between teams to edit their statistics. Save applies changes to both teams.</p>
            <SelectionTabs label="Teams for player statistics" selectedId={selectedTeamId} onSelect={setSelectedTeamId}
              items={draft.teams.map((team, teamIndex) => {
                const teamData = query.data.teams.find((item) => item.team_id === team.team_id)
                const teamName = teamData?.name ?? `Team #${team.team_id}`
                const side = team.team_id === homeTeamId ? 'Home' : team.team_id === awayTeamId ? 'Away' : null
                return {
                  id: team.team_id,
                  label: side ? `${teamName} (${side})` : teamName,
                  content: <div data-team-id={team.team_id}>
                    {query.data.configuration.allow_team_points ? <label className="box-score-team-points">Unattributed team points
                      <input type="number" min="0" max="2147483647" step="1" value={team.team_points ?? ''} onChange={(event) => {
                        const value = event.target.value
                        setDraft({ teams: draft.teams.map((item, i) => i === teamIndex ? { ...item, team_points: value === '' ? null : Number(value) } : item) })
                      }} />
                    </label> : null}
                    {!team.players.length ? <p>No players on this roster.</p> : (
                      <div className="box-score-scroll" role="region" aria-label={`${teamName} statistics table`} tabIndex={0}>
                        <table className="box-score">
                          <caption>{teamName} player statistics</caption>
                          <thead><tr>
                            <th scope="col">#</th><th scope="col">Player</th><th scope="col">Participation</th>
                            {query.data.configuration.types.map((stat) => <th key={stat.id} scope="col"><abbr title={stat.name}>{stat.abbreviation}</abbr>{stat.required ? ' *' : ''}</th>)}
                          </tr></thead>
                          <tbody>{team.players.map((player, playerIndex) => {
                            const playerData = teamData?.players.find((item) => item.player_id === player.player_id)
                            const playerName = playerData?.name ?? `Player #${player.player_id}`
                            const updatePlayer = (change: typeof player) => setDraft({
                              teams: draft.teams.map((item, i) => i === teamIndex ? {
                                ...item, players: item.players.map((entry, j) => j === playerIndex ? change : entry),
                              } : item),
                            })
                            return <tr key={player.player_id} data-player-name={playerName}>
                              <td>{playerData?.jersey_number ?? '—'}</td>
                              <th scope="row">{playerName}</th>
                              <td><select aria-label={`Participation for ${playerName}`} value={player.status ?? ''} onChange={(event) => {
                                const status = event.target.value === 'PLAYED' ? 'PLAYED' : event.target.value === 'DNP' ? 'DNP' : null
                                updatePlayer({ ...player, status, values: status === 'PLAYED' ? player.values : {} })
                              }}>
                                <option value="">Not marked</option><option value="PLAYED">Played</option><option value="DNP">DNP</option>
                              </select></td>
                              {query.data.configuration.types.map((stat) => <td key={stat.id}>
                                {player.status === 'PLAYED' ? <input type="number" step="0.01" min={stat.is_scoring ? '0' : undefined}
                                  aria-label={`${stat.name}${stat.required ? ' (required)' : ''} for ${playerName}`} data-stat-name={stat.name}
                                  value={player.values[String(stat.id)] ?? ''} onChange={(event) => updatePlayer({
                                    ...player, values: { ...player.values, [String(stat.id)]: event.target.value },
                                  })} /> : '—'}
                              </td>)}
                            </tr>
                          })}</tbody>
                          <PlayerTotalsRow players={team.players} types={query.data.configuration.types} />
                        </table>
                      </div>
                    )}
                  </div>,
                }
              })} />
            {validationError ? <p role="alert">{validationError}</p> : null}
            <button type="submit" disabled={save.isPending}>Save player statistics</button>
            <button type="button" disabled={save.isPending} onClick={() => { setDraft(null); setValidationError(''); onEditingChange(false) }}>Cancel</button>
            {save.isError ? <p role="alert">{message}</p> : null}
          </form>
        ) : <>
          {query.data.teams.map((team) => <div key={team.team_id} className="box-score-team">
            <h3>{team.name}{team.team_id === homeTeamId ? ' (Home)' : team.team_id === awayTeamId ? ' (Away)' : ''}</h3>
            {query.data.configuration.allow_team_points ? <p>Team points: {team.team_points ?? 'not entered'}</p> : null}
            {!team.players.length ? <p>No players on this roster.</p> : (
              <div className="box-score-scroll" role="region" aria-label={`${team.name} statistics table`} tabIndex={0}>
                <table className="box-score">
                  <caption>{team.name} player statistics</caption>
                  <thead><tr>
                    <th scope="col">#</th><th scope="col">Player</th><th scope="col">Participation</th>
                    {query.data.configuration.types.map((stat) => <th key={stat.id} scope="col"><abbr title={stat.name}>{stat.abbreviation}</abbr></th>)}
                  </tr></thead>
                  <tbody>{team.players.map((player) => <tr key={player.player_id}>
                    <td>{player.jersey_number}</td><th scope="row">{player.name}</th>
                    <td>{player.status === 'PLAYED' ? 'Played' : player.status === 'DNP' ? 'DNP' : 'Not marked'}</td>
                    {query.data.configuration.types.map((stat) => <td key={stat.id}>
                      {player.status === 'PLAYED' ? player.values[String(stat.id)] ?? 'Not entered' : '—'}
                    </td>)}
                  </tr>)}</tbody>
                  <PlayerTotalsRow players={team.players} types={query.data.configuration.types} />
                </table>
              </div>
            )}
          </div>)}
          {canEdit && query.data.configuration.types.length ? <button type="button" onClick={() => {
            save.reset()
            setSelectedTeamId(null)
            setValidationError('')
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
