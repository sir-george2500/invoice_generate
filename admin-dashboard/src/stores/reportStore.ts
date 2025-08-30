import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import type { DailyReport, ApiError } from '@/types';
import { reportsAPI } from '@/lib/api';

interface ReportState {
  // State
  reports: DailyReport[];
  selectedReport: DailyReport | null;
  isLoading: boolean;
  isGenerating: boolean;
  error: ApiError | null;
  
  // Filters
  filters: {
    business_tin?: string;
    start_date?: string;
    end_date?: string;
    report_type?: 'X' | 'Z';
  };

  // Actions
  generateXReport: (businessTin: string) => Promise<DailyReport | null>;
  generateZReport: (businessTin: string) => Promise<DailyReport | null>;
  fetchReportHistory: (tinNumber: string, filters?: Record<string, unknown>) => Promise<void>;
  validateBusinessAccess: (tinNumber: string) => Promise<boolean>;
  
  // UI actions
  setSelectedReport: (report: DailyReport | null) => void;
  setFilters: (filters: Partial<ReportState['filters']>) => void;
  clearError: () => void;
  clearReports: () => void;
}

export const useReportStore = create<ReportState>()(
  devtools(
    immer((set) => ({
      // Initial state
      reports: [],
      selectedReport: null,
      isLoading: false,
      isGenerating: false,
      error: null,
      filters: {},

      // Actions
      generateXReport: async (businessTin) => {
        set((state) => {
          state.isGenerating = true;
          state.error = null;
        });

        try {
          const report = await reportsAPI.generateXReport(businessTin);
          
          set((state) => {
            // Add to reports list if not exists
            const existingIndex = state.reports.findIndex(r => r.id === report.id);
            if (existingIndex === -1) {
              state.reports.unshift(report);
            } else {
              state.reports[existingIndex] = report;
            }
            
            state.selectedReport = report;
            state.isGenerating = false;
          });

          return report;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isGenerating = false;
          });
          return null;
        }
      },

      generateZReport: async (businessTin) => {
        set((state) => {
          state.isGenerating = true;
          state.error = null;
        });

        try {
          const report = await reportsAPI.generateZReport(businessTin);
          
          set((state) => {
            // Add to reports list if not exists
            const existingIndex = state.reports.findIndex(r => r.id === report.id);
            if (existingIndex === -1) {
              state.reports.unshift(report);
            } else {
              state.reports[existingIndex] = report;
            }
            
            state.selectedReport = report;
            state.isGenerating = false;
          });

          return report;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
            state.isGenerating = false;
          });
          return null;
        }
      },

      fetchReportHistory: async (tinNumber, filters = {}) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
          state.filters.business_tin = tinNumber;
        });

        try {
          const reports = await reportsAPI.getHistory(tinNumber, filters);
          
          set((state) => {
            state.reports = reports;
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

      validateBusinessAccess: async (tinNumber) => {
        try {
          await reportsAPI.validateAccess(tinNumber);
          return true;
        } catch (error: unknown) {
          const apiError = error as ApiError;
          set((state) => {
            state.error = apiError;
          });
          return false;
        }
      },

      // UI actions
      setSelectedReport: (report) => {
        set((state) => {
          state.selectedReport = report;
        });
      },

      setFilters: (newFilters) => {
        set((state) => {
          state.filters = { ...state.filters, ...newFilters };
        });
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      clearReports: () => {
        set((state) => {
          state.reports = [];
          state.selectedReport = null;
          state.filters = {};
        });
      },
    })),
    { name: 'report-store' }
  )
);