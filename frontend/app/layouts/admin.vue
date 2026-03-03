<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()
const route = useRoute()
const { $api } = useNuxtApp()

const navLinks = [
  { label: 'Knowledge Bases', to: '/settings/knowledge-bases', icon: 'i-lucide-book-open' },
  { label: 'Git Credentials', to: '/settings/git-credentials', icon: 'i-lucide-key' },
  { label: 'Sharing', to: '/settings/sharing', icon: 'i-lucide-share-2' },
  { label: 'Teams', to: '/settings/teams', icon: 'i-lucide-users' },
  { label: 'Account', to: '/settings/account', icon: 'i-lucide-user-circle' },
]

interface Team { id: string; name: string; my_role: string }

const { data: teams } = await useFetch<Team[]>('/teams/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Team[],
})

const teamId = computed(() => {
  // Explicit team route takes priority
  const match = route.path.match(/^\/settings\/teams\/([^/]+)\//)
  if (match) return match[1]
  // Single-team member: always surface that team's sub-nav
  if (teams.value?.length === 1) return teams.value[0].id
  return null
})

const activeTeam = computed(() => teams.value?.find(t => t.id === teamId.value) ?? null)

const teamSubNav = computed(() => {
  if (!teamId.value) return null
  const id = teamId.value
  return [
    { label: 'General', to: `/settings/teams/${id}/general`, icon: 'i-lucide-settings' },
    { label: 'Knowledge Bases', to: `/settings/teams/${id}/knowledge-bases`, icon: 'i-lucide-book-open' },
    { label: 'Members', to: `/settings/teams/${id}/members`, icon: 'i-lucide-users' },
    { label: 'Git Credentials', to: `/settings/teams/${id}/git-credentials`, icon: 'i-lucide-key' },
    { label: 'API Tokens', to: `/settings/teams/${id}/api-tokens`, icon: 'i-lucide-zap' },
  ]
})

const open = ref(false)

const displayName = computed(() => {
  const user = authStore.user
  if (!user) return 'Account'
  const d = user.greeting_display
  if (d === 'full_name' && user.first_name && user.last_name) return `${user.first_name} ${user.last_name}`
  if ((d === 'full_name' || d === 'first_name') && user.first_name) return user.first_name
  return user.username
})
</script>

<template>
  <UDashboardGroup unit="rem">
    <UDashboardSidebar
      id="admin"
      v-model:open="open"
      :min-size="12"
      collapsible
      resizable
      class="border-r-0 py-4"
    >
      <template #header="{ collapsed }">
        <NuxtLink to="/" class="flex items-end gap-0.5">
          <Logo class="h-8 w-auto shrink-0" />
          <span v-if="!collapsed" class="text-xl font-bold text-highlighted">Settings</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :items="navLinks"
          :collapsed="collapsed"
          orientation="vertical"
        />
        <template v-if="teamSubNav && !collapsed">
          <div class="mt-4 px-3 mb-1">
            <p class="text-xs font-semibold text-dimmed uppercase tracking-wider">{{ activeTeam?.name ?? 'Team Settings' }}</p>
          </div>
          <UNavigationMenu
            :items="teamSubNav"
            orientation="vertical"
          />
        </template>
      </template>

      <template #footer="{ collapsed }">
        <UButton
          v-bind="{
            label: collapsed ? undefined : displayName,
            trailingIcon: collapsed ? undefined : 'i-lucide-log-out',
          }"
          color="neutral"
          variant="ghost"
          block
          :square="collapsed"
          @click="logout"
        />
      </template>
    </UDashboardSidebar>

    <div class="flex-1 flex m-4 lg:ml-0 rounded-lg ring ring-default bg-default/75 shadow min-w-0">
      <slot />
    </div>
  </UDashboardGroup>
</template>
