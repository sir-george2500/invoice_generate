'use client';

import { useState, useEffect } from 'react';
import { 
  FileText, 
  RefreshCw, 
  Filter, 
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  Building2,
  TrendingUp,
  DollarSign,
  Receipt
} from 'lucide-react';
import { useReportStore } from '@/stores/reportStore';
import { useBusinesses } from '@/hooks/useBusinesses';
import { format } from 'date-fns';
import { transactionsAPI } from '@/lib/api';

// Helper function to check if business has transactions for today
const hasTransactionsForToday = async (tinNumber: string): Promise<boolean> => {
  if (!tinNumber || tinNumber.trim() === '') {
    console.warn('Invalid TIN number provided for transaction check');
    return false;
  }

  try {
    const transactions = await transactionsAPI.getByTin(tinNumber);
    
    // Handle case where API returns null/undefined
    if (!Array.isArray(transactions)) {
      console.warn('No transaction data returned for TIN:', tinNumber);
      return false;
    }

    // Check if there are any transactions for today that are not voided
    const today = new Date().toDateString();
    const todayTransactions = transactions.filter(transaction => {
      try {
        if (!transaction || !transaction.created_at) {
          return false;
        }
        const transactionDate = new Date(transaction.created_at).toDateString();
        return transactionDate === today && !transaction.is_voided;
      } catch {
        console.warn('Invalid transaction date:', transaction.created_at);
        return false;
      }
    });
    
    return todayTransactions.length > 0;
  } catch (error) {
    // More detailed error logging
    if (error && typeof error === 'object') {
      const apiError = error as { message?: string; status?: number; detail?: string };
      console.warn('Transaction check failed for TIN:', tinNumber, {
        message: apiError.message || 'Unknown error',
        status: apiError.status || 'No status',
        detail: apiError.detail || 'No details'
      });
    } else {
      console.warn('Transaction check failed for TIN:', tinNumber, 'Error:', String(error));
    }
    return false; // If we can't check, assume no transactions to be safe
  }
};

export function ReportsManagement() {
  const {
    reports,
    selectedReport,
    isLoading,
    isGenerating,
    error,
    filters,
    generateXReport,
    generateZReport,
    fetchReportHistory,
    validateBusinessAccess,
    setSelectedReport,
    setFilters,
    clearError,
  } = useReportStore();

  const { data: businesses = [] } = useBusinesses({ limit: 100 });

  const [selectedBusiness, setSelectedBusiness] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [hasTransactions, setHasTransactions] = useState<boolean>(false);
  const [isCheckingTransactions, setIsCheckingTransactions] = useState<boolean>(false);
  const [dateRange, setDateRange] = useState({
    start: '',
    end: '',
  });

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleBusinessSelect = (tinNumber: string) => {
    setSelectedBusiness(tinNumber);
    setHasTransactions(false);
    setIsCheckingTransactions(false);
    
    if (tinNumber) {
      fetchReportHistory(tinNumber, filters);
      // Check transactions in the background without blocking UI
      checkTransactionsForBusiness(tinNumber);
    }
  };

  const checkTransactionsForBusiness = async (tinNumber: string) => {
    if (!tinNumber) return;
    
    setIsCheckingTransactions(true);
    try {
      const hasTransactionsResult = await hasTransactionsForToday(tinNumber);
      setHasTransactions(hasTransactionsResult);
    } catch {
      console.warn('Failed to check transactions for business:', tinNumber);
      setHasTransactions(false);
    } finally {
      setIsCheckingTransactions(false);
    }
  };

  const handleGenerateXReport = async () => {
    if (!selectedBusiness) {
      alert('Please select a business first');
      return;
    }

    // Double-check transactions before generating
    if (!hasTransactions) {
      alert('❌ Cannot generate X Report: No transactions found for today. Please process some transactions first.');
      return;
    }

    const success = await validateBusinessAccess(selectedBusiness);
    if (success) {
      await generateXReport(selectedBusiness);
      // Refresh history after generation
      fetchReportHistory(selectedBusiness, filters);
    }
  };

  const handleGenerateZReport = async () => {
    if (!selectedBusiness) {
      alert('Please select a business first');
      return;
    }

    // Double-check transactions before generating
    if (!hasTransactions) {
      alert('❌ Cannot generate Z Report: No transactions found for today. Please process some transactions first.');
      return;
    }

    if (!confirm('Are you sure you want to generate a Z Report? This will finalize the current fiscal day and cannot be undone.')) {
      return;
    }

    const success = await validateBusinessAccess(selectedBusiness);
    if (success) {
      await generateZReport(selectedBusiness);
      // Refresh history after generation
      fetchReportHistory(selectedBusiness, filters);
    }
  };

  const handleApplyFilters = () => {
    if (selectedBusiness) {
      const filterParams = {
        ...filters,
        start_date: dateRange.start,
        end_date: dateRange.end,
      };
      setFilters(filterParams);
      fetchReportHistory(selectedBusiness, filterParams);
    }
  };

  const filteredBusinesses = businesses.filter(business =>
    business.business_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    business.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    business.tin_number.includes(searchQuery)
  );

  const selectedBusinessData = businesses.find(b => b.tin_number === selectedBusiness);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Daily Reports</h1>
          <p className="mt-1 text-sm text-gray-600">
            Generate and manage X and Z reports for businesses
          </p>
        </div>
        
        <div className="mt-4 lg:mt-0 flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
          
          <div className="relative group">
            <button
              onClick={handleGenerateXReport}
              disabled={!selectedBusiness || isGenerating || !hasTransactions || isCheckingTransactions}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isGenerating ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : isCheckingTransactions ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileText className="h-4 w-4 mr-2" />
              )}
              {isCheckingTransactions ? 'Checking...' : 'Generate X Report'}
            </button>
            
            {selectedBusiness && !hasTransactions && !isCheckingTransactions && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-gray-800 rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                No transactions found for today
              </div>
            )}
          </div>
          
          <div className="relative group">
            <button
              onClick={handleGenerateZReport}
              disabled={!selectedBusiness || isGenerating || !hasTransactions || isCheckingTransactions}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isGenerating ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : isCheckingTransactions ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Receipt className="h-4 w-4 mr-2" />
              )}
              {isCheckingTransactions ? 'Checking...' : 'Generate Z Report'}
            </button>
            
            {selectedBusiness && !hasTransactions && !isCheckingTransactions && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-gray-800 rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                No transactions found for today
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 text-sm mt-1">{error.message}</p>
        </div>
      )}

      {/* Filters Section */}
      {showFilters && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Filter Reports</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Type
              </label>
              <select
                value={filters.report_type || ''}
                onChange={(e) => setFilters({ ...filters, report_type: e.target.value as 'X' | 'Z' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
              >
                <option value="">All Types</option>
                <option value="X">X Reports</option>
                <option value="Z">Z Reports</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleApplyFilters}
              disabled={!selectedBusiness}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Business Selection */}
        <div className="lg:col-span-1">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Select Business</h3>
              
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search businesses..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white placeholder-gray-400"
                />
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredBusinesses.map((business) => (
                  <button
                    key={business.id}
                    onClick={() => handleBusinessSelect(business.tin_number)}
                    className={`w-full text-left px-3 py-3 rounded-lg border transition-all ${
                      selectedBusiness === business.tin_number
                        ? 'bg-blue-50 border-blue-200 text-blue-900'
                        : 'bg-white border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <Building2 className={`h-5 w-5 ${
                          selectedBusiness === business.tin_number ? 'text-blue-600' : 'text-gray-400'
                        }`} />
                        <div>
                          <p className="text-sm font-medium">
                            {business.business_name || business.name}
                          </p>
                          <p className="text-xs text-gray-600">
                            TIN: {business.tin_number}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          business.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {business.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Reports List and Details */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="px-4 py-5 sm:p-6">
              {selectedBusinessData ? (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        Reports for {selectedBusinessData.business_name || selectedBusinessData.name}
                      </h3>
                      <p className="text-sm text-gray-600">TIN: {selectedBusinessData.tin_number}</p>
                      
                      {/* Transaction Status Indicator */}
                      <div className="flex items-center space-x-2 mt-2">
                        {isCheckingTransactions ? (
                          <>
                            <RefreshCw className="h-4 w-4 animate-spin text-gray-400" />
                            <span className="text-sm text-gray-500">Checking transactions...</span>
                          </>
                        ) : hasTransactions ? (
                          <>
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span className="text-sm text-green-600">Has transactions for today</span>
                          </>
                        ) : selectedBusiness ? (
                          <>
                            <AlertCircle className="h-4 w-4 text-amber-500" />
                            <span className="text-sm text-amber-600">No transactions for today</span>
                          </>
                        ) : null}
                      </div>
                    </div>
                    
                    <button
                      onClick={async () => {
                        fetchReportHistory(selectedBusiness, filters);
                        // Also refresh transaction status
                        if (selectedBusiness) {
                          checkTransactionsForBusiness(selectedBusiness);
                        }
                      }}
                      disabled={isLoading || isCheckingTransactions}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100"
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${isLoading || isCheckingTransactions ? 'animate-spin' : ''}`} />
                      Refresh
                    </button>
                  </div>

                  {isLoading ? (
                    <div className="text-center py-12">
                      <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">Loading reports...</p>
                    </div>
                  ) : reports.length > 0 ? (
                    (() => {
                      // Filter out reports with no real transaction data
                      const reportsWithTransactions = reports.filter(report => 
                        report.total_transactions && report.total_transactions > 0
                      );

                      return reportsWithTransactions.length > 0 ? (
                        <div className="space-y-4">
                          {reportsWithTransactions.map((report, index) => (
                            <ReportCard
                              key={`report-${report.id || index}-${report.report_type}-${report.created_at}`}
                              report={report}
                              isSelected={selectedReport?.id === report.id}
                              onSelect={() => setSelectedReport(report)}
                            />
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                          <p className="text-gray-600 font-medium">No transaction history for this business yet</p>
                          <p className="text-gray-500 text-sm">Reports will appear here once transactions are processed</p>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 font-medium">No transaction history for this business yet</p>
                      <p className="text-gray-500 text-sm">Reports will appear here once transactions are processed</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 font-medium">Select a business</p>
                  <p className="text-gray-500 text-sm">Choose a business to view and generate reports</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Report Details */}
      {selectedReport && (
        <ReportDetails report={selectedReport} onClose={() => setSelectedReport(null)} />
      )}
    </div>
  );
}

interface ReportCardProps {
  report: {
    id: number;
    report_type: 'X' | 'Z';
    report_date?: string | null;
    created_at?: string | null;
    total_transactions?: number;
    total_sales_amount?: number;
  };
  isSelected: boolean;
  onSelect: () => void;
}

function ReportCard({ report, isSelected, onSelect }: ReportCardProps) {
  // Safely parse dates with fallbacks
  const getValidDate = (dateString?: string | null) => {
    if (!dateString) return new Date();
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? new Date() : date;
  };

  const reportDate = getValidDate(report.report_date || report.created_at);
  const createdDate = getValidDate(report.created_at);

  // Create a meaningful report display name based on date and type
  const reportDisplayName = `${report.report_type} Report - ${format(reportDate, 'MMM dd, yyyy')}`;
  
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-lg border transition-all ${
        isSelected
          ? 'bg-blue-50 border-blue-200'
          : 'bg-white border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`p-3 rounded-lg ${
            report.report_type === 'Z' ? 'bg-red-100' : 'bg-blue-100'
          }`}>
            {report.report_type === 'Z' ? (
              <Receipt className="h-6 w-6 text-red-600" />
            ) : (
              <FileText className="h-6 w-6 text-blue-600" />
            )}
          </div>
          
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-medium text-gray-900">
                {reportDisplayName}
              </h4>
            </div>
            
            <p className="text-xs text-gray-500 mt-1">
              Generated: {format(createdDate, 'HH:mm:ss')}
            </p>
            
            <div className="flex items-center space-x-4 mt-2">
              <div className="flex items-center space-x-1">
                <Receipt className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {report.total_transactions || 0} transactions
                </span>
              </div>
              
              {(report.total_sales_amount || 0) > 0 && (
                <div className="flex items-center space-x-1">
                  <DollarSign className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900">
                    {new Intl.NumberFormat('en-RW', { 
                      style: 'currency', 
                      currency: 'RWF' 
                    }).format(report.total_sales_amount || 0)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="text-right">
          <div className="flex items-center space-x-1 text-sm text-gray-500">
            {report.report_type === 'Z' ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span>Finalized</span>
              </>
            ) : (
              <>
                <Clock className="h-4 w-4 text-blue-500" />
                <span>Interim</span>
              </>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}

interface ReportDetailsProps {
  report: {
    id: number;
    report_type: 'X' | 'Z';
    report_date?: string | null;
    created_at?: string | null;
    total_transactions?: number;
    total_sales_amount?: number;
    total_tax_amount?: number;
    total_net_amount?: number;
    cash_amount?: number;
    card_amount?: number;
    mobile_amount?: number;
    other_amount?: number;
    voided_transactions?: number;
    refunded_transactions?: number;
  };
  onClose: () => void;
}

function ReportDetails({ report, onClose }: ReportDetailsProps) {
  // Check if report has any real data
  const hasTransactions = (report.total_transactions || 0) > 0;

  // Safely parse dates with fallbacks
  const getValidDate = (dateString?: string | null) => {
    if (!dateString) return new Date();
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? new Date() : date;
  };

  const reportDate = getValidDate(report.report_date || report.created_at);
  const createdDate = getValidDate(report.created_at);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {report.report_type} Report - {format(reportDate, 'MMM dd, yyyy')}
            </h3>
            <p className="text-sm text-gray-600">
              Generated: {format(createdDate, 'PPpp')}
            </p>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {hasTransactions ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <div key="total-sales" className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-600">Total Sales</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.total_sales_amount || 0)}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                </div>
              </div>

              <div key="total-tax" className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-600">Total Tax</p>
                    <p className="text-2xl font-bold text-green-900">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.total_tax_amount || 0)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-600" />
                </div>
              </div>

              <div key="net-amount" className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-600">Net Amount</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.total_net_amount || 0)}
                    </p>
                  </div>
                  <Receipt className="h-8 w-8 text-purple-600" />
                </div>
              </div>

              <div key="total-transactions" className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-orange-600">Transactions</p>
                    <p className="text-2xl font-bold text-orange-900">{report.total_transactions}</p>
                  </div>
                  <FileText className="h-8 w-8 text-orange-600" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Payment Methods */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Payment Methods</h4>
                <div className="space-y-2">
                  <div key="payment-cash" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Cash</span>
                    <span className="text-sm font-medium">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.cash_amount || 0)}
                    </span>
                  </div>
                  <div key="payment-card" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Card</span>
                    <span className="text-sm font-medium">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.card_amount || 0)}
                    </span>
                  </div>
                  <div key="payment-mobile" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Mobile Money</span>
                    <span className="text-sm font-medium">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.mobile_amount || 0)}
                    </span>
                  </div>
                  <div key="payment-other" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Other</span>
                    <span className="text-sm font-medium">
                      {new Intl.NumberFormat('en-RW', { 
                        style: 'currency', 
                        currency: 'RWF' 
                      }).format(report.other_amount || 0)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Transaction Status */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Transaction Status</h4>
                <div className="space-y-2">
                  <div key="status-successful" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Successful</span>
                    <span className="text-sm font-medium text-green-600">
                      {(report.total_transactions || 0) - (report.voided_transactions || 0) - (report.refunded_transactions || 0)}
                    </span>
                  </div>
                  <div key="status-voided" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Voided</span>
                    <span className="text-sm font-medium text-red-600">{report.voided_transactions || 0}</span>
                  </div>
                  <div key="status-refunded" className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Refunded</span>
                    <span className="text-sm font-medium text-yellow-600">{report.refunded_transactions || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No transaction history for this business yet</h3>
            <p className="text-sm text-gray-500">
              This report contains no transaction data to display
            </p>
          </div>
        )}
      </div>
    </div>
  );
}