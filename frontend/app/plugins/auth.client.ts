/**
 * Runs once on every hard page load (client-only).
 * Ensures the CSRF cookie is set, then verifies session against /auth/me/.
 * A 401 means the access token has expired: clear auth and redirect.
 */
export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()
  const colorMode = useColorMode()

  // Always fetch CSRF cookie first so subsequent POST requests can include it.
  await $fetch(`${config.public.apiBase}/auth/csrf/`, { credentials: 'include' }).catch(() => {})

  if (!authStore.user) return

  try {
    const user = await $fetch<{ id: string; username: string; email: string; is_superuser: boolean; theme: 'system' | 'light' | 'dark' }>(
      `${config.public.apiBase}/auth/me/`,
      { credentials: 'include' },
    )
    authStore.setUser(user)
    colorMode.preference = user.theme ?? 'system'
  }
  catch {
    authStore.clear()
    await navigateTo('/login')
  }
})
