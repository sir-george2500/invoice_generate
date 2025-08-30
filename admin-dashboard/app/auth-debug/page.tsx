'use client';

import { useAuthStore } from '@/stores';
import { useEffect, useState } from 'react';

export default function AuthDebugPage() {
  const { user, isAuthenticated, isLoading, verifyToken } = useAuthStore();
  const [cookies, setCookies] = useState('');
  const [localStorage, setLocalStorage] = useState('');

  useEffect(() => {
    // Check cookies
    setCookies(document.cookie);
    
    // Check localStorage
    setLocalStorage(JSON.stringify({
      token: window.localStorage.getItem('admin_token'),
      user: window.localStorage.getItem('admin_user')
    }));

    // Verify token
    verifyToken();
  }, [verifyToken]);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Authentication Debug</h1>
      
      <div className="grid gap-6">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold mb-4">Auth Store State</h2>
          <div className="space-y-2 text-sm">
            <p><strong>Is Authenticated:</strong> {isAuthenticated ? 'Yes' : 'No'}</p>
            <p><strong>Is Loading:</strong> {isLoading ? 'Yes' : 'No'}</p>
            <p><strong>User:</strong> {user ? JSON.stringify(user, null, 2) : 'null'}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold mb-4">Browser Storage</h2>
          <div className="space-y-2 text-sm">
            <p><strong>Cookies:</strong> {cookies || 'None'}</p>
            <p><strong>LocalStorage:</strong> {localStorage}</p>
          </div>
        </div>

        <div className="flex space-x-4">
          <button 
            onClick={() => window.location.href = '/dashboard'}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
          
          <button 
            onClick={() => {
              window.localStorage.clear();
              document.cookie = 'admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
              window.location.href = '/';
            }}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Clear Auth & Go to Login
          </button>
        </div>
      </div>
    </div>
  );
}