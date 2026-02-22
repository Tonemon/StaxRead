export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()

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
  })

  return { provide: { api } }
})
