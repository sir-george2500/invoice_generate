'use client';

import { useState, useEffect } from 'react';
import { 
  Settings, 
  Server, 
  Database, 
  Shield, 
  Bell,
  Globe,
  Monitor,
  HardDrive,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Activity,
  Cloud,
  FileText,
  QrCode,
  Zap
} from 'lucide-react';
import { utilityAPI } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

interface SystemHealthData {
  status: string;
  timestamp: string;
  services?: {
    vsdc_service?: string;
    pdf_service?: string;
    database?: string;
  };
  qr_generator_enabled?: boolean;
  cloudinary_configured?: boolean;
  [key: string]: unknown;
}

export function SettingsManagement() {
  const { user } = useAuth();
  const [healthData, setHealthData] = useState<SystemHealthData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('system');

  useEffect(() => {
    fetchSystemHealth();
  }, []);

  const fetchSystemHealth = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const health = await utilityAPI.health();
      setHealthData(health);
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to fetch system health');
    } finally {
      setIsLoading(false);
    }
  };

  const testPDFGeneration = async () => {
    setIsLoading(true);
    try {
      await utilityAPI.testPDFGeneration();
      await fetchSystemHealth(); // Refresh after test
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'PDF test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const testQRValidation = async () => {
    setIsLoading(true);
    try {
      await utilityAPI.testQRValidation();
      await fetchSystemHealth(); // Refresh after test
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'QR test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const testPayloadTransform = async () => {
    setIsLoading(true);
    try {
      await utilityAPI.testPayloadTransform();
      await fetchSystemHealth(); // Refresh after test
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Payload transform test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'system', name: 'System Health', icon: Monitor },
    { id: 'services', name: 'Services', icon: Server },
    { id: 'integrations', name: 'Integrations', icon: Globe },
    { id: 'maintenance', name: 'Maintenance', icon: Settings },
  ];

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'initialized':
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'offline':
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string): React.ComponentType<{ className?: string }> => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'initialized':
      case 'active':
        return CheckCircle;
      case 'warning':
      case 'degraded':
        return AlertTriangle;
      case 'error':
      case 'offline':
      case 'failed':
        return XCircle;
      default:
        return Info;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
          <p className="mt-1 text-sm text-gray-600">
            Monitor and configure your ALSM EBM system
          </p>
        </div>
        
        <div className="mt-4 lg:mt-0">
          <button
            onClick={fetchSystemHealth}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Status
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5 inline mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        {activeTab === 'system' && (
          <SystemHealthTab 
            healthData={healthData} 
            isLoading={isLoading}
            getStatusColor={getStatusColor}
            getStatusIcon={getStatusIcon}
          />
        )}
        
        {activeTab === 'services' && (
          <ServicesTab 
            healthData={healthData}
            getStatusColor={getStatusColor}
            getStatusIcon={getStatusIcon}
            testPDFGeneration={testPDFGeneration}
            testQRValidation={testQRValidation}
            testPayloadTransform={testPayloadTransform}
            isLoading={isLoading}
          />
        )}
        
        {activeTab === 'integrations' && (
          <IntegrationsTab 
            healthData={healthData}
            getStatusColor={getStatusColor}
            getStatusIcon={getStatusIcon}
          />
        )}
        
        {activeTab === 'maintenance' && (
          <MaintenanceTab user={user} />
        )}
      </div>
    </div>
  );
}

interface SystemHealthTabProps {
  healthData: SystemHealthData | null;
  isLoading: boolean;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ComponentType<{ className?: string }>;
}

function SystemHealthTab({ healthData, isLoading, getStatusColor, getStatusIcon }: SystemHealthTabProps) {
  if (isLoading && !healthData) {
    return (
      <div className="p-6 text-center">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Loading system health...</p>
      </div>
    );
  }

  const StatusIcon = healthData ? getStatusIcon(healthData.status) : Info;
  
  return (
    <div className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Overall Status */}
        <div className="col-span-1 lg:col-span-3">
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-full ${healthData ? getStatusColor(healthData.status) : 'text-gray-600 bg-gray-100'}`}>
                  <StatusIcon className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
                  <p className="text-2xl font-bold capitalize">
                    {healthData?.status || 'Unknown'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Last checked</p>
                <p className="text-sm font-medium">
                  {healthData?.timestamp ? new Date(healthData.timestamp).toLocaleString() : 'Never'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Database Status */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <Database className="h-8 w-8 text-blue-600" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Database</h4>
              <p className={`text-sm px-2 py-1 rounded-full ${getStatusColor(healthData?.services?.database || 'unknown')}`}>
                {healthData?.services?.database || 'Unknown'}
              </p>
            </div>
          </div>
        </div>

        {/* API Status */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <Server className="h-8 w-8 text-green-600" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">API Server</h4>
              <p className={`text-sm px-2 py-1 rounded-full ${getStatusColor(healthData?.status || 'unknown')}`}>
                {healthData?.status || 'Unknown'}
              </p>
            </div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <HardDrive className="h-8 w-8 text-purple-600" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Memory</h4>
              <p className="text-sm text-gray-600">
                {String(healthData?.memory_usage) || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Uptime */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <Activity className="h-8 w-8 text-orange-600" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Uptime</h4>
              <p className="text-sm text-gray-600">
                {String(healthData?.uptime) || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ServicesTabProps {
  healthData: SystemHealthData | null;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ComponentType<{ className?: string }>;
  testPDFGeneration: () => Promise<void>;
  testQRValidation: () => Promise<void>;
  testPayloadTransform: () => Promise<void>;
  isLoading: boolean;
}

function ServicesTab({ healthData, getStatusColor, getStatusIcon, testPDFGeneration, testQRValidation, testPayloadTransform, isLoading }: ServicesTabProps) {
  const services = [
    {
      name: 'VSDC Service',
      description: 'Electronic Billing Machine integration service',
      status: healthData?.services?.vsdc_service || 'unknown',
      icon: Zap,
      testAction: testPayloadTransform,
      testLabel: 'Test VSDC Connection'
    },
    {
      name: 'PDF Service',
      description: 'Invoice and receipt PDF generation',
      status: healthData?.services?.pdf_service || 'unknown',
      icon: FileText,
      testAction: testPDFGeneration,
      testLabel: 'Test PDF Generation'
    },
    {
      name: 'QR Generator',
      description: 'QR code generation for invoices',
      status: healthData?.qr_generator_enabled ? 'enabled' : 'disabled',
      icon: QrCode,
      testAction: testQRValidation,
      testLabel: 'Test QR Generation'
    },
    {
      name: 'Cloudinary',
      description: 'Image hosting and QR code storage',
      status: healthData?.cloudinary_configured ? 'configured' : 'not configured',
      icon: Cloud,
      testAction: undefined,
      testLabel: ''
    },
  ];

  return (
    <div className="p-6">
      <div className="space-y-6">
        {services.map((service) => {
          const Icon = service.icon;
          const StatusIcon = getStatusIcon(service.status);
          
          return (
            <div key={service.name} className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-white rounded-lg shadow-sm">
                    <Icon className="h-6 w-6 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{service.name}</h3>
                    <p className="text-sm text-gray-600">{service.description}</p>
                    <div className="flex items-center space-x-2 mt-2">
                      <StatusIcon className="h-4 w-4" />
                      <span className={`text-sm font-medium px-2 py-1 rounded-full ${getStatusColor(service.status)}`}>
                        {service.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
                
                {service.testAction && (
                  <button
                    onClick={service.testAction}
                    disabled={isLoading}
                    className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:bg-gray-100 disabled:text-gray-400 transition-colors"
                  >
                    {service.testLabel}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface IntegrationsTabProps {
  healthData: SystemHealthData | null;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ComponentType<{ className?: string }>;
}

function IntegrationsTab({ healthData, getStatusColor, getStatusIcon }: IntegrationsTabProps) {
  const integrations = [
    {
      name: 'Rwanda Revenue Authority (RRA)',
      description: 'Electronic Billing Machine system integration',
      status: healthData?.services?.vsdc_service === 'initialized' ? 'connected' : 'disconnected',
      icon: Shield,
      lastSync: healthData?.last_rra_sync || 'Never'
    },
    {
      name: 'Cloudinary CDN',
      description: 'Image and QR code storage service',
      status: healthData?.cloudinary_configured ? 'configured' : 'not configured',
      icon: Cloud,
      lastSync: healthData?.last_cloudinary_sync || 'N/A'
    },
    {
      name: 'Email Service',
      description: 'Email notifications and reports',
      status: healthData?.email_service_enabled ? 'enabled' : 'disabled',
      icon: Bell,
      lastSync: healthData?.last_email_sent || 'Never'
    },
  ];

  return (
    <div className="p-6">
      <div className="space-y-6">
        {integrations.map((integration) => {
          const Icon = integration.icon;
          const StatusIcon = getStatusIcon(integration.status);
          
          return (
            <div key={integration.name} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-gray-100 rounded-lg">
                    <Icon className="h-6 w-6 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{integration.name}</h3>
                    <p className="text-sm text-gray-600">{integration.description}</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <div className="flex items-center space-x-2">
                        <StatusIcon className="h-4 w-4" />
                        <span className={`text-sm font-medium px-2 py-1 rounded-full ${getStatusColor(integration.status)}`}>
                          {integration.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Last sync: {String(integration.lastSync)}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <button className="px-3 py-1 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors">
                    Configure
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface MaintenanceTabProps {
  user: {
    username?: string;
    role?: string;
  } | null;
}

function MaintenanceTab({ user }: MaintenanceTabProps) {
  const [pdfList, setPdfList] = useState<Array<{ filename: string; size: string; created: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchPDFList();
  }, []);

  const fetchPDFList = async () => {
    setIsLoading(true);
    try {
      const result = await utilityAPI.listPDFs();
      setPdfList(result.pdfs || []);
    } catch (err) {
      console.error('Failed to fetch PDF list:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="space-y-8">
        {/* System Information */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Information</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">Current User</p>
                <p className="text-sm text-gray-600">{user?.username} ({user?.role})</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">System Version</p>
                <p className="text-sm text-gray-600">ALSM EBM v2.0.0</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">API Base URL</p>
                <p className="text-sm text-gray-600">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Environment</p>
                <p className="text-sm text-gray-600">{process.env.NODE_ENV || 'development'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Generated Files */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Generated Files</h3>
            <button
              onClick={fetchPDFList}
              disabled={isLoading}
              className="px-3 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded hover:bg-blue-50 disabled:bg-gray-100 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 inline mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="overflow-hidden">
              {isLoading ? (
                <div className="p-6 text-center">
                  <RefreshCw className="h-6 w-6 animate-spin text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Loading files...</p>
                </div>
              ) : pdfList.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Filename
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pdfList.map((file, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {file.filename}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {file.size}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {file.created}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-6 text-center">
                  <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">No files found</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Maintenance Actions */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Maintenance Actions</h3>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
              <span className="text-yellow-800 font-medium">Admin Only</span>
            </div>
            <p className="text-yellow-700 text-sm mt-1">
              These actions are only available to system administrators and should be used with caution.
            </p>
            
            {user?.role === 'admin' && (
              <div className="mt-4 space-x-3">
                <button className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 transition-colors">
                  Clear Cache
                </button>
                <button className="px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 transition-colors">
                  Restart Services
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}