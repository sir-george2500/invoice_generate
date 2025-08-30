import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  
  // Modal states
  modals: {
    createBusiness: boolean;
    editBusiness: boolean;
    confirmDelete: boolean;
    reportDetails: boolean;
  };
  
  // Loading states for specific actions
  actionLoading: {
    [key: string]: boolean;
  };
  
  // Toast notifications
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    duration?: number;
  }>;

  // Actions
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  
  // Modal actions
  openModal: (modal: keyof UIState['modals']) => void;
  closeModal: (modal: keyof UIState['modals']) => void;
  closeAllModals: () => void;
  
  // Loading actions
  setActionLoading: (action: string, loading: boolean) => void;
  
  // Notification actions
  addNotification: (notification: Omit<UIState['notifications'][0], 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      sidebarOpen: false,
      modals: {
        createBusiness: false,
        editBusiness: false,
        confirmDelete: false,
        reportDetails: false,
      },
      actionLoading: {},
      notifications: [],

      // Actions
      setSidebarOpen: (open) => {
        set((state) => {
          state.sidebarOpen = open;
        });
      },

      toggleSidebar: () => {
        set((state) => {
          state.sidebarOpen = !state.sidebarOpen;
        });
      },

      // Modal actions
      openModal: (modal) => {
        set((state) => {
          state.modals[modal] = true;
        });
      },

      closeModal: (modal) => {
        set((state) => {
          state.modals[modal] = false;
        });
      },

      closeAllModals: () => {
        set((state) => {
          Object.keys(state.modals).forEach((key) => {
            state.modals[key as keyof typeof state.modals] = false;
          });
        });
      },

      // Loading actions
      setActionLoading: (action, loading) => {
        set((state) => {
          state.actionLoading[action] = loading;
        });
      },

      // Notification actions
      addNotification: (notification) => {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        
        set((state) => {
          state.notifications.push({
            ...notification,
            id,
            duration: notification.duration || 5000,
          });
        });

        // Auto remove notification after duration
        const duration = notification.duration || 5000;
        setTimeout(() => {
          get().removeNotification(id);
        }, duration);
      },

      removeNotification: (id) => {
        set((state) => {
          state.notifications = state.notifications.filter(n => n.id !== id);
        });
      },

      clearNotifications: () => {
        set((state) => {
          state.notifications = [];
        });
      },
    })),
    { name: 'ui-store' }
  )
);