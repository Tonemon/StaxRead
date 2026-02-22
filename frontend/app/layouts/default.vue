<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()
const searchStore = useSearchStore()
const { $api } = useNuxtApp()

const open = ref(false)

interface KB {
  id: string
  name: string
}

const { data: kbs } = await useFetch<KB[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

function toggleKb(id: string, val: boolean) {
  if (val && !searchStore.activeKbIds.includes(id)) {
    searchStore.activeKbIds = [...searchStore.activeKbIds, id]
  } else if (!val) {
    searchStore.activeKbIds = searchStore.activeKbIds.filter(k => k !== id)
  }
}

const navItems = computed(() => [
  { label: 'Search', to: '/', icon: 'i-lucide-search' },
  { label: 'Bookmarks', to: '/bookmarks', icon: 'i-lucide-bookmark' },
  ...(authStore.isSuperuser ? [{ label: 'Admin', to: '/admin/knowledge-bases', icon: 'i-lucide-settings' }] : []),
])

const kbItems = computed(() =>
  (kbs.value || []).map(kb => ({
    id: kb.id,
    label: kb.name,
    slot: 'kb' as const,
    icon: 'i-lucide-database',
  }))
)
</script>

<template>
  <UDashboardGroup unit="rem">
    <UDashboardSidebar
      id="default"
      v-model:open="open"
      :min-size="12"
      collapsible
      resizable
      class="border-r-0 py-4"
    >
      <template #header="{ collapsed }">
        <NuxtLink to="/" class="flex items-end gap-0.5">
          <Logo class="h-8 w-auto shrink-0" />
          <span v-if="!collapsed" class="text-xl font-bold text-highlighted">StaxRead</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :items="navItems"
          :collapsed="collapsed"
          orientation="vertical"
        />

        <template v-if="!collapsed && kbItems.length">
          <p class="px-3 mt-4 text-xs font-semibold text-dimmed uppercase tracking-wider mb-1">
            Knowledge Bases
          </p>
          <UNavigationMenu
            :items="kbItems"
            orientation="vertical"
            :ui="{ link: 'overflow-hidden' }"
          >
            <template #kb-leading="{ item }">
              <USwitch
                :model-value="searchStore.activeKbIds.includes((item as any).id)"
                size="xs"
                @update:model-value="(val: boolean) => toggleKb((item as any).id, val)"
                @click.stop.prevent
              />
            </template>
          </UNavigationMenu>
        </template>
      </template>

      <template #footer="{ collapsed }">
        <template v-if="authStore.isAuthenticated">
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
        <UButton
          v-else
          :label="collapsed ? '' : 'Sign in'"
          icon="i-lucide-log-in"
          color="neutral"
          variant="ghost"
          class="w-full"
          to="/login"
        />
      </template>
    </UDashboardSidebar>

    <div class="flex-1 flex m-4 lg:ml-0 rounded-lg ring ring-default bg-default/75 shadow min-w-0">
      <slot />
    </div>
  </UDashboardGroup>
</template>
