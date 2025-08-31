'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';
import { Lock, User, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { ClientOnly } from '@/components/ClientOnly';

// Validation schema
const loginSchema = Yup.object().shape({
  username: Yup.string()
    .min(2, 'Username must be at least 2 characters')
    .max(50, 'Username must be less than 50 characters')
    .required('Username is required'),
  password: Yup.string()
    .min(6, 'Password must be at least 6 characters')
    .required('Password is required'),
});

interface LoginFormValues {
  username: string;
  password: string;
}

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const { isAuthenticated, isLoading, login, error } = useAuth();

  // Check if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (values: LoginFormValues) => {
    try {
      await login(values);
      // Navigation handled automatically in useAuth hook
    } catch (error) {
      // Error handling is done by React Query
    }
  };

  return (
    <ClientOnly fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    }>
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-lg p-8 border border-gray-200">
            {/* Header */}
            <div className="text-center mb-8">
              {/* Use the actual logo */}
              <div className="mx-auto w-20 h-20 mb-4 flex items-center justify-center">
                <img
                  src="/logo.png"
                  alt="ALSM EBM Logo"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    // Fallback to icon if logo fails to load
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const fallback = target.nextElementSibling as HTMLDivElement;
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
                <div className="w-16 h-16 bg-blue-600 rounded-full items-center justify-center hidden">
                  <Lock className="w-8 h-8 text-white" />
                </div>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">ALSM EBM Admin</h1>
              <p className="text-sm text-gray-600">
                Administrative dashboard for EBM integration management
              </p>
            </div>

            {/* Professional Formik Form */}
            <Formik
              initialValues={{ username: '', password: '' }}
              validationSchema={loginSchema}
              onSubmit={handleSubmit}
            >
              {({ errors, touched, isSubmitting, values }: {
                errors: Record<string, string>;
                touched: Record<string, boolean>;
                isSubmitting: boolean;
                values: LoginFormValues;
              }) => (
                <Form className="space-y-6">
                  {!!error && (
                    <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                      <span className="text-sm text-red-800 font-medium">
                        Login failed. Please try again.
                      </span>
                    </div>
                  )}

                  <div>
                    <label htmlFor="username" className="block text-sm font-semibold text-gray-800 mb-2">
                      Username
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                      <Field
                        id="username"
                        name="username"
                        type="text"
                        className={`block w-full pl-10 pr-3 py-3 text-gray-900 bg-white border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500 transition-colors ${errors.username && touched.username
                          ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                          : 'border-gray-300'
                          }`}
                        placeholder="Enter your username"
                      />
                    </div>
                    {errors.username && touched.username && (
                      <div className="mt-1 text-sm text-red-600 font-medium">{errors.username}</div>
                    )}
                  </div>

                  <div>
                    <label htmlFor="password" className="block text-sm font-semibold text-gray-800 mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                      <Field
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        className={`block w-full pl-10 pr-10 py-3 text-gray-900 bg-white border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500 transition-colors ${errors.password && touched.password
                          ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                          : 'border-gray-300'
                          }`}
                        placeholder="Enter your password"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 transition-colors"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                    {errors.password && touched.password && (
                      <div className="mt-1 text-sm text-red-600 font-medium">{errors.password}</div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting || isLoading || !values.username || !values.password}
                    className="w-full flex justify-center items-center py-3 px-4 border-2 border-transparent rounded-lg shadow-sm text-base font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:opacity-60 transition-all duration-200"
                  >
                    {isSubmitting || isLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="text-white font-semibold">Signing in...</span>
                      </>
                    ) : (
                      <span className="text-white font-semibold">Sign In</span>
                    )}
                  </button>
                </Form>
              )}
            </Formik>

            {/* Footer */}
            <div className="mt-8 text-center border-t border-gray-200 pt-6">
              <p className="text-xs text-gray-600 font-medium">
                © 2024 ALSM Consulting. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ClientOnly>
  );
}
