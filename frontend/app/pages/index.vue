<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const router = useRouter()
const store = useSearchStore()
const { $api } = useNuxtApp()

const query = ref('')
const loading = ref(false)

interface BookmarkItem { id: string; chunk: string; chunk_text: string; query: string; note: string; category: string | null; created_at: string }

const { data: bookmarks } = await useFetch<BookmarkItem[]>('/bookmarks/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as BookmarkItem[],
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

const suggestionBookmarks = computed(() => (bookmarks.value || []).slice(0, 7))

function bookmarkLabel(item: BookmarkItem) {
  const text = item.query || item.note || item.chunk_text
  return text.length > 45 ? text.slice(0, 42) + '…' : text
}

function bookmarkQuery(item: BookmarkItem) {
  return item.query || item.chunk_text
}
</script>

<template>
  <UDashboardPanel id="home" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>

    <template #body>
      <div class="flex flex-1">
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
              <div />
              <UChatPromptSubmit color="neutral" size="sm" :disabled="loading" />
            </template>
          </UChatPrompt>

          <div v-if="suggestionBookmarks.length" class="flex flex-wrap gap-2">
            <UButton
              v-for="item in suggestionBookmarks"
              :key="item.id"
              :label="bookmarkLabel(item)"
              icon="i-lucide-bookmark"
              size="sm"
              color="neutral"
              variant="outline"
              class="rounded-full"
              @click="query = bookmarkQuery(item); search()"
            />
          </div>
        </UContainer>
      </div>
    </template>
  </UDashboardPanel>
</template>
