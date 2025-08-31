'use client';

import { useState } from 'react';
import { 
  Building2, 
  Plus, 
  Search, 
  Filter,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { useBusinesses, useSearchBusinesses, useDeactivateBusiness } from '@/hooks/useBusinesses';
import { CreateBusinessModal } from './CreateBusinessModal';
import type { Business } from '@/types';

export function BusinessManagement() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Use React Query for lightning-fast data fetching
  const { data: businesses = [], isLoading, error } = useBusinesses({ limit: 200 });
  const { data: searchResults = [] } = useSearchBusinesses(searchQuery);
  const deactivateMutation = useDeactivateBusiness();

  const handleDeactivate = async (business: Business) => {
    if (!window.confirm(`Deactivate ${business.business_name || business.name}?`)) return;

    try {
      await deactivateMutation.mutateAsync(business.id);
      alert('✅ Business deactivated successfully');
    } catch (error: unknown) {
      const err = error as { message: string };
      alert(`❌ Error: ${err.message}`);
    }
  };

  // Fast client-side filtering
  const displayBusinesses = searchQuery.trim() ? searchResults : businesses;
  const filteredBusinesses = displayBusinesses.filter(business => {
    if (statusFilter === 'active') return business.is_active;
    if (statusFilter === 'inactive') return !business.is_active;
    return true;
  });

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Error: {error.message}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Management</h1>
          <p className="text-gray-600">Manage EBM integration businesses</p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Business</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search businesses by name, TIN, or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white placeholder-gray-400"
            />
          </div>
          
          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
            >
              <option value="all">All Status</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Business List */}
      <div className="bg-white shadow-lg rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Businesses ({filteredBusinesses.length})
          </h2>
        </div>

        {isLoading ? (
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="p-6 animate-pulse">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gray-300 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-300 rounded mb-2"></div>
                    <div className="h-3 bg-gray-300 rounded w-2/3"></div>
                  </div>
                  <div className="w-20 h-8 bg-gray-300 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredBusinesses.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {filteredBusinesses.map((business) => (
              <BusinessRow 
                key={business.id} 
                business={business} 
                onDeactivate={() => handleDeactivate(business)}
              />
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No businesses found</h3>
            <p className="text-gray-500 mb-6">
              {searchQuery ? 'Try adjusting your search terms' : 'Get started by adding your first business'}
            </p>
            {!searchQuery && (
              <button 
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Your First Business
              </button>
            )}
          </div>
        )}
      </div>

      {/* Create Business Modal */}
      <CreateBusinessModal 
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}

interface BusinessRowProps {
  business: Business;
  onDeactivate: () => void;
}

function BusinessRow({ business, onDeactivate }: BusinessRowProps) {
  const [showActions, setShowActions] = useState(false);

  const handleEdit = () => {
    window.location.href = `/dashboard/businesses/${business.id}/edit`;
  };

  const handleView = () => {
    window.location.href = `/dashboard/businesses/${business.id}`;
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            business.is_active ? 'bg-green-100' : 'bg-gray-100'
          }`}>
            <Building2 className={`w-6 h-6 ${
              business.is_active ? 'text-green-600' : 'text-gray-400'
            }`} />
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {business.business_name || business.name}
            </h3>
            <p className="text-sm text-gray-600">
              TIN: {business.tin_number}
            </p>
            <p className="text-sm text-gray-500">
              {business.email} {business.phone_number && `• ${business.phone_number}`}
            </p>
            {business.location && (
              <p className="text-xs text-gray-500 mt-1">📍 {business.location}</p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              business.is_active
                ? 'bg-green-100 text-green-800 border border-green-200'
                : 'bg-red-100 text-red-800 border border-red-200'
            }`}
          >
            {business.is_active ? 'Active' : 'Inactive'}
          </span>

          <div className="text-right text-sm text-gray-500">
            <p>Created: {new Date(business.created_at).toLocaleDateString()}</p>
            {business.updated_at && (
              <p>Updated: {new Date(business.updated_at).toLocaleDateString()}</p>
            )}
          </div>

          {/* Actions */}
          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <MoreHorizontal className="w-5 h-5" />
            </button>

            {showActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                <button
                  onClick={handleView}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </button>
                <button
                  onClick={handleEdit}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Business
                </button>
                {business.is_active && (
                  <button
                    onClick={() => {
                      onDeactivate();
                      setShowActions(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Deactivate
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}