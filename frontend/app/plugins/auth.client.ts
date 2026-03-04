/**
 * Runs once on every hard page load (client-only).
 * If a stored token exists, verify it against /auth/me/ and refresh the
 * user record in the store.  This guarantees is_superuser is correctly
 * set before any layout computes navItems — even when useLocalStorage
 * hasn't fully synced during Nuxt's initial render pass.
 * A 401 response means the token has expired: clear auth and redirect.
 */
export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()
  const colorMode = useColorMode()

  if (!authStore.accessToken) return

  try {
    const user = await $fetch<{ id: string; username: string; email: string; is_superuser: boolean; theme: 'system' | 'light' | 'dark' }>(
      `${config.public.apiBase}/auth/me/`,
      { headers: { Authorization: `Bearer ${authStore.accessToken}` } },
    )
    authStore.setUser(user)
    colorMode.preference = user.theme ?? 'system'
  } catch {
    authStore.clear()
    await navigateTo('/login')
  }
})
