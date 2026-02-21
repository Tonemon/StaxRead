<script setup lang="ts">
definePageMeta({ middleware: "auth" })
const { $api } = useNuxtApp()

interface Category {
  id: string
  name: string
}

interface BookmarkItem {
  id: string
  chunk: string
  category: string | null
  note: string
  created_at: string
}

const { data: categories, refresh: refreshCategories } = await useFetch<Category[]>("/bookmark-categories/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as Category[],
})

const { data: bookmarks, refresh: refreshBookmarks } = await useFetch<BookmarkItem[]>("/bookmarks/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as BookmarkItem[],
})

function bookmarksByCategory(categoryId: string | null) {
  return (bookmarks.value || []).filter((b) => b.category === categoryId)
}

const uncategorized = computed(() => bookmarksByCategory(null))

async function deleteBookmark(id: string) {
  await ($api as typeof $fetch)(`/bookmarks/${id}/`, { method: "DELETE" })
  refreshBookmarks()
}

// New category modal
const showNewCategory = ref(false)
const newCategoryName = ref("")

async function createCategory() {
  if (!newCategoryName.value.trim()) return
  await ($api as typeof $fetch)("/bookmark-categories/", {
    method: "POST",
    body: { name: newCategoryName.value.trim() },
  })
  newCategoryName.value = ""
  showNewCategory.value = false
  refreshCategories()
}

async function deleteCategory(id: string) {
  await ($api as typeof $fetch)(`/bookmark-categories/${id}/`, { method: "DELETE" })
  refreshCategories()
  refreshBookmarks()
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Bookmarks</h1>
      <UButton size="sm" @click="showNewCategory = true" icon="i-heroicons-plus">New Category</UButton>
    </div>

    <UModal v-model:open="showNewCategory" title="New Category">
      <template #body>
        <UInput v-model="newCategoryName" placeholder="Category name" autofocus />
      </template>
      <template #footer>
        <UButton @click="createCategory">Create</UButton>
        <UButton variant="ghost" @click="showNewCategory = false">Cancel</UButton>
      </template>
    </UModal>

    <!-- Uncategorized -->
    <div v-if="uncategorized.length" class="mb-6">
      <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Uncategorized</h2>
      <div class="space-y-2">
        <div
          v-for="bm in uncategorized"
          :key="bm.id"
          class="flex items-start justify-between gap-2 p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
        >
          <div>
            <p class="text-sm text-gray-700 dark:text-gray-300">Chunk: {{ bm.chunk }}</p>
            <p v-if="bm.note" class="text-xs text-gray-400 mt-1">{{ bm.note }}</p>
          </div>
          <UButton size="xs" variant="ghost" color="error" icon="i-heroicons-trash" @click="deleteBookmark(bm.id)" />
        </div>
      </div>
    </div>

    <!-- By category -->
    <div v-for="cat in categories" :key="cat.id" class="mb-6">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">{{ cat.name }}</h2>
        <UButton size="xs" variant="ghost" color="error" icon="i-heroicons-trash" @click="deleteCategory(cat.id)" />
      </div>
      <div v-if="bookmarksByCategory(cat.id).length" class="space-y-2">
        <div
          v-for="bm in bookmarksByCategory(cat.id)"
          :key="bm.id"
          class="flex items-start justify-between gap-2 p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
        >
          <div>
            <p class="text-sm text-gray-700 dark:text-gray-300">Chunk: {{ bm.chunk }}</p>
            <p v-if="bm.note" class="text-xs text-gray-400 mt-1">{{ bm.note }}</p>
          </div>
          <UButton size="xs" variant="ghost" color="error" icon="i-heroicons-trash" @click="deleteBookmark(bm.id)" />
        </div>
      </div>
      <p v-else class="text-sm text-gray-400">No bookmarks in this category.</p>
    </div>

    <p v-if="!bookmarks?.length && !categories?.length" class="text-gray-400 text-center mt-16">
      No bookmarks yet. Bookmark search results to see them here.
    </p>
  </div>
</template>
