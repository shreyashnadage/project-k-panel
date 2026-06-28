import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AdminUser {
  clientId: string
  email: string
  companyName: string
}

interface DashboardStore {
  darkMode: boolean
  sidebarCollapsed: boolean
  accessToken: string | null
  adminUser: AdminUser | null
  setDarkMode: (dark: boolean) => void
  setSidebarCollapsed: (v: boolean) => void
  setAccessToken: (token: string | null) => void
  setAdminUser: (user: AdminUser | null) => void
  clearAuth: () => void
}

export const useDashboardStore = create<DashboardStore>()(
  persist(
    (set) => ({
      darkMode: true,
      sidebarCollapsed: false,
      accessToken: null,
      adminUser: null,
      setDarkMode: (dark) => set({ darkMode: dark }),
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      setAccessToken: (token) => set({ accessToken: token }),
      setAdminUser: (user) => set({ adminUser: user }),
      clearAuth: () => set({ accessToken: null, adminUser: null }),
    }),
    {
      name: 'tally-sync-ui',
      partialize: (s) => ({
        darkMode: s.darkMode,
        sidebarCollapsed: s.sidebarCollapsed,
        accessToken: s.accessToken,
        adminUser: s.adminUser,
      }),
    }
  )
)
