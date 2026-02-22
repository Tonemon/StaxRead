<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const router = useRouter()
const store = useSearchStore()
const { $api } = useNuxtApp()

const query = ref('')
const loading = ref(false)

interface HistoryItem {
  id: string
  query: string
  created_at: string
}

const { data: history } = await useFetch<HistoryItem[]>('/search/history/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as HistoryItem[],
})

async function search() {
  if (!query.value.trim() || loading.value) return
  loading.value = true
  try {
    const data = await ($api as typeof $fetch)<{ results: typeof store.results; query: string }>(
      '/search/',
      { method: 'POST', body: { query: query.value, kb_ids: store.activeKbIds } }
    )
    store.results = data.results
    store.lastQuery = query.value
    await router.push({ path: '/search', query: { q: query.value } })
  } catch {
    loading.value = false
  }
}

const recentSearches = computed(() => (history.value || []).slice(0, 7))
</script>

<template>
  <UDashboardPanel id="home" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col justify-center gap-4 sm:gap-6 py-8">
        <h1 class="text-3xl sm:text-4xl text-highlighted font-bold">
          What are you looking for?
        </h1>

        <UChatPrompt
          v-model="query"
          :status="loading ? 'streaming' : 'ready'"
          variant="subtle"
          placeholder="Search your knowledge bases..."
          :ui="{ base: 'px-1.5' }"
          @submit="search"
        >
          <template #footer>
            <UChatPromptSubmit
              color="neutral"
              size="sm"
              icon="i-lucide-search"
              :disabled="loading"
            />
          </template>
        </UChatPrompt>

        <div v-if="recentSearches.length" class="flex flex-wrap gap-2">
          <UButton
            v-for="item in recentSearches"
            :key="item.id"
            :label="item.query"
            icon="i-lucide-history"
            size="sm"
            color="neutral"
            variant="outline"
            class="rounded-full"
            @click="query = item.query; search()"
          />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
