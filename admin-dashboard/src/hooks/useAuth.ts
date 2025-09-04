import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '@/lib/api';
import type { LoginCredentials, User } from '@/types';

// Auth state management
const getStoredUser = (): User | null => {
  try {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem('admin_user');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
};

const getStoredToken = (): string | null => {
  try {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('admin_token');
  } catch {
    return null;
  }
};

export function useAuth() {
  const queryClient = useQueryClient();

  // Get current user from cache or storage
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      const token = getStoredToken();
      if (!token) return null;

      // Try to get from storage first (instant)
      const storedUser = getStoredUser();
      if (storedUser) return storedUser;

      // Fallback to API verification
      return authAPI.me();
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: typeof window !== 'undefined' && !!getStoredToken(),
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => authAPI.login(credentials),
    onSuccess: (authResponse) => {
      // Ensure admin role
      if (authResponse.user.role !== 'admin') {
        throw new Error('Access denied. Admin privileges required.');
      }

      // Store auth data
      localStorage.setItem('admin_token', authResponse.access_token);
      localStorage.setItem('admin_user', JSON.stringify(authResponse.user));

      // Set cookie (remove secure for development)
      document.cookie = `admin_token=${authResponse.access_token}; path=/; max-age=${authResponse.expires_in}; samesite=lax`;

      // Update cache immediately
      queryClient.setQueryData(['auth', 'user'], authResponse.user);

      // Navigate immediately
      window.location.href = '/dashboard';
    },
    onError: (error: unknown) => {
      console.error('Login failed:', error);
    }
  });

  const logout = () => {
    // Clear storage
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');

    // Clear cookie
    document.cookie = 'admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';

    // Clear all queries
    queryClient.clear();

    // Navigate to login
    window.location.href = '/';
  };

  return {
    user: user || null,
    isAuthenticated: !!user,
    isLoading: isLoading || loginMutation.isPending,
    login: loginMutation.mutateAsync,
    logout,
    error: loginMutation.error,
  };
}
