'use client';

import { useState } from 'react';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Webhook,
  RefreshCw
} from 'lucide-react';

export function WebhookActivity() {
  const [isLoading, setIsLoading] = useState(false);

  // Placeholder webhook data - in real implementation this would come from an API
  const webhookLogs = [
    {
      id: 1,
      timestamp: '2024-01-15 14:30:22',
      status: 'success',
      method: 'POST',
      endpoint: '/api/v1/webhooks/zoho',
      response_code: 200,
      processing_time: '1.2s',
      payload_size: '2.4KB'
    },
    {
      id: 2,
      timestamp: '2024-01-15 14:25:18',
      status: 'error',
      method: 'POST', 
      endpoint: '/api/v1/webhooks/zoho',
      response_code: 500,
      processing_time: '0.8s',
      payload_size: '1.9KB'
    },
    {
      id: 3,
      timestamp: '2024-01-15 14:20:45',
      status: 'success',
      method: 'POST',
      endpoint: '/api/v1/webhooks/zoho', 
      response_code: 200,
      processing_time: '2.1s',
      payload_size: '3.1KB'
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return CheckCircle;
      case 'error':
        return XCircle;
      case 'warning':
        return AlertTriangle;
      default:
        return Clock;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
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
        
        <div className="mt-4 lg:mt-0">
          <button
            onClick={() => setIsLoading(!isLoading)}
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
                  <dd className="text-2xl font-bold text-gray-900">1,247</dd>
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
                  <dd className="text-2xl font-bold text-gray-900">98.2%</dd>
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
                  <dd className="text-2xl font-bold text-gray-900">1.4s</dd>
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
                  <dd className="text-2xl font-bold text-gray-900">3</dd>
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
          
          <div className="flow-root">
            <ul className="-mb-8">
              {webhookLogs.map((log, logIdx) => {
                const StatusIcon = getStatusIcon(log.status);
                
                return (
                  <li key={log.id}>
                    <div className="relative pb-8">
                      {logIdx !== webhookLogs.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${getStatusColor(log.status)}`}>
                            <StatusIcon className="h-5 w-5" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              <span className="font-medium text-gray-900">{log.method}</span>{' '}
                              request to <span className="font-medium">{log.endpoint}</span>
                            </p>
                            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                log.response_code >= 200 && log.response_code < 300 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {log.response_code}
                              </span>
                              <span>Processing time: {log.processing_time}</span>
                              <span>Size: {log.payload_size}</span>
                            </div>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            <time>{log.timestamp}</time>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
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
                  <Webhook className="h-5 w-5 text-blue-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Zoho Books Webhook</p>
                    <p className="text-sm text-gray-500">/api/v1/webhooks/zoho</p>
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
                  <Webhook className="h-5 w-5 text-purple-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">EBM Integration</p>
                    <p className="text-sm text-gray-500">/api/v1/vsdc/process</p>
                  </div>
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Active
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}