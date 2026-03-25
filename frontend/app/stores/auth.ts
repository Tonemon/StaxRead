import { defineStore } from 'pinia'

export interface UserInfo {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  is_superuser: boolean
  show_greeting: boolean
  greeting_display: 'username' | 'full_name' | 'first_name'
  theme: 'system' | 'light' | 'dark'
}

export const useAuthStore = defineStore('auth', () => {
  const user = useLocalStorage<UserInfo | null>('staxread_user', null)

  const isAuthenticated = computed(() => !!user.value)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)

  function setUser(u: UserInfo) {
    user.value = u
  }

  function clear() {
    user.value = null
  }

  return { user, isAuthenticated, isSuperuser, setUser, clear }
})
