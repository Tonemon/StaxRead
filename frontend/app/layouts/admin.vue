<script setup lang="ts">
const { logout } = useAuth()
const authStore = useAuthStore()

const navLinks = [
  { label: "Knowledge Bases", to: "/admin/knowledge-bases", icon: "i-heroicons-book-open" },
  { label: "Git Credentials", to: "/admin/git-credentials", icon: "i-heroicons-key" },
  { label: "Users", to: "/admin/users", icon: "i-heroicons-users", superuserOnly: true },
]

const visibleLinks = computed(() =>
  navLinks.filter((l) => !l.superuserOnly || authStore.isSuperuser)
)
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
    <aside class="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col shrink-0">
      <div class="p-4 border-b border-gray-200 dark:border-gray-800">
        <NuxtLink to="/" class="text-sm text-gray-400 hover:text-gray-600">&larr; Back to search</NuxtLink>
        <div class="font-bold text-lg text-gray-900 dark:text-white mt-1">Admin</div>
      </div>
      <nav class="flex-1 overflow-y-auto p-3 space-y-1">
        <NuxtLink
          v-for="link in visibleLinks"
          :key="link.to"
          :to="link.to"
          class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          active-class="bg-gray-100 dark:bg-gray-800"
        >
          <UIcon :name="link.icon" class="w-4 h-4" />
          {{ link.label }}
        </NuxtLink>
      </nav>
      <div class="p-3 border-t border-gray-200 dark:border-gray-800">
        <div class="text-xs text-gray-400 px-3 mb-2 truncate">{{ authStore.user?.username }}</div>
        <UButton variant="ghost" color="neutral" size="sm" block @click="logout">Sign out</UButton>
      </div>
    </aside>
    <main class="flex-1 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
