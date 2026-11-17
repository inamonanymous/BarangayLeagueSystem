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

export interface SeasonSportConfiguration {
  id: number
  season_id: number
  name: string
  description: string | null
  divisions: ConfiguredDivision[]
}

export interface ConfiguredDivision {
  id: number
  season_sport_id: number
  name: string
  gender_policy: 'ANY' | 'MALE_ONLY' | 'FEMALE_ONLY' | 'MIXED'
  minimum_roster_size: number
  maximum_roster_size: number
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
  const configuration = response.data.data
  if (configuration.sports.some((sport) =>
    typeof sport.name !== 'string'
    || sport.divisions.some((division) => division.season_sport_id !== sport.id)
  )) {
    throw new Error('The backend is using an older season configuration. Your data may still exist; back up and migrate the database, then restart the backend before continuing.')
  }
  return configuration
}

export async function createSeasonSport(seasonId: number, name: string, description: string): Promise<Omit<SeasonSportConfiguration, 'divisions'>> {
  const response = await api.post<ApiResponse<Omit<SeasonSportConfiguration, 'divisions'>>>(`/seasons/${seasonId}/sports`, { name, description })
  return response.data.data
}

export async function updateSeasonSport(seasonId: number, sportId: number, name: string, description: string): Promise<Omit<SeasonSportConfiguration, 'divisions'>> {
  const response = await api.put<ApiResponse<Omit<SeasonSportConfiguration, 'divisions'>>>(`/seasons/${seasonId}/sports/${sportId}`, { name, description })
  return response.data.data
}

export type DivisionPayload = {
  name: string
  gender_policy: ConfiguredDivision['gender_policy']
  minimum_roster_size: number
  maximum_roster_size: number
}

export async function createSeasonDivision(sportId: number, payload: DivisionPayload): Promise<ConfiguredDivision> {
  const response = await api.post<ApiResponse<ConfiguredDivision>>(`/seasons/sports/${sportId}/divisions`, payload)
  return response.data.data
}

export async function updateSeasonDivision(sportId: number, divisionId: number, payload: DivisionPayload): Promise<ConfiguredDivision> {
  const response = await api.put<ApiResponse<ConfiguredDivision>>(`/seasons/sports/${sportId}/divisions/${divisionId}`, payload)
  return response.data.data
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

export interface ScheduledGame {
  id: number
  season_sport_division_id: number
  home_team_id: number
  away_team_id: number
  venue: string
  starts_at: string
  ends_at: string
  result_status: 'SCHEDULED' | 'FOR_ENCODING' | 'FINALIZED'
  home_score: number | null
  away_score: number | null
  finalized_at: string | null
  finalized_by: number | null
}

export type GameScheduleDetails = Pick<ScheduledGame, 'venue' | 'starts_at' | 'ends_at'>
export type NewGameSchedule = GameScheduleDetails & Pick<ScheduledGame, 'home_team_id' | 'away_team_id'>

export interface Standing {
  rank: number
  team_id: number
  team_name: string
  is_archived: boolean
  wins: number
  losses: number
}

export interface StatisticType {
  id: number
  name: string
  abbreviation: string
  required: boolean
  is_scoring: boolean
}

export interface StatisticConfiguration {
  season_sport_id: number
  locked: boolean
  allow_team_points: boolean
  types: StatisticType[]
}

export interface GameStatistics {
  configuration: StatisticConfiguration
  teams: {
    team_id: number
    name: string
    team_points: number | null
    players: {
      player_id: number
      name: string
      jersey_number: string
      status: 'PLAYED' | 'DNP' | null
      values: Record<string, string>
    }[]
  }[]
}

export type StatisticConfigurationInput = {
  allow_team_points: boolean
  types: Omit<StatisticType, 'id'>[]
}

export type GameStatisticsInput = {
  teams: {
    team_id: number
    team_points: number | null
    players: Pick<GameStatistics['teams'][number]['players'][number], 'player_id' | 'status' | 'values'>[]
  }[]
}

export async function getStatisticConfiguration(sportId: number): Promise<StatisticConfiguration> {
  const response = await api.get<ApiResponse<StatisticConfiguration>>(`/season-sports/${sportId}/statistics-configuration`)
  return response.data.data
}

export async function saveStatisticConfiguration(sportId: number, payload: StatisticConfigurationInput): Promise<StatisticConfiguration> {
  const response = await api.put<ApiResponse<StatisticConfiguration>>(`/season-sports/${sportId}/statistics-configuration`, payload)
  return response.data.data
}

export async function getGameStatistics(gameId: number): Promise<GameStatistics> {
  const response = await api.get<ApiResponse<GameStatistics>>(`/games/${gameId}/statistics`)
  return response.data.data
}

export async function saveGameStatistics(gameId: number, payload: GameStatisticsInput): Promise<GameStatistics> {
  const response = await api.put<ApiResponse<GameStatistics>>(`/games/${gameId}/statistics`, payload)
  return response.data.data
}

export async function getStandings(assignmentId: number): Promise<Standing[]> {
  const response = await api.get<ApiResponse<Standing[]>>(`/season-sport-divisions/${assignmentId}/standings`)
  return response.data.data
}

export async function saveGameResult(gameId: number, home_score: number, away_score: number): Promise<ScheduledGame> {
  const response = await api.put<ApiResponse<ScheduledGame>>(`/games/${gameId}/result`, { home_score, away_score })
  return response.data.data
}

export async function finalizeGame(gameId: number): Promise<ScheduledGame> {
  const response = await api.post<ApiResponse<ScheduledGame>>(`/games/${gameId}/finalize`)
  return response.data.data
}

export async function reopenGame(gameId: number, reason: string): Promise<ScheduledGame> {
  const response = await api.post<ApiResponse<ScheduledGame>>(`/games/${gameId}/reopen`, { reason })
  return response.data.data
}

export async function getDivisionGames(assignmentId: number): Promise<ScheduledGame[]> {
  const response = await api.get<ApiResponse<ScheduledGame[]>>(
    `/season-sport-divisions/${assignmentId}/games`,
  )
  return response.data.data
}

export async function scheduleGame(
  assignmentId: number,
  payload: NewGameSchedule,
): Promise<ScheduledGame> {
  const response = await api.post<ApiResponse<ScheduledGame>>(
    `/season-sport-divisions/${assignmentId}/games`, payload,
  )
  return response.data.data
}

export async function rescheduleGame(gameId: number, payload: GameScheduleDetails): Promise<ScheduledGame> {
  const response = await api.put<ApiResponse<ScheduledGame>>(`/games/${gameId}/schedule`, payload)
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

export async function getAvailablePlayers(teamId: number): Promise<Player[]> {
  const response = await api.get<ApiResponse<Player[]>>(`/season-teams/${teamId}/available-players`)
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