function getCsrfToken(): string {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export const useAuth = () => {
  const store = useAuthStore()
  const config = useRuntimeConfig()
  const router = useRouter()
  const colorMode = useColorMode()

  const login = async (username: string, password: string) => {
    await $fetch(`${config.public.apiBase}/auth/login/`, {
      method: 'POST',
      body: { username, password },
      credentials: 'include',
      headers: { 'X-CSRFToken': getCsrfToken() },
    })
    const user = await $fetch<{ id: string; username: string; email: string; first_name: string; last_name: string; is_superuser: boolean; show_greeting: boolean; greeting_display: 'username' | 'full_name' | 'first_name'; theme: 'system' | 'light' | 'dark' }>(
      `${config.public.apiBase}/auth/me/`,
      { credentials: 'include' },
    )
    store.setUser(user)
    colorMode.preference = user.theme ?? 'system'
    await router.push('/')
  }

  const logout = async () => {
    await $fetch(`${config.public.apiBase}/auth/logout/`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => {})
    store.clear()
    await router.push('/login')
  }

  return { login, logout, store }
}
