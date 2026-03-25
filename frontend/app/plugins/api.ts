function getCsrfToken(): string {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()
  const router = useRouter()

  let isRefreshing = false

  const api = $fetch.create({
    baseURL: config.public.apiBase,
    credentials: 'include',
    onRequest({ options }) {
      const csrf = getCsrfToken()
      if (csrf) {
        options.headers = {
          ...(options.headers as Record<string, string>),
          'X-CSRFToken': csrf,
        }
      }
    },
    async onResponseError({ request, options, response }) {
      if (response.status === 401 && authStore.isAuthenticated) {
        if (isRefreshing) {
          authStore.clear()
          await router.push('/login?session_expired=1')
          return
        }
        isRefreshing = true
        try {
          await $fetch(`${config.public.apiBase}/auth/refresh/`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'X-CSRFToken': getCsrfToken() },
          })
          isRefreshing = false
          // Replay the original request
          await $fetch(request, { ...options })
        }
        catch {
          isRefreshing = false
          authStore.clear()
          await router.push('/login?session_expired=1')
        }
      }
    },
  })

  return { provide: { api } }
})
