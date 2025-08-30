import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { businessAPI, utilityAPI } from '@/lib/api';
import type { Business, BusinessCreate, BusinessUpdate } from '@/types';

// Query Keys
export const businessKeys = {
  all: ['businesses'] as const,
  lists: () => [...businessKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...businessKeys.lists(), filters] as const,
  details: () => [...businessKeys.all, 'detail'] as const,
  detail: (id: number) => [...businessKeys.details(), id] as const,
  search: (query: string) => [...businessKeys.all, 'search', query] as const,
};

// Businesses Query
export function useBusinesses(params?: { skip?: number; limit?: number; active_only?: boolean }) {
  return useQuery({
    queryKey: businessKeys.list(params),
    queryFn: () => businessAPI.list(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Single Business Query
export function useBusiness(id: number) {
  return useQuery({
    queryKey: businessKeys.detail(id),
    queryFn: () => businessAPI.get(id),
    enabled: !!id,
  });
}

// Search Businesses
export function useSearchBusinesses(query: string) {
  return useQuery({
    queryKey: businessKeys.search(query),
    queryFn: () => businessAPI.search(query),
    enabled: query.length > 2,
    staleTime: 1 * 60 * 1000, // 1 minute for search
  });
}

// Create Business Mutation
export function useCreateBusiness() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BusinessCreate) => businessAPI.create(data),
    onSuccess: () => {
      // Invalidate all business queries
      queryClient.invalidateQueries({ queryKey: businessKeys.all });
    },
  });
}

// Update Business Mutation
export function useUpdateBusiness() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: BusinessUpdate }) => 
      businessAPI.update(id, data),
    onSuccess: (updatedBusiness) => {
      // Update the specific business in cache
      queryClient.setQueryData(
        businessKeys.detail(updatedBusiness.id),
        updatedBusiness
      );
      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: businessKeys.lists() });
    },
  });
}

// Deactivate Business Mutation
export function useDeactivateBusiness() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => businessAPI.deactivate(id),
    onSuccess: (_, id) => {
      // Update cache to mark as inactive
      queryClient.setQueryData(
        businessKeys.detail(id),
        (old: Business | undefined) => 
          old ? { ...old, is_active: false } : undefined
      );
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: businessKeys.lists() });
    },
  });
}

// System Health Query
export function useSystemHealth() {
  return useQuery({
    queryKey: ['system', 'health'],
    queryFn: () => utilityAPI.health(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}