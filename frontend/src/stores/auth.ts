import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserRead } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserRead | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: UserRead) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setTokens: (access, refresh) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ accessToken: null, refreshToken: null, user: null });
      },

      isAuthenticated: () => Boolean(get().accessToken),
    }),
    {
      name: "fleetops-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);
