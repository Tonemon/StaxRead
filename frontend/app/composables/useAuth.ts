export const useAuth = () => {
  const store = useAuthStore()
  const config = useRuntimeConfig()
  const router = useRouter()

  const login = async (username: string, password: string) => {
    const resp = await $fetch<{ access: string; refresh: string }>(
      `${config.public.apiBase}/auth/login/`,
      { method: 'POST', body: { username, password } }
    )
    store.setTokens(resp.access)
    const user = await $fetch<{ id: string; username: string; email: string; is_superuser: boolean }>(
      `${config.public.apiBase}/auth/me/`,
      { headers: { Authorization: `Bearer ${resp.access}` } }
    )
    store.setUser(user)
    await router.push('/')
  }

  const logout = async () => {
    if (store.accessToken) {
      await $fetch(`${config.public.apiBase}/auth/logout/`, {
        method: 'POST',
        body: { refresh: '' },
        headers: { Authorization: `Bearer ${store.accessToken}` },
      }).catch(() => {})
    }
    store.clear()
    await router.push('/login')
  }

  return { login, logout, store }
}
