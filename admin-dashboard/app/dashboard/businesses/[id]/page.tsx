'use client';

import { useParams, useRouter } from 'next/navigation';

import { 
  ArrowLeft, 
  Building2, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar,
  Edit,
  Trash2,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useBusiness, useDeactivateBusiness } from '@/hooks/useBusinesses';

export default function BusinessDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const businessId = parseInt(params.id as string);
  
  const { data: business, isLoading, error } = useBusiness(businessId);
  const deactivateMutation = useDeactivateBusiness();

  const handleEdit = () => {
    router.push(`/dashboard/businesses/${businessId}/edit`);
  };

  const handleDeactivate = async () => {
    if (!business) return;
    
    if (!window.confirm(`Are you sure you want to deactivate ${business.business_name || business.name}? This action will affect all associated users.`)) {
      return;
    }

    try {
      await deactivateMutation.mutateAsync(businessId);
      alert('✅ Business deactivated successfully');
      router.refresh();
    } catch (error: unknown) {
      const err = error as { message: string };
      alert(`❌ Error: ${err.message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-gray-300 rounded animate-pulse"></div>
          <div className="h-8 bg-gray-300 rounded w-64 animate-pulse"></div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-300 rounded w-1/3"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 rounded"></div>
              <div className="h-4 bg-gray-300 rounded w-2/3"></div>
              <div className="h-4 bg-gray-300 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !business) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Businesses
        </button>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="text-red-800">
            <h3 className="text-lg font-semibold mb-2">Error Loading Business</h3>
            <p>{error?.message || 'Business not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Businesses
          </button>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleEdit}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Edit className="w-4 h-4 mr-2" />
            Edit Business
          </button>
          
          {business.is_active && (
            <button
              onClick={handleDeactivate}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              disabled={deactivateMutation.isPending}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {deactivateMutation.isPending ? 'Deactivating...' : 'Deactivate'}
            </button>
          )}
        </div>
      </div>

      {/* Business Details Card */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
              business.is_active ? 'bg-green-100' : 'bg-gray-100'
            }`}>
              <Building2 className={`w-8 h-8 ${
                business.is_active ? 'text-green-600' : 'text-gray-400'
              }`} />
            </div>
            
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">
                {business.business_name || business.name}
              </h1>
              <p className="text-gray-600">TIN: {business.tin_number}</p>
            </div>

            <div className="text-right">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                business.is_active
                  ? 'bg-green-100 text-green-800 border border-green-200'
                  : 'bg-red-100 text-red-800 border border-red-200'
              }`}>
                {business.is_active ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Active
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 mr-1" />
                    Inactive
                  </>
                )}
              </span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Contact Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Contact Information
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Mail className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="text-gray-900">{business.email}</p>
                  </div>
                </div>

                {business.phone_number && (
                  <div className="flex items-center space-x-3">
                    <Phone className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Phone</p>
                      <p className="text-gray-900">{business.phone_number}</p>
                    </div>
                  </div>
                )}

                {business.location && (
                  <div className="flex items-center space-x-3">
                    <MapPin className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="text-gray-900">{business.location}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* System Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                System Information
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Calendar className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Created</p>
                    <p className="text-gray-900">
                      {new Date(business.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </div>

                {business.updated_at && (
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Last Updated</p>
                      <p className="text-gray-900">
                        {new Date(business.updated_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 flex items-center justify-center">
                    <span className="text-gray-400 font-mono">#</span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Business ID</p>
                    <p className="text-gray-900 font-mono">{business.id}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Information */}
      {business.description && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Description</h3>
          <p className="text-gray-700">{business.description}</p>
        </div>
      )}
    </div>
  );
}