import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Token } from '../types'

interface AuthState {
  token: string | null
  user: User | null
  expiresAt: Date | null
  isAuthenticated: boolean

  // Actions
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      expiresAt: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        const credentials = btoa(`${username}:${password}`)

        const response = await fetch('/auth/login', {
          method: 'POST',
          headers: {
            'Authorization': `Basic ${credentials}`,
          },
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Login failed')
        }

        const data: Token = await response.json()

        set({
          token: data.access_token,
          user: { username },
          expiresAt: new Date(data.expires_at),
          isAuthenticated: true,
        })
      },

      logout: () => {
        set({
          token: null,
          user: null,
          expiresAt: null,
          isAuthenticated: false,
        })
      },

      checkAuth: () => {
        const { token, expiresAt } = get()
        if (!token || !expiresAt) return false

        // Check if token is expired
        if (new Date() > new Date(expiresAt)) {
          get().logout()
          return false
        }

        return true
      },
    }),
    {
      name: 'admin-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        expiresAt: state.expiresAt,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
