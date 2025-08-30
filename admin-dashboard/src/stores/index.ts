import { useAuthStore } from './authStore';
import { useBusinessStore } from './businessStore';
import { useReportStore } from './reportStore';
import { useUIStore } from './uiStore';

// Re-export all stores directly - no wrapper hooks needed
export { useAuthStore } from './authStore';
export { useBusinessStore } from './businessStore';
export { useReportStore } from './reportStore';
export { useUIStore } from './uiStore';

// Combined store hook for common patterns
export const useAppStore = () => {
  const auth = useAuthStore();
  const business = useBusinessStore();
  const report = useReportStore();
  const ui = useUIStore();

  return {
    auth,
    business,
    report,
    ui,
  };
};

// Helper hooks for specific use cases
export const useNotifications = () => {
  const { notifications, addNotification, removeNotification, clearNotifications } = useUIStore();
  
  const showSuccess = (title: string, message?: string) => {
    addNotification({ type: 'success', title, message });
  };
  
  const showError = (title: string, message?: string) => {
    addNotification({ type: 'error', title, message });
  };
  
  const showWarning = (title: string, message?: string) => {
    addNotification({ type: 'warning', title, message });
  };
  
  const showInfo = (title: string, message?: string) => {
    addNotification({ type: 'info', title, message });
  };

  return {
    notifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeNotification,
    clearNotifications,
  };
};