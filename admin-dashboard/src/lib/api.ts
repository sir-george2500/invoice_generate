import axios, { AxiosResponse } from 'axios';
import type { 
  User, 
  Business, 
  BusinessCreate, 
  BusinessUpdate,
  Transaction,
  DailyReport,
  LoginCredentials,
  AuthResponse,
  ApiError 
} from '@/types';

// Constants
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 10000;

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('admin_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle common errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    const apiError: ApiError = {
      message: 'An error occurred',
      status: error.response?.status,
    };

    if (error.response?.status === 401) {
      // Handle unauthorized - clear auth and redirect
      if (typeof window !== 'undefined') {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        window.location.href = '/';
      }
      apiError.message = 'Unauthorized access';
    } else if (error.response?.status === 403) {
      apiError.message = 'Access forbidden';
    } else if (error.response?.status === 404) {
      apiError.message = 'Resource not found';
    } else if (error.response?.status >= 500) {
      apiError.message = 'Server error occurred';
    } else if (error.response?.data?.detail) {
      apiError.message = error.response.data.detail;
    }

    return Promise.reject(apiError);
  }
);

// Auth API methods
export const authAPI = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
    return response.data;
  },

  async verify(): Promise<{ valid: boolean; user: User }> {
    const response = await apiClient.get('/api/v1/auth/verify');
    return response.data;
  },

  async me(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },
};

// Business API methods
export const businessAPI = {
  async list(params?: { 
    skip?: number; 
    limit?: number; 
    active_only?: boolean; 
  }): Promise<Business[]> {
    const { skip = 0, limit = 100, active_only = true } = params || {};
    const response = await apiClient.get<Business[]>(
      `/api/v1/businesses?skip=${skip}&limit=${limit}&active_only=${active_only}`
    );
    return response.data;
  },

  async create(data: BusinessCreate): Promise<{ business: Business; admin_credentials: { username: string; password: string } }> {
    const response = await apiClient.post('/api/v1/businesses', data);
    return response.data;
  },

  async get(id: number): Promise<Business> {
    const response = await apiClient.get<Business>(`/api/v1/businesses/${id}`);
    return response.data;
  },

  async update(id: number, data: BusinessUpdate): Promise<Business> {
    const response = await apiClient.put<Business>(`/api/v1/businesses/${id}`, data);
    return response.data;
  },

  async deactivate(id: number): Promise<{ message: string }> {
    const response = await apiClient.put(`/api/v1/businesses/${id}/deactivate`);
    return response.data;
  },

  async search(query: string, params?: { skip?: number; limit?: number }): Promise<Business[]> {
    const { skip = 0, limit = 100 } = params || {};
    const response = await apiClient.get<Business[]>(
      `/api/v1/businesses/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`
    );
    return response.data;
  },
};

// Reports API methods
export const reportsAPI = {
  async generateXReport(businessTin: string): Promise<DailyReport> {
    const response = await apiClient.post<DailyReport>('/api/v1/reports/x-report', {
      business_tin: businessTin,
    });
    return response.data;
  },

  async generateZReport(businessTin: string): Promise<DailyReport> {
    const response = await apiClient.post<DailyReport>('/api/v1/reports/z-report', {
      business_tin: businessTin,
    });
    return response.data;
  },

  async getHistory(
    tinNumber: string, 
    params?: { 
      start_date?: string; 
      end_date?: string; 
      report_type?: 'X' | 'Z'; 
    }
  ): Promise<DailyReport[]> {
    const response = await apiClient.get<DailyReport[]>(
      `/api/v1/reports/history/${tinNumber}`,
      { params }
    );
    return response.data;
  },

  async validateAccess(tinNumber: string): Promise<{ message: string }> {
    const response = await apiClient.get(`/api/v1/reports/validate-access/${tinNumber}`);
    return response.data;
  },
};

// Transactions API methods
export const transactionsAPI = {
  async getByTin(tinNumber: string): Promise<Transaction[]> {
    const response = await apiClient.get<Transaction[]>(`/api/v1/transactions/${tinNumber}`);
    return response.data;
  },

  async create(data: Partial<Transaction>): Promise<Transaction> {
    const response = await apiClient.post<Transaction>('/api/v1/transactions/', data);
    return response.data;
  },

  async void(transactionId: number): Promise<{ message: string }> {
    const response = await apiClient.put(`/api/v1/transactions/void/${transactionId}`);
    return response.data;
  },
};

// Utility API methods
export const utilityAPI = {
  async health(): Promise<{ status: string; timestamp: string; [key: string]: unknown }> {
    const response = await apiClient.get('/health');
    return response.data;
  },

  async listPDFs(): Promise<{ message: string; pdfs: Array<{ filename: string; size: string; created: string }> }> {
    const response = await apiClient.get('/api/v1/pdfs/list');
    return response.data;
  },

  async testPayloadTransform(): Promise<{ message: string; [key: string]: unknown }> {
    const response = await apiClient.post('/api/v1/test/transform-payload');
    return response.data;
  },

  async testPDFGeneration(): Promise<{ message: string; [key: string]: unknown }> {
    const response = await apiClient.post('/api/v1/test/generate-pdf');
    return response.data;
  },

  async testQRValidation(): Promise<{ message: string; [key: string]: unknown }> {
    const response = await apiClient.post('/api/v1/test/validate-qr');
    return response.data;
  },
};

export default apiClient;