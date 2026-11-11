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

export interface SeasonSportConfiguration {
  id: number
  season_id: number
  sport_id: number
  sport: Sport
  divisions: Division[]
}

export interface SeasonConfiguration {
  season: Season
  sports: SeasonSportConfiguration[]
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

export async function createCatalogDivision(payload: {
  name: string
  gender_policy: Division['gender_policy']
  minimum_roster_size: number
  maximum_roster_size: number
}): Promise<Division> {
  const response = await api.post<ApiResponse<Division>>('/catalogs/divisions', payload)
  return response.data.data
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