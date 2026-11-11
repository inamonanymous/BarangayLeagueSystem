import axios from 'axios'

export interface CurrentUser {
  id: number
  username: string
  role: string
  is_active: boolean
}

export type UserRole = 'Administrator' | 'Encoder' | 'Viewer'

export interface CreatedUser {
  id: number
  username: string
  role: UserRole
  is_active: boolean
}

interface ApiResponse<T> {
  message: string
  data: T
}

export const currentUserQueryKey = ['currentUser'] as const

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

export async function loginUser(username: string, password: string): Promise<ApiResponse<CurrentUser>> {
  const response = await api.post<ApiResponse<CurrentUser>>('/auth/login', { username, password })
  return response.data
}

export async function logoutUser(): Promise<ApiResponse<unknown>> {
  const response = await api.post<ApiResponse<unknown>>('/auth/logout')
  return response.data
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<ApiResponse<CurrentUser>>('/auth/me')
  return response.data.data
}

export async function createUser(
  username: string,
  password: string,
  role: UserRole,
): Promise<ApiResponse<CreatedUser>> {
  const response = await api.post<ApiResponse<CreatedUser>>('/users/', {
    username,
    password,
    role,
  })
  return response.data
}
