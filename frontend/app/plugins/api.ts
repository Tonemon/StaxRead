export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()
  const router = useRouter()

  const api = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (authStore.accessToken) {
        options.headers = {
          ...(options.headers as Record<string, string>),
          Authorization: `Bearer ${authStore.accessToken}`,
        }
      }
    },
    async onResponseError({ response }) {
      if (response.status === 401 && authStore.isAuthenticated) {
        authStore.clear()
        await router.push('/login?session_expired=1')
      }
    },
  })

  return { provide: { api } }
})
