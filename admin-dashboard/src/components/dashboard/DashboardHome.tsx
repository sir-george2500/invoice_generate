'use client';

import { 
  Building2, 
  FileText, 
  Activity,
  TrendingUp,
  AlertTriangle,
  Receipt
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useBusinesses, useSystemHealth } from '@/hooks/useBusinesses';
import Link from 'next/link';

export function DashboardHome() {
  const { user } = useAuth();
  const { data: businesses = [], isLoading: businessLoading, error: businessError } = useBusinesses({ limit: 100 });
  const { data: healthData, isLoading: healthLoading, error: healthError } = useSystemHealth();

  const activeBusinesses = businesses.filter(b => b.is_active).length;
  const stats = [
    {
      name: 'Total Businesses',
      value: businesses.length.toString(),
      subtext: `${activeBusinesses} active`,
      icon: Building2,
      color: 'blue',
      href: '/dashboard/businesses'
    },
    {
      name: 'System Health', 
      value: healthData?.status === 'healthy' ? '100%' : healthLoading ? '...' : 'Error',
      subtext: healthData?.status || 'Checking...',
      icon: Activity,
      color: healthData?.status === 'healthy' ? 'green' : 'yellow',
      href: '/dashboard/settings'
    },
    {
      name: 'EBM Service',
      value: (healthData as any)?.services?.vsdc_service === 'initialized' ? 'Online' : healthLoading ? '...' : 'Offline',
      subtext: `PDF: ${(healthData as any)?.services?.pdf_service === 'initialized' ? 'Ready' : 'Error'}`,
      icon: FileText,
      color: (healthData as any)?.services?.vsdc_service === 'initialized' ? 'green' : 'red',
      href: '/dashboard/settings'
    },
    {
      name: 'QR Generator',
      value: healthData?.qr_generator_enabled ? 'Enabled' : healthLoading ? '...' : 'Disabled',
      subtext: healthData?.cloudinary_configured ? 'Cloudinary OK' : 'Config Missing',
      icon: TrendingUp,
      color: healthData?.qr_generator_enabled ? 'green' : 'orange',
      href: '/dashboard/settings'
    },
  ];

  if (businessError || healthError) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center space-x-2 text-red-700">
          <AlertTriangle className="h-5 w-5" />
          <span className="font-medium">Error loading dashboard</span>
        </div>
        <p className="text-red-600 text-sm mt-1">
          {businessError?.message || healthError?.message || 'Unknown error'}
        </p>
      </div>
    );
  }

  const recentBusinesses = businesses.slice(0, 6);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.username}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here&apos;s what&apos;s happening with your ALSM EBM system today.
        </p>
      </div>

      {/* Lightning-Fast Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: 'bg-blue-100 text-blue-600',
            green: 'bg-green-100 text-green-600', 
            red: 'bg-red-100 text-red-600',
            yellow: 'bg-yellow-100 text-yellow-600',
            orange: 'bg-orange-100 text-orange-600',
          };
          
          return (
            <Link
              key={stat.name}
              href={stat.href}
              className="bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200 hover:shadow-xl transition-all duration-200 hover:scale-105 cursor-pointer"
            >
              <div className="p-6">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 p-3 rounded-lg ${colorClasses[stat.color as keyof typeof colorClasses] || colorClasses.blue}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="ml-4 flex-1">
                    <dt className="text-sm font-medium text-gray-600 truncate">
                      {stat.name}
                    </dt>
                    <dd className="mt-1">
                      <div className="text-2xl font-bold text-gray-900">
                        {stat.value}
                      </div>
                      {stat.subtext && (
                        <div className="text-sm text-gray-500 mt-1">
                          {stat.subtext}
                        </div>
                      )}
                    </dd>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Quick Actions
          </h3>
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <QuickActionCard
              title="Add New Business"
              description="Register a new business for EBM integration"
              icon={Building2}
              href="/dashboard/businesses?action=create"
              color="green"
            />
            <QuickActionCard
              title="Generate X Report"
              description="Generate interim daily sales report"
              icon={FileText}
              href="/dashboard/reports"
              color="blue"
            />
            <QuickActionCard
              title="Generate Z Report"
              description="Generate end-of-day final report"
              icon={Receipt}
              href="/dashboard/reports"
              color="red"
            />
            <QuickActionCard
              title="System Settings"
              description="Monitor system health and configure settings"
              icon={Activity}
              href="/dashboard/settings"
              color="yellow"
            />
          </div>
        </div>
      </div>

      {/* Recent Businesses */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Businesses
            </h3>
            <a
              href="/dashboard/businesses"
              className="text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              View all →
            </a>
          </div>
          
          <div className="mt-6">
            {businessLoading || !businesses ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                      <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
                      <div className="flex-1">
                        <div className="h-4 bg-gray-300 rounded mb-2"></div>
                        <div className="h-3 bg-gray-300 rounded w-3/4"></div>
                      </div>
                      <div className="w-20 h-6 bg-gray-300 rounded"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentBusinesses.length > 0 ? (
              <div className="space-y-4">
                {recentBusinesses.map((business) => (
                  <div
                    key={business.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <Building2 className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">
                          {business.business_name || business.name}
                        </p>
                        <p className="text-sm text-gray-600">
                          TIN: {business.tin_number}
                        </p>
                        <p className="text-xs text-gray-500">
                          {business.email} {business.phone_number && `• ${business.phone_number}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                          business.is_active
                            ? 'bg-green-100 text-green-800 border border-green-200'
                            : 'bg-red-100 text-red-800 border border-red-200'
                        }`}
                      >
                        {business.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(business.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 font-medium">No businesses registered yet</p>
                <p className="text-gray-500 text-sm">Get started by adding your first business</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  color?: 'blue' | 'red' | 'green' | 'yellow';
}

function QuickActionCard({ title, description, icon: Icon, href, color = 'blue' }: QuickActionCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 group-hover:bg-blue-100',
    red: 'bg-red-50 text-red-700 group-hover:bg-red-100',
    green: 'bg-green-50 text-green-700 group-hover:bg-green-100',
    yellow: 'bg-yellow-50 text-yellow-700 group-hover:bg-yellow-100',
  };

  return (
    <a
      href={href}
      className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 hover:bg-gray-50 border border-gray-200 rounded-lg transition-colors"
    >
      <div>
        <span className={`rounded-lg inline-flex p-3 ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </span>
      </div>
      <div className="mt-4">
        <h3 className="text-lg font-medium text-gray-900">
          <span className="absolute inset-0" aria-hidden="true" />
          {title}
        </h3>
        <p className="mt-2 text-sm text-gray-500">{description}</p>
      </div>
    </a>
  );
}