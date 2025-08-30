import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import type { Business, BusinessCreate, BusinessUpdate, ApiError } from '@/types';
import { businessAPI } from '@/lib/api';

interface BusinessState {
  // State
  businesses: Business[];
  selectedBusiness: Business | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  error: ApiError | null;
  searchQuery: string;
  searchResults: Business[];
  
  // Pagination
  pagination: {
    skip: number;
    limit: number;
    total: number;
  };

  // Actions
  fetchBusinesses: (params?: { skip?: number; limit?: number; active_only?: boolean }) => Promise<void>;
  createBusiness: (data: BusinessCreate) => Promise<{ business: Business; admin_credentials: { username: string; password: string } } | null>;
  updateBusiness: (id: number, data: BusinessUpdate) => Promise<Business | null>;
  deactivateBusiness: (id: number) => Promise<boolean>;
  fetchBusiness: (id: number) => Promise<void>;
  searchBusinesses: (query: string) => Promise<void>;
  
  // UI actions
  setSelectedBusiness: (business: Business | null) => void;
  clearError: () => void;
  clearSearch: () => void;
  
  // Cache management
  updateBusinessInCache: (updatedBusiness: Business) => void;
  removeBusinessFromCache: (id: number) => void;
}

export const useBusinessStore = create<BusinessState>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      businesses: [],
      selectedBusiness: null,
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      error: null,
      searchQuery: '',
      searchResults: [],
      pagination: {
        skip: 0,
        limit: 20,
        total: 0,
      },

      // Actions
      fetchBusinesses: async (params = {}) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const businesses = await businessAPI.list(params);
          
          set((state) => {
            state.businesses = businesses;
            state.pagination.skip = params.skip || 0;
            state.pagination.limit = params.limit || 20;
            state.isLoading = false;
          });
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isLoading = false;
          });
        }
      },

      createBusiness: async (data) => {
        set((state) => {
          state.isCreating = true;
          state.error = null;
        });

        try {
          const result = await businessAPI.create(data);
          
          set((state) => {
            state.businesses.unshift(result.business);
            state.isCreating = false;
          });

          return result;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isCreating = false;
          });
          return null;
        }
      },

      updateBusiness: async (id, data) => {
        set((state) => {
          state.isUpdating = true;
          state.error = null;
        });

        try {
          const updatedBusiness = await businessAPI.update(id, data);
          
          set((state) => {
            const index = state.businesses.findIndex(b => b.id === id);
            if (index !== -1) {
              state.businesses[index] = updatedBusiness;
            }
            
            if (state.selectedBusiness?.id === id) {
              state.selectedBusiness = updatedBusiness;
            }
            
            state.isUpdating = false;
          });

          return updatedBusiness;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isUpdating = false;
          });
          return null;
        }
      },

      deactivateBusiness: async (id) => {
        set((state) => {
          state.error = null;
        });

        try {
          await businessAPI.deactivate(id);
          
          set((state) => {
            const index = state.businesses.findIndex(b => b.id === id);
            if (index !== -1) {
              state.businesses[index].is_active = false;
            }
            
            if (state.selectedBusiness?.id === id) {
              state.selectedBusiness.is_active = false;
            }
          });

          return true;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
          });
          return false;
        }
      },

      fetchBusiness: async (id) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const business = await businessAPI.get(id);
          
          set((state) => {
            state.selectedBusiness = business;
            state.isLoading = false;
            
            // Update in cache if exists
            const index = state.businesses.findIndex(b => b.id === id);
            if (index !== -1) {
              state.businesses[index] = business;
            }
          });
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isLoading = false;
          });
        }
      },

      searchBusinesses: async (query) => {
        if (!query.trim()) {
          get().clearSearch();
          return;
        }

        set((state) => {
          state.searchQuery = query;
          state.isLoading = true;
          state.error = null;
        });

        try {
          const results = await businessAPI.search(query);
          
          set((state) => {
            state.searchResults = results;
            state.isLoading = false;
          });
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isLoading = false;
          });
        }
      },

      // UI actions
      setSelectedBusiness: (business) => {
        set((state) => {
          state.selectedBusiness = business;
        });
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      clearSearch: () => {
        set((state) => {
          state.searchQuery = '';
          state.searchResults = [];
        });
      },

      // Cache management
      updateBusinessInCache: (updatedBusiness) => {
        set((state) => {
          const index = state.businesses.findIndex(b => b.id === updatedBusiness.id);
          if (index !== -1) {
            state.businesses[index] = updatedBusiness;
          }
          
          if (state.selectedBusiness?.id === updatedBusiness.id) {
            state.selectedBusiness = updatedBusiness;
          }
        });
      },

      removeBusinessFromCache: (id) => {
        set((state) => {
          state.businesses = state.businesses.filter(b => b.id !== id);
          
          if (state.selectedBusiness?.id === id) {
            state.selectedBusiness = null;
          }
        });
      },
    })),
    { name: 'business-store' }
  )
);