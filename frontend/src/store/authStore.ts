import { create } from 'zustand';
import api from '../utils/api';
import { User } from '../types/user';

interface SessionResponse {
  user: User;
  active_games: unknown[];
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, nickname: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  checkSession: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/auth/login', { username, password });
      const { data } = await api.get<User>('/users/me');
      set({ user: data, isAuthenticated: true, error: null });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      set({ error: message, isAuthenticated: false, user: null });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (username: string, password: string, nickname: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/auth/register', { username, password, nickname });
      const { data } = await api.get<User>('/users/me');
      set({ user: data, isAuthenticated: true, error: null });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      set({ error: message });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      set({ user: null, isAuthenticated: false });
    }
  },

  refresh: async () => {
    try {
      await api.post('/auth/refresh');
      const { data } = await api.get<User>('/users/me');
      set({ user: data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  checkSession: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get<SessionResponse>('/users/session');
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
