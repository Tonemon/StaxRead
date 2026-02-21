import { defineStore } from "pinia"

interface UserInfo {
  id: string
  username: string
  email: string
  is_superuser: boolean
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: null as string | null,
    user: null as UserInfo | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    isSuperuser: (state) => state.user?.is_superuser ?? false,
  },
  actions: {
    setTokens(access: string) {
      this.accessToken = access
    },
    setUser(user: UserInfo) {
      this.user = user
    },
    clear() {
      this.accessToken = null
      this.user = null
    },
  },
  persist: true,
})
