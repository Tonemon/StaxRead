<script setup lang="ts">
const props = defineProps<{ chunkId: string }>()
const { $api } = useNuxtApp()
const searchStore = useSearchStore()
const isOpen = ref(false)
const note = ref("")
const selectedCategory = ref("none")
const saveError = ref("")

interface Category { id: string; name: string }

const categories = ref<Category[]>([])
const categoriesLoaded = ref(false)

async function loadCategories() {
  if (categoriesLoaded.value) return
  categories.value = await ($api as typeof $fetch)<Category[]>("/bookmark-categories/")
  categoriesLoaded.value = true
}

watch(isOpen, (val) => { if (val) loadCategories() })

const categoryItems = computed(() => [
  { label: "No category", value: "none" },
  ...categories.value.map(c => ({ label: c.name, value: c.id })),
])

async function addBookmark() {
  saveError.value = ""
  try {
    await ($api as typeof $fetch)("/bookmarks/", {
      method: "POST",
      body: {
        chunk: props.chunkId,
        category: selectedCategory.value === "none" ? undefined : selectedCategory.value,
        note: note.value,
        query: searchStore.lastQuery,
      },
    })
    isOpen.value = false
    note.value = ""
    selectedCategory.value = "none"
  } catch {
    saveError.value = "Failed to save bookmark"
  }
}
</script>

<template>
  <UPopover v-model:open="isOpen">
    <UButton
      icon="i-heroicons-bookmark"
      size="xs"
      variant="ghost"
      color="neutral"
      aria-label="Bookmark"
    />
    <template #content>
      <div class="p-3 w-56 space-y-3">
        <p class="text-sm font-medium">Add bookmark</p>
        <USelectMenu
          v-model="selectedCategory"
          :items="categoryItems"
          value-key="value"
          size="sm"
          placeholder="Category (optional)"
          class="w-full"
        />
        <UTextarea v-model="note" placeholder="Note (optional)" size="sm" :rows="2" />
        <UAlert v-if="saveError" color="error" :description="saveError" />
        <UButton size="sm" block @click="addBookmark">Save</UButton>
      </div>
    </template>
  </UPopover>
</template>
