import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getStatisticConfiguration, saveStatisticConfiguration,
  type StatisticConfigurationInput,
} from '../../shared/api/seasons'
import { seasonDataStaleTime } from './queryOptions'

interface Props {
  sportId: number
  isAdmin: boolean
  isActive: boolean
}

function StatisticConfigurationEditor({ sportId, isAdmin, isActive }: Props) {
  const client = useQueryClient()
  const key = ['sport-statistics-configuration', sportId] as const
  const query = useQuery({ queryKey: key, queryFn: () => getStatisticConfiguration(sportId), enabled: isActive, staleTime: seasonDataStaleTime })
  const [draft, setDraft] = useState<StatisticConfigurationInput | null>(null)
  const save = useMutation({
    mutationFn: (input: StatisticConfigurationInput) => saveStatisticConfiguration(sportId, input),
    onSuccess: async () => {
      setDraft(null)
      await Promise.all([
        client.invalidateQueries({ queryKey: key }),
        client.invalidateQueries({ queryKey: ['game-statistics'] }),
      ])
    },
  })
  const message = save.error instanceof AxiosError
    ? (save.error.response?.data as { message?: string } | undefined)?.message ?? 'Could not save statistics configuration.'
    : 'Could not save statistics configuration.'

  function updateStatistic(index: number, changes: Partial<StatisticConfigurationInput['types'][number]>) {
    setDraft((current) => current && {
      ...current,
      types: current.types.map((item, i) => i === index ? { ...item, ...changes } : item),
    })
  }

  if (!isActive) return null
  if (query.isPending) return <p>Loading sport statistics...</p>
  if (query.isError) return <p role="alert">Could not load sport statistics configuration.</p>
  const config = query.data

  return (
    <section>
      <h5>Sport statistics</h5>
      <p className="muted-help">Configure statistics for this season sport. Definitions lock when game statistics are first saved.</p>
      {config.locked ? <p>Statistic definitions are locked.</p> : null}
      {!draft ? (
        <>
          {config.types.length ? <ul>{config.types.map((stat) => (
            <li key={stat.id}>{stat.name} ({stat.abbreviation}){stat.required ? ' · required' : ' · optional'}{stat.is_scoring ? ' · matches score' : ''}</li>
          ))}</ul> : <p>No statistics configured; games cannot be finalized yet.</p>}
          {config.allow_team_points ? <p>Unattributed team points are enabled.</p> : null}
          {isAdmin && !config.locked ? <button type="button" onClick={() => {
            save.reset()
            setDraft({ allow_team_points: config.allow_team_points, types: config.types.map(({ name, abbreviation, required, is_scoring }) => ({ name, abbreviation, required, is_scoring })) })
          }}>Configure statistics</button> : null}
        </>
      ) : (
        <form onSubmit={(event) => { event.preventDefault(); save.mutate(draft) }}>
          {draft.types.map((stat, index) => (
            <fieldset key={index}>
              <legend>Statistic {index + 1}</legend>
              <label>Name <input required maxLength={100} value={stat.name} onChange={(event) => updateStatistic(index, { name: event.target.value })} /></label>
              <label>Abbreviation <input required maxLength={20} value={stat.abbreviation} onChange={(event) => updateStatistic(index, { abbreviation: event.target.value })} /></label>
              <label><input type="checkbox" checked={stat.required} disabled={stat.is_scoring} onChange={(event) => updateStatistic(index, { required: event.target.checked })} /> Required for players who played</label>
              <label><input type="radio" name={`scoring-${sportId}`} checked={stat.is_scoring} onChange={() => setDraft({
                ...draft, types: draft.types.map((item, i) => ({ ...item, is_scoring: i === index, required: i === index || item.required })),
              })} /> Matches official score</label>
              <button type="button" onClick={() => setDraft({ ...draft, types: draft.types.filter((_, i) => i !== index), allow_team_points: stat.is_scoring ? false : draft.allow_team_points })}>Remove statistic</button>
            </fieldset>
          ))}
          <label><input type="radio" name={`scoring-${sportId}`} checked={!draft.types.some((item) => item.is_scoring)} onChange={() => setDraft({
            ...draft, allow_team_points: false, types: draft.types.map((item) => ({ ...item, is_scoring: false })),
          })} /> Do not match player statistics to the official score</label>
          <label><input type="checkbox" checked={draft.allow_team_points} disabled={!draft.types.some((item) => item.is_scoring)} onChange={(event) => setDraft({
            ...draft, allow_team_points: event.target.checked,
          })} /> Allow unattributed team points</label>
          <button type="button" onClick={() => setDraft({ ...draft, types: [...draft.types, { name: '', abbreviation: '', required: true, is_scoring: false }] })}>Add statistic</button>
          <button type="submit" disabled={save.isPending || !draft.types.length}>Save configuration</button>
          <button type="button" disabled={save.isPending} onClick={() => setDraft(null)}>Cancel</button>
          {save.isError ? <p role="alert">{message}</p> : null}
        </form>
      )}
    </section>
  )
}

export default StatisticConfigurationEditor
