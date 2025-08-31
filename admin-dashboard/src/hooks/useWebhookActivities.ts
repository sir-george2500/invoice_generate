import { useQuery } from '@tanstack/react-query';
import { utilityAPI } from '@/lib/api';

// Types for webhook activities
export interface WebhookActivity {
  id: number;
  webhook_type: 'invoice' | 'credit_note';
  status: 'pending' | 'success' | 'failed' | 'timeout' | 'retry';
  business_tin?: string;
  business_name?: string;
  invoice_number?: string;
  vsdc_receipt_number?: string;
  error_code?: string;
  error_message?: string;
  error_type?: string;
  processing_time_ms?: number;
  retry_count: number;
  pdf_generated: boolean;
  pdf_filename?: string;
  created_at?: string;
  processed_at?: string;
}

export interface WebhookActivityFilters {
  business_tin?: string;
  status?: string;
  webhook_type?: string;
  invoice_number?: string;
  hours_back?: number;
  limit?: number;
  offset?: number;
}

export interface WebhookStats {
  total_webhooks: number;
  successful: number;
  failed: number;
  pending: number;
  by_type: {
    invoices: number;
    credit_notes: number;
  };
  avg_processing_time_ms: number;
  success_rate: number;
}

// Query Keys
export const webhookActivityKeys = {
  all: ['webhook-activities'] as const,
  lists: () => [...webhookActivityKeys.all, 'list'] as const,
  list: (filters: WebhookActivityFilters) => [...webhookActivityKeys.lists(), filters] as const,
  details: () => [...webhookActivityKeys.all, 'detail'] as const,
  detail: (id: number) => [...webhookActivityKeys.details(), id] as const,
  stats: (filters?: { business_tin?: string; days_back?: number }) => [...webhookActivityKeys.all, 'stats', filters] as const,
  failures: (hours_back?: number) => [...webhookActivityKeys.all, 'failures', hours_back] as const,
};

// Webhook Activities Query
export function useWebhookActivities(filters: WebhookActivityFilters = {}) {
  return useQuery({
    queryKey: webhookActivityKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      
      if (filters.business_tin) params.append('business_tin', filters.business_tin);
      if (filters.status) params.append('status', filters.status);
      if (filters.webhook_type) params.append('webhook_type', filters.webhook_type);
      if (filters.invoice_number) params.append('invoice_number', filters.invoice_number);
      if (filters.hours_back) params.append('hours_back', filters.hours_back.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/webhook-activities?${params}`);
      if (!response.ok) throw new Error('Failed to fetch webhook activities');
      return response.json();
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refresh every minute for live updates
  });
}

// Failed Webhooks Query
export function useFailedWebhooks(hours_back: number = 24) {
  return useQuery({
    queryKey: webhookActivityKeys.failures(hours_back),
    queryFn: async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/webhook-activities/failures?hours_back=${hours_back}`
      );
      if (!response.ok) throw new Error('Failed to fetch failed webhooks');
      return response.json();
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

// Webhook Stats Query
export function useWebhookStats(filters?: { business_tin?: string; days_back?: number }) {
  return useQuery({
    queryKey: webhookActivityKeys.stats(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.business_tin) params.append('business_tin', filters.business_tin);
      if (filters?.days_back) params.append('days_back', filters.days_back.toString());
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/webhook-activities/stats?${params}`
      );
      if (!response.ok) throw new Error('Failed to fetch webhook stats');
      return response.json();
    },
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
}

// Single Webhook Activity Query
export function useWebhookActivity(id: number) {
  return useQuery({
    queryKey: webhookActivityKeys.detail(id),
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/webhook-activities/${id}`);
      if (!response.ok) throw new Error('Failed to fetch webhook activity');
      return response.json();
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}