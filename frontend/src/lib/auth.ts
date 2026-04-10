import { create } from 'zustand'
import type { User, Organization } from '@/types'

interface AuthState {
  token: string | null
  user: User | null
  currentOrg: Organization | null
  setToken: (token: string) => void
  setUser: (user: User) => void
  setCurrentOrg: (org: Organization) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token:
    typeof window !== 'undefined' ? localStorage.getItem('compliai_token') : null,
  user: null,
  currentOrg: null,

  setToken: (token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('compliai_token', token)
    }
    set({ token })
  },

  setUser: (user: User) => set({ user }),

  setCurrentOrg: (org: Organization) => set({ currentOrg: org }),

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('compliai_token')
    }
    set({ token: null, user: null, currentOrg: null })
  },

  isAuthenticated: () => !!get().token,
}))
