'use client';

import { useState } from 'react';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Webhook,
  RefreshCw,
  Building2,
  FileText,
  Receipt
} from 'lucide-react';
import { 
  useWebhookActivities, 
  useWebhookStats, 
  useFailedWebhooks,
  type WebhookActivity 
} from '@/hooks/useWebhookActivities';
import { format } from 'date-fns';

export function WebhookActivity() {
  const [hoursBack, setHoursBack] = useState(24);
  
  // Real data from our webhook activity system
  const { data: activitiesData, isLoading: loadingActivities, refetch: refetchActivities } = useWebhookActivities({
    hours_back: hoursBack,
    limit: 20
  });
  
  const { data: statsData, isLoading: loadingStats } = useWebhookStats({
    days_back: 7
  });
  
  const { data: failuresData } = useFailedWebhooks(24);
  
  const isLoading = loadingActivities || loadingStats;
  
  const activities: WebhookActivity[] = activitiesData?.activities || [];
  const stats = statsData?.statistics || {
    total_webhooks: 0,
    successful: 0,
    failed: 0,
    pending: 0,
    avg_processing_time_ms: 0,
    success_rate: 0
  };
  const recentFailures = failuresData?.failed_webhooks || [];
  
  const handleRefresh = () => {
    refetchActivities();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return CheckCircle;
      case 'failed':
        return XCircle;
      case 'retry':
        return RefreshCw;
      case 'timeout':
        return Clock;
      case 'pending':
        return AlertTriangle;
      default:
        return Clock;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'retry':
        return 'text-yellow-600 bg-yellow-100';
      case 'timeout':
        return 'text-orange-600 bg-orange-100';
      case 'pending':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getWebhookTypeIcon = (type: string) => {
    switch (type) {
      case 'invoice':
        return FileText;
      case 'credit_note':
        return Receipt;
      default:
        return Webhook;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Webhook Activity</h1>
          <p className="mt-1 text-sm text-gray-600">
            Monitor webhook requests and system integration activity
          </p>
        </div>
        
        <div className="mt-4 lg:mt-0 flex items-center space-x-3">
          <select
            value={hoursBack}
            onChange={(e) => setHoursBack(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={1}>Last Hour</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
          </select>
          
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Requests
                  </dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : stats.total_webhooks.toLocaleString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Success Rate
                  </dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : `${stats.success_rate.toFixed(1)}%`}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Avg Response Time
                  </dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : `${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Failed Today
                  </dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : recentFailures.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
            Recent Webhook Activity
          </h3>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-600">Loading webhook activities...</span>
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-8">
              <Webhook className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 font-medium">No webhook activity found</p>
              <p className="text-gray-500 text-sm">
                {hoursBack === 1 ? 'No webhooks in the last hour' :
                 hoursBack === 24 ? 'No webhooks in the last 24 hours' :
                 'No webhooks in the last week'}
              </p>
            </div>
          ) : (
            <div className="flow-root">
              <ul className="-mb-8">
                {activities.map((activity, activityIdx) => {
                  const StatusIcon = getStatusIcon(activity.status);
                  const TypeIcon = getWebhookTypeIcon(activity.webhook_type);
                  
                  return (
                    <li key={activity.id}>
                      <div className="relative pb-8">
                        {activityIdx !== activities.length - 1 ? (
                          <span
                            className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                            aria-hidden="true"
                          />
                        ) : null}
                        <div className="relative flex space-x-3">
                          <div>
                            <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${getStatusColor(activity.status)}`}>
                              <StatusIcon className="h-4 w-4" />
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                            <div>
                              <div className="flex items-center space-x-2">
                                <TypeIcon className="h-4 w-4 text-gray-400" />
                                <p className="text-sm text-gray-500">
                                  <span className="font-medium text-gray-900 capitalize">{activity.webhook_type}</span>{' '}
                                  webhook {activity.status === 'success' ? 'processed successfully' : 'failed'}
                                </p>
                              </div>
                              
                              <div className="mt-1 space-y-1">
                                {activity.business_tin && (
                                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                                    <Building2 className="h-3 w-3 text-gray-400" />
                                    <span>TIN: {activity.business_tin}</span>
                                    {activity.business_name && (
                                      <span>({activity.business_name})</span>
                                    )}
                                  </div>
                                )}
                                
                                {activity.invoice_number && (
                                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                                    <span className="font-medium">Invoice: {activity.invoice_number}</span>
                                  </div>
                                )}
                                
                                <div className="flex items-center space-x-4 text-sm text-gray-500">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                                    {activity.status.toUpperCase()}
                                  </span>
                                  
                                  {activity.processing_time_ms && (
                                    <span>Processing: {(activity.processing_time_ms / 1000).toFixed(2)}s</span>
                                  )}
                                  
                                  {activity.vsdc_receipt_number && (
                                    <span>Receipt: {activity.vsdc_receipt_number}</span>
                                  )}
                                  
                                  {activity.pdf_generated && (
                                    <span className="text-green-600">PDF ✓</span>
                                  )}
                                  
                                  {activity.retry_count > 0 && (
                                    <span className="text-yellow-600">Retries: {activity.retry_count}</span>
                                  )}
                                </div>
                                
                                {activity.error_message && (
                                  <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                                    <strong>Error:</strong> {activity.error_message}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="text-right text-sm whitespace-nowrap text-gray-500">
                              <time>
                                {activity.created_at ? format(new Date(activity.created_at), 'MMM dd, HH:mm:ss') : 'Unknown'}
                              </time>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* System Integration Status */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
            Integration Endpoints
          </h3>
          
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-blue-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Zoho Invoice Webhook</p>
                    <p className="text-sm text-gray-500 font-mono">/api/v1/webhooks/zoho/invoice</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Invoices: {stats.by_type?.invoices || 0} processed
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Active
                </span>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Receipt className="h-5 w-5 text-purple-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Credit Note Webhook</p>
                    <p className="text-sm text-gray-500 font-mono">/api/v1/webhooks/zoho/credit-note</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Credit Notes: {stats.by_type?.credit_notes || 0} processed
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Active
                </span>
              </div>
            </div>
          </div>
          
          {recentFailures.length > 0 && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-red-800 mb-2">Recent Failures Requiring Attention</h4>
              <div className="space-y-2">
                {recentFailures.slice(0, 3).map((failure: { 
                  id: number; 
                  business_tin: string; 
                  business_name: string; 
                  invoice_number?: string; 
                  error_code?: string; 
                }) => (
                  <div key={failure.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span className="font-medium">{failure.business_tin}</span>
                      <span>({failure.business_name})</span>
                      {failure.invoice_number && <span>- {failure.invoice_number}</span>}
                    </div>
                    <span className="text-red-600 text-xs">
                      {failure.error_code && `Error ${failure.error_code}`}
                    </span>
                  </div>
                ))}
                {recentFailures.length > 3 && (
                  <p className="text-xs text-red-600 mt-2">
                    +{recentFailures.length - 3} more failures in the last 24 hours
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}