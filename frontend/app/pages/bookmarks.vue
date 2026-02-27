<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { $api } = useNuxtApp()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

interface Category { id: string; name: string }
interface BookmarkItem { id: string; chunk: string; chunk_text: string; chunk_metadata: Record<string, unknown>; source_title: string; source_id: string; category: string | null; note: string; query: string; created_at: string }

const { data: categories, refresh: refreshCategories } = await useFetch<Category[]>('/bookmark-categories/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Category[],
})
const { data: bookmarks, refresh: refreshBookmarks } = await useFetch<BookmarkItem[]>('/bookmarks/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as BookmarkItem[],
})

function bookmarksByCategory(categoryId: string | null) {
  return (bookmarks.value || []).filter(b => b.category === categoryId)
}

const uncategorized = computed(() => bookmarksByCategory(null))

async function deleteBookmark(id: string) {
  await ($api as typeof $fetch)(`/bookmarks/${id}/`, { method: 'DELETE' })
  refreshBookmarks()
}

const showNewCategory = ref(false)
const newCategoryName = ref('')

async function createCategory() {
  if (!newCategoryName.value.trim()) return
  await ($api as typeof $fetch)('/bookmark-categories/', { method: 'POST', body: { name: newCategoryName.value.trim() } })
  newCategoryName.value = ''
  showNewCategory.value = false
  refreshCategories()
}

async function deleteCategory(id: string) {
  await ($api as typeof $fetch)(`/bookmark-categories/${id}/`, { method: 'DELETE' })
  refreshCategories()
  refreshBookmarks()
}

onMounted(() => setRefresh(() => { refreshCategories(); refreshBookmarks() }))
onUnmounted(clearRefresh)
</script>

<template>
  <UDashboardPanel id="bookmarks" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-highlighted">Bookmarks</h1>
          <UButton size="sm" icon="i-lucide-plus" color="neutral" variant="outline" @click="showNewCategory = true">New Category</UButton>
        </div>

        <UModal v-model:open="showNewCategory" title="New Category">
          <template #body>
            <UInput v-model="newCategoryName" placeholder="Category name" autofocus @keydown.enter="createCategory" />
          </template>
          <template #footer>
            <UButton @click="createCategory">Create</UButton>
            <UButton color="neutral" variant="ghost" @click="showNewCategory = false">Cancel</UButton>
          </template>
        </UModal>

        <div v-if="uncategorized.length" class="space-y-2">
          <p class="text-xs font-semibold text-dimmed uppercase tracking-wider">Uncategorized</p>
          <div v-for="bm in uncategorized" :key="bm.id" class="flex items-start justify-between gap-2 p-3 bg-default rounded-lg ring ring-default">
            <div class="min-w-0 flex-1">
              <NuxtLink :to="`/documents/${bm.source_id}?page=${bm.chunk_metadata?.page_number ?? 1}`" class="text-xs font-medium text-dimmed hover:text-default truncate block">{{ bm.source_title }}</NuxtLink>
              <p class="text-sm text-default mt-0.5 line-clamp-3">{{ bm.chunk_text }}</p>
              <NuxtLink v-if="bm.query" :to="`/search?q=${encodeURIComponent(bm.query)}`" class="inline-flex items-center gap-1 mt-1.5 text-xs text-primary hover:underline">
                <UIcon name="i-lucide-search" class="w-3 h-3" />{{ bm.query }}
              </NuxtLink>
              <p v-if="bm.note" class="text-xs text-dimmed mt-1 italic">{{ bm.note }}</p>
            </div>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" class="shrink-0" @click="deleteBookmark(bm.id)" />
          </div>
        </div>

        <div v-for="cat in categories" :key="cat.id" class="space-y-2">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold text-dimmed uppercase tracking-wider">{{ cat.name }}</p>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="deleteCategory(cat.id)" />
          </div>
          <div v-if="bookmarksByCategory(cat.id).length" class="space-y-2">
            <div v-for="bm in bookmarksByCategory(cat.id)" :key="bm.id" class="flex items-start justify-between gap-2 p-3 bg-default rounded-lg ring ring-default">
              <div class="min-w-0 flex-1">
                <NuxtLink :to="`/documents/${bm.source_id}?page=${bm.chunk_metadata?.page_number ?? 1}`" class="text-xs font-medium text-dimmed hover:text-default truncate block">{{ bm.source_title }}</NuxtLink>
                <p class="text-sm text-default mt-0.5 line-clamp-3">{{ bm.chunk_text }}</p>
                <NuxtLink v-if="bm.query" :to="`/search?q=${encodeURIComponent(bm.query)}`" class="inline-flex items-center gap-1 mt-1.5 text-xs text-primary hover:underline">
                  <UIcon name="i-lucide-search" class="w-3 h-3" />{{ bm.query }}
                </NuxtLink>
                <p v-if="bm.note" class="text-xs text-dimmed mt-1 italic">{{ bm.note }}</p>
              </div>
              <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" class="shrink-0" @click="deleteBookmark(bm.id)" />
            </div>
          </div>
          <p v-else class="text-sm text-dimmed">No bookmarks in this category.</p>
        </div>

        <p v-if="!bookmarks?.length && !categories?.length" class="text-dimmed text-center mt-16">
          No bookmarks yet.
        </p>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
