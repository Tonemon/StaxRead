<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()
const searchStore = useSearchStore()
const { $api } = useNuxtApp()

interface KB {
  id: string
  name: string
}

const { data: kbs } = await useFetch<KB[]>("/knowledge-bases/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

const toggledKbs = ref<Record<string, boolean>>({})

function updateActiveKbs() {
  searchStore.activeKbIds = Object.entries(toggledKbs.value)
    .filter(([, v]) => v)
    .map(([k]) => k)
}

const navLinks = [
  { label: "Search", to: "/", icon: "i-heroicons-magnifying-glass" },
  { label: "Bookmarks", to: "/bookmarks", icon: "i-heroicons-bookmark" },
]
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
    <aside class="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col shrink-0">
      <div class="p-4 border-b border-gray-200 dark:border-gray-800">
        <NuxtLink to="/" class="font-bold text-lg text-gray-900 dark:text-white">StaxRead</NuxtLink>
      </div>
      <nav class="flex-1 overflow-y-auto p-3 space-y-1">
        <NuxtLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          active-class="bg-gray-100 dark:bg-gray-800"
        >
          <UIcon :name="link.icon" class="w-4 h-4" />
          {{ link.label }}
        </NuxtLink>
        <NuxtLink
          v-if="authStore.isSuperuser"
          to="/admin"
          class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          active-class="bg-gray-100 dark:bg-gray-800"
        >
          <UIcon name="i-heroicons-cog-6-tooth" class="w-4 h-4" />
          Admin
        </NuxtLink>
        <div v-if="kbs && kbs.length" class="pt-3">
          <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Knowledge Bases
          </p>
          <div
            v-for="kb in kbs"
            :key="kb.id"
            class="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <UToggle
              v-model="toggledKbs[kb.id]"
              size="xs"
              @update:model-value="updateActiveKbs"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300 truncate">{{ kb.name }}</span>
          </div>
        </div>
      </nav>
      <div class="p-3 border-t border-gray-200 dark:border-gray-800">
        <div class="text-xs text-gray-400 px-3 mb-2 truncate">{{ authStore.user?.username }}</div>
        <UButton variant="ghost" color="neutral" size="sm" block @click="logout">
          Sign out
        </UButton>
      </div>
    </aside>
    <main class="flex-1 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
