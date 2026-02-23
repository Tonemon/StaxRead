<script setup lang="ts">
const props = defineProps<{ chunkId: string }>()
const { $api } = useNuxtApp()
const isOpen = ref(false)
const note = ref("")
const selectedCategory = ref("")

interface Category {
  id: string
  name: string
}

const { data: categories } = await useFetch<Category[]>("/bookmark-categories/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as Category[],
})

const categoryItems = computed(() => [
  { label: "No category", value: "" },
  ...(categories.value || []).map(c => ({ label: c.name, value: c.id })),
])

async function addBookmark() {
  await ($api as typeof $fetch)("/bookmarks/", {
    method: "POST",
    body: {
      chunk: props.chunkId,
      category: selectedCategory.value || undefined,
      note: note.value,
    },
  })
  isOpen.value = false
  note.value = ""
  selectedCategory.value = ""
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
        <USelect
          v-model="selectedCategory"
          :items="categoryItems"
          size="sm"
          placeholder="Category (optional)"
        />
        <UTextarea v-model="note" placeholder="Note (optional)" size="sm" :rows="2" />
        <UButton size="sm" block @click="addBookmark">Save</UButton>
      </div>
    </template>
  </UPopover>
</template>
