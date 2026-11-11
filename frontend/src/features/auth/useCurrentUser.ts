import { useQuery } from '@tanstack/react-query'
import { currentUserQueryKey, getCurrentUser } from '../../shared/api/auth'

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 60_000,
  })
}