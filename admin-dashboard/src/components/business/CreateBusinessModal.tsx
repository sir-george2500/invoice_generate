'use client';

import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { X, Building2, Mail, Phone, MapPin, Hash } from 'lucide-react';
import { useCreateBusiness } from '@/hooks/useBusinesses';

const businessSchema = Yup.object().shape({
  name: Yup.string()
    .required('Business name is required')
    .min(2, 'Business name must be at least 2 characters')
    .max(100, 'Business name must be less than 100 characters'),
  tin_number: Yup.string()
    .required('TIN number is required')
    .matches(/^[0-9]+$/, 'TIN must contain only numbers')
    .min(9, 'TIN must be at least 9 digits')
    .max(15, 'TIN must be less than 15 digits'),
  email: Yup.string()
    .email('Invalid email format')
    .required('Email is required')
    .max(100, 'Email must be less than 100 characters'),
  phone: Yup.string()
    .matches(/^[\+]?[0-9\s\-\(\)]*$/, 'Invalid phone number format')
    .min(10, 'Phone number must be at least 10 digits')
    .max(20, 'Phone number must be less than 20 characters')
    .optional(),
  address: Yup.string()
    .required('Address is required')
    .min(10, 'Address must be at least 10 characters')
    .max(500, 'Address must be less than 500 characters'),
});

interface CreateBusinessModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface BusinessFormValues {
  name: string;
  tin_number: string;
  email: string;
  phone: string;
  address: string;
}

export function CreateBusinessModal({ isOpen, onClose }: CreateBusinessModalProps) {
  const createBusiness = useCreateBusiness();

  const handleSubmit = async (values: BusinessFormValues, { setSubmitting, resetForm }: any) => {
    try {
      const result = await createBusiness.mutateAsync({
        name: values.name,
        tin_number: values.tin_number,
        email: values.email,
        phone: values.phone || undefined,
        address: values.address,
      });

      // Show success message with admin credentials
      alert(`✅ Business created successfully!\n\nAdmin Credentials:\nUsername: ${result.admin_credentials.username}\nPassword: ${result.admin_credentials.password}\n\n⚠️ Save these credentials - they won't be shown again!`);
      
      resetForm();
      onClose();
    } catch (error: unknown) {
      const err = error as { message: string };
      alert(`❌ Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Add New Business</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <Formik
          initialValues={{
            name: '',
            tin_number: '',
            email: '',
            phone: '',
            address: '',
          }}
          validationSchema={businessSchema}
          onSubmit={handleSubmit}
        >
          {({ errors, touched, isSubmitting }) => (
            <Form className="p-6 space-y-6">
              {/* Business Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-semibold text-gray-800 mb-2">
                  Business Name *
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Field
                    id="name"
                    name="name"
                    type="text"
                    className={`w-full pl-10 pr-3 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                      errors.name && touched.name
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter business name"
                  />
                </div>
                <ErrorMessage name="name" component="div" className="mt-1 text-sm text-red-600 font-medium" />
              </div>

              {/* TIN Number */}
              <div>
                <label htmlFor="tin_number" className="block text-sm font-semibold text-gray-800 mb-2">
                  TIN Number *
                </label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Field
                    id="tin_number"
                    name="tin_number"
                    type="text"
                    className={`w-full pl-10 pr-3 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                      errors.tin_number && touched.tin_number
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter TIN number (numbers only)"
                  />
                </div>
                <ErrorMessage name="tin_number" component="div" className="mt-1 text-sm text-red-600 font-medium" />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-800 mb-2">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Field
                    id="email"
                    name="email"
                    type="email"
                    className={`w-full pl-10 pr-3 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                      errors.email && touched.email
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter business email"
                  />
                </div>
                <ErrorMessage name="email" component="div" className="mt-1 text-sm text-red-600 font-medium" />
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="block text-sm font-semibold text-gray-800 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Field
                    id="phone"
                    name="phone"
                    type="tel"
                    className={`w-full pl-10 pr-3 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                      errors.phone && touched.phone
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter phone number (optional)"
                  />
                </div>
                <ErrorMessage name="phone" component="div" className="mt-1 text-sm text-red-600 font-medium" />
              </div>

              {/* Address */}
              <div>
                <label htmlFor="address" className="block text-sm font-semibold text-gray-800 mb-2">
                  Business Address *
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
                  <Field
                    id="address"
                    name="address"
                    as="textarea"
                    rows={3}
                    className={`w-full pl-10 pr-3 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none ${
                      errors.address && touched.address
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder="Enter complete business address"
                  />
                </div>
                <ErrorMessage name="address" component="div" className="mt-1 text-sm text-red-600 font-medium" />
              </div>

              {/* Form Actions */}
              <div className="flex space-x-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-3 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || createBusiness.isPending}
                  className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-semibold flex items-center justify-center"
                >
                  {isSubmitting || createBusiness.isPending ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Creating...
                    </>
                  ) : (
                    'Create Business'
                  )}
                </button>
              </div>
            </Form>
          )}
        </Formik>
      </div>
    </div>
  );
}