<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()
const searchStore = useSearchStore()
const { $api } = useNuxtApp()
const { registerRefresh } = useKbList()

const open = ref(false)

const displayName = computed(() => {
  const user = authStore.user
  if (!user) return 'Account'
  const d = user.greeting_display
  if (d === 'full_name' && user.first_name && user.last_name) return `${user.first_name} ${user.last_name}`
  if ((d === 'full_name' || d === 'first_name') && user.first_name) return user.first_name
  return user.username
})

interface KB {
  id: string
  name: string
}

const { data: kbs, refresh: refreshKbs } = await useFetch<KB[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

registerRefresh(refreshKbs)

// When new KBs appear (e.g. after accepting an invitation), auto-add them to the
// active list so they are searched immediately. Only applies when the user has an
// explicit selection (not null/"all" mode, where every KB is already included).
watch(kbs, (newKbs, oldKbs) => {
  if (!newKbs || searchStore.activeKbIds === null) return
  const knownIds = new Set((oldKbs ?? []).map(kb => kb.id))
  const addedIds = newKbs.filter(kb => !knownIds.has(kb.id)).map(kb => kb.id)
  if (addedIds.length) {
    searchStore.activeKbIds = [...searchStore.activeKbIds, ...addedIds]
  }
})

// ── KB toggle helpers ──────────────────────────────────────────────────────

function isKbActive(id: string): boolean {
  if (searchStore.activeKbIds === null) return true
  return searchStore.activeKbIds.includes(id)
}

const allActive = computed(() => {
  if (searchStore.activeKbIds === null) return true
  const list = kbs.value ?? []
  return list.length > 0 && list.every(kb => searchStore.activeKbIds!.includes(kb.id))
})

function toggleAll(val: boolean) {
  searchStore.activeKbIds = val ? null : []
}

function toggleKb(id: string, val: boolean) {
  if (searchStore.activeKbIds === null) {
    // Currently in "all" mode. Turning one off → switch to explicit list.
    if (!val) {
      searchStore.activeKbIds = (kbs.value ?? []).map(kb => kb.id).filter(kid => kid !== id)
    }
    return
  }
  if (val && !searchStore.activeKbIds.includes(id)) {
    searchStore.activeKbIds = [...searchStore.activeKbIds, id]
  } else if (!val) {
    searchStore.activeKbIds = searchStore.activeKbIds.filter(k => k !== id)
  }
}

// ── Nav ────────────────────────────────────────────────────────────────────

const navItems = computed(() => [
  { label: 'Search', to: '/', icon: 'i-lucide-search' },
  { label: 'Bookmarks', to: '/bookmarks', icon: 'i-lucide-bookmark' },
  { label: 'Settings', to: '/settings/knowledge-bases', icon: 'i-lucide-settings' },
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

          <!-- "All knowledge bases" master toggle — only shown when more than one KB -->
          <div
            v-if="kbs && kbs.length > 1"
            class="flex items-center gap-2 px-3 py-1.5 cursor-pointer select-none"
            @click.stop="toggleAll(!allActive)"
          >
            <USwitch
              :model-value="allActive"
              size="xs"
              @update:model-value="toggleAll"
              @click.stop
            />
            <span class="text-sm text-muted">All knowledge bases</span>
          </div>

          <UNavigationMenu
            :items="kbItems"
            orientation="vertical"
            :ui="{ link: 'overflow-hidden' }"
          >
            <template #kb-leading="{ item }">
              <USwitch
                :model-value="isKbActive((item as any).id)"
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
            v-if="authStore.isSuperuser"
            v-bind="{
              label: collapsed ? undefined : 'Admin',
              icon: 'i-lucide-shield',
            }"
            color="neutral"
            variant="ghost"
            block
            :square="collapsed"
            to="/admin"
          />
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
