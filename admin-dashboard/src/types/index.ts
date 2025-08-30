// User types
export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'admin' | 'business_admin' | 'user';
  business_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Business types
export interface Business {
  id: number;
  name: string;
  business_name?: string; // Alternative name field
  tin_number: string;
  email: string;
  phone?: string;
  phone_number?: string; // Alternative phone field
  address: string;
  location?: string; // Alternative address field
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessCreate {
  name: string;
  tin_number: string;
  email: string;
  phone?: string;
  address: string;
}

export interface BusinessUpdate {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
}

// Transaction types
export interface Transaction {
  id: number;
  business_id: number;
  invoice_number: string;
  transaction_type: 'sale' | 'refund' | 'void';
  total_amount: number;
  tax_amount: number;
  net_amount: number;
  payment_method: string;
  currency: string;
  customer_name?: string;
  customer_tin?: string;
  receipt_number?: string;
  is_voided: boolean;
  created_at: string;
  updated_at: string;
}

// Report types
export interface DailyReport {
  id: number;
  business_id: number;
  report_date: string;
  report_type: 'X' | 'Z';
  total_transactions: number;
  total_sales_amount: number;
  total_tax_amount: number;
  total_net_amount: number;
  cash_amount: number;
  card_amount: number;
  mobile_amount: number;
  other_amount: number;
  voided_transactions: number;
  refunded_transactions: number;
  generated_by: number;
  created_at: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

// Auth types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Error types
export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}