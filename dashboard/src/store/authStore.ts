import { create } from "zustand";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("unitforge_token"),
  isAuthenticated: !!localStorage.getItem("unitforge_token"),
  setToken: (token: string) => {
    localStorage.setItem("unitforge_token", token);
    set({ token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("unitforge_token");
    set({ token: null, isAuthenticated: false });
  },
}));
