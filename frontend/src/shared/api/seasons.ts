import axios from 'axios'

export type SeasonStatus = 'PLANNING' | 'REGISTRATION' | 'ONGOING' | 'COMPLETED' | 'ARCHIVED'

export interface Season {
  id: number
  name: string
  year: number
  registration_start_date: string | null
  registration_end_date: string | null
  start_date: string | null
  end_date: string | null
  season_status: SeasonStatus
  created_at: string | null
  updated_at: string | null
}

export interface CreateSeasonPayload {
  name: string
  year: number
  registration_start_date: string | null
  registration_end_date: string | null
  start_date: string | null
  end_date: string | null
}

interface ApiResponse<T> {
  message: string
  data: T
}

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

export const seasonsQueryKey = ['seasons'] as const

export async function getSeasons(): Promise<Season[]> {
  const response = await api.get<ApiResponse<Season[]>>('/seasons/')
  return response.data.data
}

export async function createSeason(payload: CreateSeasonPayload): Promise<Season> {
  const response = await api.post<ApiResponse<Season>>('/seasons/', payload)
  return response.data.data
}

export async function transitionSeason(seasonId: number, season_status: SeasonStatus): Promise<Season> {
  const response = await api.patch<ApiResponse<Season>>(`/seasons/${seasonId}/status`, { season_status })
  return response.data.data
}

export interface Sport {
  id: number
  name: string
  description: string | null
}

export interface Division {
  id: number
  name: string
  gender_policy: 'ANY' | 'MALE_ONLY' | 'FEMALE_ONLY' | 'MIXED'
  minimum_roster_size: number
  maximum_roster_size: number
}

export interface ConfiguredDivision extends Division {
  assignment_id: number
}

export interface SeasonSportConfiguration {
  id: number
  season_id: number
  sport_id: number
  sport: Sport
  divisions: ConfiguredDivision[]
}

export interface SeasonConfiguration {
  season: Season
  sports: SeasonSportConfiguration[]
}

export interface SeasonTeam {
  id: number
  season_sport_division_id: number
  name: string
  barangay: string
  coach_name: string | null
  manager_name: string | null
  team_color: string | null
  is_archived: boolean
  created_at: string | null
  updated_at: string | null
}

export async function getSeasonConfiguration(seasonId: number): Promise<SeasonConfiguration> {
  const response = await api.get<ApiResponse<SeasonConfiguration>>(`/seasons/${seasonId}/configuration`)
  return response.data.data
}

export async function getCatalogSports(): Promise<Sport[]> {
  const response = await api.get<ApiResponse<Sport[]>>('/catalogs/sports')
  return response.data.data
}

export async function getCatalogDivisions(): Promise<Division[]> {
  const response = await api.get<ApiResponse<Division[]>>('/catalogs/divisions')
  return response.data.data
}

export async function createCatalogSport(name: string, description: string): Promise<Sport> {
  const response = await api.post<ApiResponse<Sport>>('/catalogs/sports', { name, description })
  return response.data.data
}

export async function updateCatalogSport(sportId: number, name: string, description: string): Promise<Sport> {
  const response = await api.put<ApiResponse<Sport>>(`/catalogs/sports/${sportId}`, { name, description })
  return response.data.data
}

export async function deleteCatalogSport(sportId: number): Promise<void> {
  await api.delete(`/catalogs/sports/${sportId}`)
}

export async function createCatalogDivision(payload: {
  name: string
  gender_policy: Division['gender_policy']
  minimum_roster_size: number
  maximum_roster_size: number
}): Promise<Division> {
  const response = await api.post<ApiResponse<Division>>('/catalogs/divisions', payload)
  return response.data.data
}

export async function updateCatalogDivision(divisionId: number, payload: {
  name: string
  gender_policy: Division['gender_policy']
  minimum_roster_size: number
  maximum_roster_size: number
}): Promise<Division> {
  const response = await api.put<ApiResponse<Division>>(`/catalogs/divisions/${divisionId}`, payload)
  return response.data.data
}

export async function deleteCatalogDivision(divisionId: number): Promise<void> {
  await api.delete(`/catalogs/divisions/${divisionId}`)
}

export async function assignSportToSeason(seasonId: number, sport_id: number): Promise<void> {
  await api.post(`/seasons/${seasonId}/sports`, { sport_id })
}

export async function assignDivisionToSeasonSport(
  seasonSportId: number,
  division_id: number,
): Promise<void> {
  await api.post(`/seasons/sports/${seasonSportId}/divisions`, { division_id })
}

export async function removeSportFromSeason(seasonId: number, seasonSportId: number): Promise<void> {
  await api.delete(`/seasons/${seasonId}/sports/${seasonSportId}`)
}

export async function removeDivisionFromSeasonSport(
  seasonSportId: number,
  assignmentId: number,
): Promise<void> {
  await api.delete(`/seasons/sports/${seasonSportId}/divisions/${assignmentId}`)
}

export async function getTeamsForDivision(divisionAssignmentId: number): Promise<SeasonTeam[]> {
  const response = await api.get<ApiResponse<SeasonTeam[]>>(
    `/season-sport-divisions/${divisionAssignmentId}/teams`,
  )
  return response.data.data
}

export async function registerTeam(
  divisionAssignmentId: number,
  payload: Omit<SeasonTeam, 'id' | 'season_sport_division_id' | 'is_archived' | 'created_at' | 'updated_at'>,
): Promise<SeasonTeam> {
  const response = await api.post<ApiResponse<SeasonTeam>>(
    `/season-sport-divisions/${divisionAssignmentId}/teams`,
    payload,
  )
  return response.data.data
}

export interface Player {
  id: number
  first_name: string
  middle_name: string | null
  last_name: string
  birthdate: string
  gender: string
  address: string
  is_archived: boolean
}

export interface RosterEntry {
  id: number
  season_team_id: number
  player_id: number
  jersey_number: string
  player: Player
}

export async function updateTeam(teamId: number, payload: Omit<SeasonTeam, 'id' | 'season_sport_division_id' | 'is_archived' | 'created_at' | 'updated_at'>): Promise<SeasonTeam> {
  const response = await api.put<ApiResponse<SeasonTeam>>(`/season-teams/${teamId}`, payload)
  return response.data.data
}

export async function setTeamArchived(teamId: number, is_archived: boolean): Promise<SeasonTeam> {
  const response = await api.patch<ApiResponse<SeasonTeam>>(`/season-teams/${teamId}/archive`, { is_archived })
  return response.data.data
}

export async function getPlayers(includeArchived = false): Promise<Player[]> {
  const response = await api.get<ApiResponse<Player[]>>('/players/', {
    params: { include_archived: includeArchived },
  })
  return response.data.data
}

export async function createPlayer(payload: Omit<Player, 'id' | 'is_archived'>): Promise<Player> {
  const response = await api.post<ApiResponse<Player>>('/players/', payload)
  return response.data.data
}

export async function updatePlayer(playerId: number, payload: Omit<Player, 'id' | 'is_archived'>): Promise<Player> {
  const response = await api.put<ApiResponse<Player>>(`/players/${playerId}`, payload)
  return response.data.data
}

export async function setPlayerArchived(playerId: number, is_archived: boolean): Promise<Player> {
  const response = await api.patch<ApiResponse<Player>>(`/players/${playerId}/archive`, { is_archived })
  return response.data.data
}

export async function getTeamRoster(teamId: number): Promise<RosterEntry[]> {
  const response = await api.get<ApiResponse<RosterEntry[]>>(`/season-teams/${teamId}/roster`)
  return response.data.data
}

export async function addPlayerToRoster(teamId: number, payload: {
  player_id: number
  jersey_number: string
  voter_verified: boolean
  voter_number: string | null
  eligibility_notes: string | null
}): Promise<RosterEntry> {
  const response = await api.post<ApiResponse<RosterEntry>>(`/season-teams/${teamId}/roster`, payload)
  return response.data.data
}

export async function updateRosterEntry(teamId: number, rosterId: number, jersey_number: string): Promise<RosterEntry> {
  const response = await api.put<ApiResponse<RosterEntry>>(`/season-teams/${teamId}/roster/${rosterId}`, { jersey_number })
  return response.data.data
}

export async function removePlayerFromRoster(teamId: number, rosterId: number): Promise<void> {
  await api.delete(`/season-teams/${teamId}/roster/${rosterId}`)
}