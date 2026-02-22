import { defineStore } from 'pinia'

interface UserInfo {
  id: string
  username: string
  email: string
  is_superuser: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = useLocalStorage<string | null>('staxread_token', null)
  const user = useLocalStorage<UserInfo | null>('staxread_user', null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)

  function setTokens(access: string) {
    accessToken.value = access
  }

  function setUser(u: UserInfo) {
    user.value = u
  }

  function clear() {
    accessToken.value = null
    user.value = null
  }

  return { accessToken, user, isAuthenticated, isSuperuser, setTokens, setUser, clear }
})
