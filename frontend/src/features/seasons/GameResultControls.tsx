import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { finalizeGame, reopenGame, saveGameResult, type ScheduledGame, type SeasonStatus } from '../../shared/api/seasons'
import GameStatisticsPanel from './GameStatisticsPanel'

interface Props {
  game: ScheduledGame
  divisionId: number
  isAdmin: boolean
  canEncode: boolean
  seasonStatus: SeasonStatus
}

function GameResultControls({ game, divisionId, isAdmin, canEncode, seasonStatus }: Props) {
  const client = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [home, setHome] = useState('')
  const [away, setAway] = useState('')
  const [reason, setReason] = useState('')
  const [reopening, setReopening] = useState(false)
  const [editingStatistics, setEditingStatistics] = useState(false)
  const refresh = async () => {
    await Promise.all([
      client.invalidateQueries({ queryKey: ['division-games', divisionId] }),
      client.invalidateQueries({ queryKey: ['division-standings', divisionId] }),
    ])
  }
  const save = useMutation({
    mutationFn: () => saveGameResult(game.id, Number(home), Number(away)),
    onSuccess: async () => { setEditing(false); await refresh() },
  })
  const finalize = useMutation({ mutationFn: () => finalizeGame(game.id), onSuccess: refresh })
  const reopen = useMutation({
    mutationFn: () => reopenGame(game.id, reason),
    onSuccess: async () => { setReason(''); setReopening(false); await refresh() },
  })
  const error = save.error ?? finalize.error ?? reopen.error
  const message = error instanceof AxiosError
    ? (error.response?.data as { message?: string } | undefined)?.message ?? 'Result request failed.'
    : 'Result request failed.'
  const canChange = seasonStatus === 'ONGOING' && new Date(game.ends_at).getTime() <= Date.now()
  const busy = save.isPending || finalize.isPending || reopen.isPending

  return (
    <div>
      <p>Result: {game.result_status}{game.home_score !== null && game.away_score !== null
        ? ` · ${game.home_score} – ${game.away_score}` : ' · No scores entered'}</p>
      {error ? <p role="alert">{message}</p> : null}
      <GameStatisticsPanel gameId={game.id}
        canEdit={canEncode && canChange && game.result_status !== 'FINALIZED'}
        onEditingChange={setEditingStatistics} />
      {canEncode && canChange && game.result_status !== 'FINALIZED' ? (
        editing ? (
          <form onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
            <label>Home score <input required type="number" min="0" step="1" value={home} onChange={(event) => setHome(event.target.value)} /></label>
            <label>Away score <input required type="number" min="0" step="1" value={away} onChange={(event) => setAway(event.target.value)} /></label>
            <button type="submit" disabled={busy}>Save scores</button>
            <button type="button" onClick={() => setEditing(false)}>Cancel</button>
          </form>
        ) : <button type="button" disabled={busy} onClick={() => {
          setHome(game.home_score?.toString() ?? ''); setAway(game.away_score?.toString() ?? '')
          save.reset(); setEditing(true)
        }}>Enter or edit scores</button>
      ) : null}
      {isAdmin && canChange && game.result_status === 'FOR_ENCODING' ? (
        <button type="button" disabled={busy || editingStatistics} onClick={() => finalize.mutate()}>Finalize result</button>
      ) : null}
      {isAdmin && canChange && game.result_status === 'FINALIZED' ? (
        reopening ? (
          <form onSubmit={(event) => { event.preventDefault(); reopen.mutate() }}>
            <label>Reason for reopening <input required maxLength={2000} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
            <button type="submit" disabled={busy}>Reopen result</button>
            <button type="button" onClick={() => setReopening(false)}>Cancel</button>
          </form>
        ) : <button type="button" disabled={busy} onClick={() => { reopen.reset(); setReopening(true) }}>Reopen result</button>
      ) : null}
    </div>
  )
}

export default GameResultControls
