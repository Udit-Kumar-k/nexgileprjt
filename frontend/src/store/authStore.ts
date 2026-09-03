import { create } from 'zustand';
import api from '../api/client';
import { User, UserRole } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  switchRole: (newRole: UserRole) => Promise<void>;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('decarbx_token'),
  isAuthenticated: !!localStorage.getItem('decarbx_token'),
  isLoading: true,

  setAuth: (user: User, token: string) => {
    localStorage.setItem('decarbx_token', token);
    set({ user, token, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem('decarbx_token');
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },

  switchRole: async (newRole: UserRole) => {
    try {
      const res = await api.post('/auth/switch-role', { role: newRole });
      const { access_token, user } = res.data;
      get().setAuth(user, access_token);
    } catch (err) {
      console.error("Failed to switch role:", err);
    }
  },

  initializeAuth: async () => {
    const token = localStorage.getItem('decarbx_token');
    if (!token) {
      set({ isLoading: false, isAuthenticated: false, user: null });
      return;
    }

    try {
      const res = await api.get('/auth/me');
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch (err) {
      localStorage.removeItem('decarbx_token');
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
