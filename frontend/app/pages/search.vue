<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const route = useRoute()
const router = useRouter()
const store = useSearchStore()
const { $api } = useNuxtApp()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

const query = ref((route.query.q as string) || '')
const loading = ref(false)
const error = ref('')

async function runSearch() {
  if (!query.value.trim()) return
  if (store.noKbsSelected) {
    error.value = 'Please select a knowledge base to search.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await ($api as typeof $fetch)<{ results: typeof store.results; query: string }>(
      '/search/',
      { method: 'POST', body: { query: query.value, kb_ids: store.searchKbIds } }
    )
    store.results = data.results
    store.lastQuery = query.value
  } catch {
    error.value = 'Search failed. Please try again.'
  } finally {
    loading.value = false
  }
}

if (query.value) runSearch()

onMounted(() => setRefresh(runSearch))
onUnmounted(clearRefresh)
</script>

<template>
  <UDashboardPanel id="search" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <div class="flex flex-1">
        <UContainer class="flex-1 flex flex-col gap-4 sm:gap-6 py-6">
          <UChatPrompt
            v-model="query"
            :status="loading ? 'streaming' : 'ready'"
            variant="subtle"
            placeholder="Search..."
            :ui="{ base: 'px-1.5' }"
            @submit="runSearch"
          >
            <template #footer>
              <div />
              <UChatPromptSubmit color="neutral" size="sm" :disabled="loading" />
            </template>
          </UChatPrompt>

          <UAlert v-if="error" color="error" :description="error" />

          <p v-if="!store.results.length && !loading && !error" class="text-dimmed text-center mt-8">
            No results yet. Enter a query above.
          </p>

          <div class="space-y-3">
            <ResultCard
              v-for="result in store.results"
              :key="result.chunk_id"
              :result="result"
              :query="store.lastQuery"
            />
          </div>
        </UContainer>
      </div>
    </template>
  </UDashboardPanel>
</template>
