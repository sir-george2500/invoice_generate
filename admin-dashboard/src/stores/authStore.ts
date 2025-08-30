import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import type { User, LoginCredentials, ApiError } from '@/types';
import { authAPI } from '@/lib/api';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: ApiError | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => void;
  verifyToken: () => Promise<void>;
  clearError: () => void;
  
  // Internal actions
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: ApiError | null) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const authResponse = await authAPI.login(credentials);
          
          // Ensure user is admin
          if (authResponse.user.role !== 'admin') {
            throw new Error('Access denied. Admin privileges required.');
          }

          // Store tokens and user data (only on client)
          if (typeof window !== 'undefined') {
            localStorage.setItem('admin_token', authResponse.access_token);
            localStorage.setItem('admin_user', JSON.stringify(authResponse.user));
            
            // Set cookie for route protection (remove secure flag for development)
            document.cookie = `admin_token=${authResponse.access_token}; path=/; max-age=${authResponse.expires_in}; samesite=lax`;
          }

          set((state) => {
            state.user = authResponse.user;
            state.isAuthenticated = true;
            state.isLoading = false;
          });

          return true;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = {
              message: apiError.message || 'Login failed',
              status: apiError.status,
            };
            state.isLoading = false;
          });
          return false;
        }
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          
          // Clear cookie
          document.cookie = 'admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        }
        
        set((state) => {
          state.user = null;
          state.isAuthenticated = false;
          state.error = null;
        });
      },

      verifyToken: async () => {
        if (typeof window === 'undefined') return;
        
        const token = localStorage.getItem('admin_token');
        const savedUser = localStorage.getItem('admin_user');

        if (!token || !savedUser) {
          get().logout();
          return;
        }

        set((state) => {
          state.isLoading = true;
        });

        try {
          const result = await authAPI.verify();
          
          if (result.valid) {
            const user = JSON.parse(savedUser);
            set((state) => {
              state.user = user;
              state.isAuthenticated = true;
              state.isLoading = false;
            });
          } else {
            get().logout();
          }
        } catch {
          get().logout();
        } finally {
          set((state) => {
            state.isLoading = false;
          });
        }
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      // Internal actions
      setUser: (user) => {
        set((state) => {
          state.user = user;
          state.isAuthenticated = !!user;
        });
      },

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading;
        });
      },

      setError: (error) => {
        set((state) => {
          state.error = error;
        });
      },
    })),
    { name: 'auth-store' }
  )
);