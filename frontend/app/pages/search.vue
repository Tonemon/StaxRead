<script setup lang="ts">
definePageMeta({ middleware: "auth" })
const route = useRoute()
const store = useSearchStore()
const { $api } = useNuxtApp()

const query = ref((route.query.q as string) || "")
const loading = ref(false)
const error = ref("")

async function runSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = ""
  try {
    const data = await ($api as typeof $fetch)<{ results: typeof store.results; query: string }>(
      "/search/",
      {
        method: "POST",
        body: { query: query.value, kb_ids: store.activeKbIds },
      }
    )
    store.results = data.results
    store.lastQuery = query.value
  } catch {
    error.value = "Search failed. Please try again."
  } finally {
    loading.value = false
  }
}

if (query.value) runSearch()
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="border-b border-gray-200 dark:border-gray-800 p-4 bg-white dark:bg-gray-900">
      <UInput
        v-model="query"
        size="lg"
        placeholder="Search..."
        icon="i-heroicons-magnifying-glass"
        :loading="loading"
        @keydown.enter="runSearch"
      />
    </div>
    <div class="flex-1 overflow-y-auto p-4 space-y-3">
      <UAlert v-if="error" color="error" :description="error" />
      <p v-else-if="!store.results.length && !loading" class="text-gray-400 text-center mt-16">
        No results yet. Enter a query above.
      </p>
      <ResultCard
        v-for="result in store.results"
        :key="result.chunk_id"
        :result="result"
        :query="store.lastQuery"
      />
    </div>
  </div>
</template>
