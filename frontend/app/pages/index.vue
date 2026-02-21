<script setup lang="ts">
definePageMeta({ middleware: "auth" })
const router = useRouter()
const { $api } = useNuxtApp()

interface HistoryItem {
  id: string
  query: string
  created_at: string
}

const query = ref("")
const { data: history } = await useFetch<HistoryItem[]>("/search/history/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as HistoryItem[],
})

function search() {
  if (!query.value.trim()) return
  router.push({ path: "/search", query: { q: query.value } })
}
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full min-h-[80vh] p-8">
    <h1 class="text-4xl font-bold mb-8 text-gray-900 dark:text-white">StaxRead</h1>
    <div class="w-full max-w-2xl space-y-3">
      <UInput
        v-model="query"
        size="xl"
        placeholder="Search your knowledge bases..."
        icon="i-heroicons-magnifying-glass"
        @keydown.enter="search"
      />
      <div v-if="history && history.length">
        <p class="text-xs text-gray-400 mb-2 px-1">Recent searches</p>
        <div class="flex flex-wrap gap-2">
          <UBadge
            v-for="item in history.slice(0, 8)"
            :key="item.id"
            variant="subtle"
            color="neutral"
            class="cursor-pointer"
            @click="query = item.query; search()"
          >{{ item.query }}</UBadge>
        </div>
      </div>
    </div>
  </div>
</template>
