import { useState } from 'react'
import { AxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { createSeason, getSeasons, seasonsQueryKey, transitionSeason, type CreateSeasonPayload, type Season, type SeasonStatus } from '../../shared/api/seasons'
import { useCurrentUser } from '../auth/useCurrentUser'

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

const nextSeasonStatus: Partial<Record<SeasonStatus, SeasonStatus>> = {
  PLANNING: 'REGISTRATION',
  REGISTRATION: 'ONGOING',
  ONGOING: 'COMPLETED',
  COMPLETED: 'ARCHIVED',
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ApiErrorResponse | undefined
    const validationMessage = response?.errors
      ? Object.values(response.errors).flat()[0]
      : undefined
    return validationMessage ?? response?.message ?? 'Could not complete the request.'
  }
  return 'Could not complete the request.'
}

function SeasonsPage() {
  const queryClient = useQueryClient()
  const { data: currentUser } = useCurrentUser()
  const [name, setName] = useState('')
  const [year, setYear] = useState(String(new Date().getFullYear()))
  const [registrationStartDate, setRegistrationStartDate] = useState('')
  const [registrationEndDate, setRegistrationEndDate] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [formError, setFormError] = useState('')
  const [transitionError, setTransitionError] = useState<{ seasonId: number; message: string } | null>(null)

  const seasonsQuery = useQuery({
    queryKey: seasonsQueryKey,
    queryFn: getSeasons,
  })

  const createSeasonMutation = useMutation({
    mutationFn: createSeason,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: seasonsQueryKey })
      setName('')
      setRegistrationStartDate('')
      setRegistrationEndDate('')
      setStartDate('')
      setEndDate('')
      setFormError('')
    },
    onError: (error: unknown) => setFormError(getErrorMessage(error)),
  })

  const transitionMutation = useMutation({
    mutationFn: ({ season, status }: { season: Season; status: SeasonStatus }) =>
      transitionSeason(season.id, status),
    onSuccess: async () => {
      setTransitionError(null)
      await queryClient.invalidateQueries({ queryKey: seasonsQueryKey })
    },
    onError: (error: unknown, variables) => setTransitionError({
      seasonId: variables.season.id,
      message: getErrorMessage(error),
    }),
  })

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError('')

    const payload: CreateSeasonPayload = {
      name: name.trim(),
      year: Number(year),
      registration_start_date: registrationStartDate || null,
      registration_end_date: registrationEndDate || null,
      start_date: startDate || null,
      end_date: endDate || null,
    }

    createSeasonMutation.mutate(payload)
  }

  return (
    <div style={{ display: 'grid', gap: '1.5rem' }}>
      <section>
        <h2 style={{ margin: '0 0 0.35rem' }}>Seasons</h2>
        <p style={{ margin: 0, color: '#64748b' }}>Current and completed league seasons.</p>
      </section>

      {currentUser?.role === 'Administrator' ? (
        <section style={{ maxWidth: '720px', background: 'white', padding: '1.25rem', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Create season</h3>
          <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '0.9rem' }}>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Season name
              <input required minLength={1} maxLength={150} value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Year
              <input required type="number" min="1" step="1" value={year} onChange={(event) => setYear(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Registration starts
              <input type="date" value={registrationStartDate} onChange={(event) => setRegistrationStartDate(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Registration ends
              <input type="date" value={registrationEndDate} onChange={(event) => setRegistrationEndDate(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Competition starts
              <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            </label>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              Competition ends
              <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            </label>
            <div style={{ display: 'flex', alignItems: 'end' }}>
              <button type="submit" disabled={createSeasonMutation.isPending}>
                {createSeasonMutation.isPending ? 'Creating...' : 'Create season'}
              </button>
            </div>
          </form>
          {formError ? <p role="alert" style={{ color: '#b91c1c' }}>{formError}</p> : null}
          {createSeasonMutation.isSuccess ? <p role="status" style={{ color: '#0f766e' }}>Season created.</p> : null}
        </section>
      ) : null}

      <section>
        {seasonsQuery.isPending ? <p>Loading seasons...</p> : null}
        {seasonsQuery.isError ? <p role="alert">{getErrorMessage(seasonsQuery.error)}</p> : null}
        {seasonsQuery.data?.length === 0 ? <p>No seasons have been created yet.</p> : null}
        {seasonsQuery.data && seasonsQuery.data.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid #cbd5e1' }}>
                  <th style={{ padding: '0.75rem' }}>Season</th>
                  <th style={{ padding: '0.75rem' }}>Registration</th>
                  <th style={{ padding: '0.75rem' }}>Competition</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Configuration</th>
                  {currentUser?.role === 'Administrator' ? <th style={{ padding: '0.75rem' }}>Action</th> : null}
                </tr>
              </thead>
              <tbody>
                {seasonsQuery.data.map((season) => (
                  <tr key={season.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <td style={{ padding: '0.75rem' }}>{season.name} ({season.year})</td>
                    <td style={{ padding: '0.75rem' }}>{season.registration_start_date ?? 'Not set'} to {season.registration_end_date ?? 'Not set'}</td>
                    <td style={{ padding: '0.75rem' }}>{season.start_date ?? 'Not set'} to {season.end_date ?? 'Not set'}</td>
                    <td style={{ padding: '0.75rem' }}>{season.season_status}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <Link to={`/seasons/${season.id}/configuration`}>View configuration</Link>
                    </td>
                    {currentUser?.role === 'Administrator' ? (
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          {nextSeasonStatus[season.season_status] ? (
                            <button
                              type="button"
                              disabled={transitionMutation.isPending}
                              onClick={() => {
                                setTransitionError(null)
                                transitionMutation.mutate({ season, status: nextSeasonStatus[season.season_status]! })
                              }}
                            >
                              Move to {nextSeasonStatus[season.season_status]}
                            </button>
                          ) : null}
                          {season.season_status === 'PLANNING' || season.season_status === 'REGISTRATION' ? (
                            <button
                              type="button"
                              disabled={transitionMutation.isPending}
                              onClick={() => {
                                setTransitionError(null)
                                transitionMutation.mutate({ season, status: 'ARCHIVED' })
                              }}
                            >
                              Archive
                            </button>
                          ) : null}
                          {!nextSeasonStatus[season.season_status] && season.season_status !== 'PLANNING' && season.season_status !== 'REGISTRATION' ? 'Complete' : null}
                          {transitionError?.seasonId === season.id ? (
                            <p role="alert" style={{ flexBasis: '100%', color: '#b91c1c', margin: 0 }}>
                              {transitionError.message}
                            </p>
                          ) : null}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  )
}

export default SeasonsPage