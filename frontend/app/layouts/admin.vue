<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()

const navLinks = computed(() => [
  { label: 'Knowledge Bases', to: '/settings/knowledge-bases', icon: 'i-lucide-book-open' },
  { label: 'Git Credentials', to: '/settings/git-credentials', icon: 'i-lucide-key' },
  ...(authStore.isSuperuser ? [{ label: 'Users', to: '/settings/users', icon: 'i-lucide-users' }] : []),
  { label: 'Account', to: '/settings/account', icon: 'i-lucide-user-circle' },
])

const open = ref(false)
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
          <span v-if="!collapsed" class="text-xl font-bold text-highlighted">Admin</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :items="navLinks"
          :collapsed="collapsed"
          orientation="vertical"
        />
      </template>

      <template #footer="{ collapsed }">
        <UButton
          v-bind="{
            label: collapsed ? undefined : (authStore.user?.username || 'Account'),
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
