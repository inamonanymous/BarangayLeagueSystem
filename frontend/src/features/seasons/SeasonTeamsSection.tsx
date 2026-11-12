import { useState } from 'react'
import { AxiosError } from 'axios'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getTeamsForDivision, registerTeam, setTeamArchived, updateTeam, type SeasonStatus, type SeasonTeam } from '../../shared/api/seasons'
import TeamRosterSection from './TeamRosterSection'

interface SeasonTeamsSectionProps {
  divisionAssignmentId: number
  minimumRosterSize: number
  seasonStatus: SeasonStatus
  registrationStartDate: string | null
  registrationEndDate: string | null
  isAdmin: boolean
}

interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const response = error.response?.data as ApiErrorResponse | undefined
    return (response?.errors ? Object.values(response.errors).flat()[0] : undefined)
      ?? response?.message
      ?? 'Could not load or register teams.'
  }
  return 'Could not load or register teams.'
}

function todayLocal(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function SeasonTeamsSection({
  divisionAssignmentId,
  minimumRosterSize,
  seasonStatus,
  registrationStartDate,
  registrationEndDate,
  isAdmin,
}: SeasonTeamsSectionProps) {
  const queryClient = useQueryClient()
  const queryKey = ['season-teams', divisionAssignmentId] as const
  const [name, setName] = useState('')
  const [barangay, setBarangay] = useState('')
  const [coachName, setCoachName] = useState('')
  const [managerName, setManagerName] = useState('')
  const [teamColor, setTeamColor] = useState('')
  const [editingTeam, setEditingTeam] = useState<SeasonTeam | null>(null)
  const [error, setError] = useState('')
  const [isRegisterFormOpen, setIsRegisterFormOpen] = useState(false)
  const teamsQuery = useQuery({
    queryKey,
    queryFn: () => getTeamsForDivision(divisionAssignmentId),
  })
  const registerMutation = useMutation({
    mutationFn: (payload: Omit<SeasonTeam, 'id' | 'season_sport_division_id' | 'is_archived' | 'created_at' | 'updated_at'>) =>
      registerTeam(divisionAssignmentId, payload),
    onSuccess: async () => {
      setName('')
      setBarangay('')
      setCoachName('')
      setManagerName('')
      setTeamColor('')
      setIsRegisterFormOpen(false)
      await queryClient.invalidateQueries({ queryKey })
    },
    onError: (caught) => setError(getErrorMessage(caught)),
  })
  const updateTeamMutation = useMutation({
    mutationFn: (team: SeasonTeam) => updateTeam(team.id, {
      name: team.name.trim(),
      barangay: team.barangay.trim(),
      coach_name: team.coach_name,
      manager_name: team.manager_name,
      team_color: team.team_color,
    }),
    onSuccess: async () => {
      setEditingTeam(null)
      setError('')
      await queryClient.invalidateQueries({ queryKey })
    },
    onError: (caught) => setError(getErrorMessage(caught)),
  })
  const archiveTeamMutation = useMutation({
    mutationFn: ({ teamId, archived }: { teamId: number; archived: boolean }) => setTeamArchived(teamId, archived),
    onSuccess: async () => {
      setError('')
      await queryClient.invalidateQueries({ queryKey })
    },
    onError: (caught) => setError(getErrorMessage(caught)),
  })

  const today = todayLocal()
  const hasRegistrationWindow = registrationStartDate !== null && registrationEndDate !== null
  const dateWindowOpen = !hasRegistrationWindow
    || (today >= registrationStartDate && today <= registrationEndDate)
  const canRegister = isAdmin && seasonStatus === 'REGISTRATION' && dateWindowOpen

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    registerMutation.mutate({
      name: name.trim(),
      barangay: barangay.trim(),
      coach_name: coachName.trim() || null,
      manager_name: managerName.trim() || null,
      team_color: teamColor.trim() || null,
    })
  }

  return (
    <section style={{ marginTop: '0.85rem', paddingTop: '0.75rem', borderTop: '1px solid #e2e8f0' }}>
      <h5 style={{ margin: '0 0 0.5rem' }}>
        Step 2: Register teams{teamsQuery.data
          ? ` (${teamsQuery.data.filter((team) => !team.is_archived).length} active)`
          : ''}
      </h5>
      <p style={{ margin: '0 0 0.5rem', color: '#64748b' }}>
        Register each team in this division, then add its players in the roster section.
      </p>
      {teamsQuery.isPending ? <p>Loading teams...</p> : null}
      {teamsQuery.isError ? <p role="alert">{getErrorMessage(teamsQuery.error)}</p> : null}
      {error ? <p role="alert">{error}</p> : null}
      {isAdmin ? (
        <div style={{ margin: '0.75rem 0' }}>
          <button
            type="button"
            disabled={!canRegister}
            onClick={() => {
              setError('')
              registerMutation.reset()
              setIsRegisterFormOpen(true)
            }}
          >
            Add team
          </button>
          {!canRegister ? (
            <p role="status" style={{ color: '#64748b', margin: '0.4rem 0 0' }}>
              {seasonStatus !== 'REGISTRATION' ? (
                <>Move the season to Registration first. <Link to="/seasons">Go to Seasons</Link>.</>
              ) : hasRegistrationWindow ? (
                today < registrationStartDate
                  ? `Registration opens on ${registrationStartDate}.`
                  : `Registration closed on ${registrationEndDate}.`
              ) : (
                'Team registration is currently unavailable.'
              )}
            </p>
          ) : null}
        </div>
      ) : (
        <p role="status" style={{ color: '#64748b' }}>Only an Administrator can add teams.</p>
      )}
      {registerMutation.isSuccess ? <p role="status">Team added.</p> : null}
      {canRegister && isRegisterFormOpen ? (
        <form onSubmit={handleSubmit} className="team-registration-form">
          <label style={{ display: 'grid', gap: '0.25rem' }}>Team name
            <input required maxLength={150} value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Barangay
            <input required maxLength={150} value={barangay} onChange={(event) => setBarangay(event.target.value)} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Coach
            <input maxLength={150} value={coachName} onChange={(event) => setCoachName(event.target.value)} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Manager
            <input maxLength={150} value={managerName} onChange={(event) => setManagerName(event.target.value)} />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>Team color
            <input maxLength={50} value={teamColor} onChange={(event) => setTeamColor(event.target.value)} />
          </label>
          <button type="submit" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? 'Registering...' : 'Register team'}
          </button>
          <button type="button" onClick={() => setIsRegisterFormOpen(false)}>Cancel</button>
        </form>
      ) : null}
      {teamsQuery.data?.length === 0 ? <p>No teams registered in this division yet.</p> : null}
      {teamsQuery.data?.length ? (
        <div className="season-team-list">
          {teamsQuery.data.map((team) => (
            <article key={team.id} className="season-team-card">
              {editingTeam?.id === team.id ? (
                <div className="season-team-edit-form">
                  <input aria-label="Team name" value={editingTeam.name} onChange={(event) => setEditingTeam({ ...editingTeam, name: event.target.value })} />
                  <input aria-label="Barangay" value={editingTeam.barangay} onChange={(event) => setEditingTeam({ ...editingTeam, barangay: event.target.value })} />
                  <input aria-label="Coach" value={editingTeam.coach_name ?? ''} onChange={(event) => setEditingTeam({ ...editingTeam, coach_name: event.target.value || null })} />
                  <input aria-label="Manager" value={editingTeam.manager_name ?? ''} onChange={(event) => setEditingTeam({ ...editingTeam, manager_name: event.target.value || null })} />
                  <input aria-label="Team color" value={editingTeam.team_color ?? ''} onChange={(event) => setEditingTeam({ ...editingTeam, team_color: event.target.value || null })} />
                  <button type="button" disabled={updateTeamMutation.isPending} onClick={() => updateTeamMutation.mutate(editingTeam)}>Save team</button>
                  <button type="button" onClick={() => setEditingTeam(null)}>Cancel</button>
                </div>
              ) : (
                <div className="season-team-card__header">
                  <div>
                    <h4 className="season-team-card__name">
                      {team.name}
                      {team.is_archived ? <span className="status-badge status-badge--muted">Archived</span> : null}
                    </h4>
                    <div className="season-team-card__details">
                      <span>Barangay: {team.barangay}</span>
                      {team.coach_name ? <span>Coach: {team.coach_name}</span> : null}
                      {team.manager_name ? <span>Manager: {team.manager_name}</span> : null}
                      {team.team_color ? <span>Team color: {team.team_color}</span> : null}
                    </div>
                  </div>
                  {isAdmin ? (
                    <span className="season-team-card__actions">
                      {!team.is_archived && canRegister ? <button type="button" onClick={() => setEditingTeam(team)}>Edit</button> : null}
                      <button
                        type="button"
                        disabled={archiveTeamMutation.isPending || (team.is_archived && !canRegister)}
                        onClick={() => archiveTeamMutation.mutate({ teamId: team.id, archived: !team.is_archived })}
                      >
                        {team.is_archived ? 'Restore' : 'Archive'}
                      </button>
                    </span>
                  ) : null}
                </div>
              )}
              {team.is_archived && isAdmin && !canRegister ? (
                <p className="muted-help">Restore is available during the season registration window.</p>
              ) : null}
              <TeamRosterSection
                teamId={team.id}
                teamArchived={team.is_archived}
                minimumRosterSize={minimumRosterSize}
                seasonStatus={seasonStatus}
                registrationStartDate={registrationStartDate}
                registrationEndDate={registrationEndDate}
                isAdmin={isAdmin}
              />
            </article>
          ))}
        </div>
      ) : null}
    </section>
  )
}

export default SeasonTeamsSection
