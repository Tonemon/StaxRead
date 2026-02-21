<script setup lang="ts">
import type { SearchResult } from "~/stores/search"

const props = defineProps<{
  result: SearchResult
  query: string
}>()

const highlightedText = computed(() => {
  if (!props.query) return props.result.text
  const escaped = props.query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  return props.result.text.replace(
    new RegExp(`(${escaped})`, "gi"),
    '<mark class="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">$1</mark>'
  )
})

const scorePercent = computed(() => Math.round(props.result.relevance_score * 100))
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <NuxtLink
            :to="`/documents/${result.source_id}`"
            class="font-medium text-sm hover:underline text-gray-900 dark:text-white truncate block"
          >
            {{ result.source_title }}
          </NuxtLink>
          <p class="text-xs text-gray-400 mt-0.5">{{ result.kb_name }}</p>
        </div>
        <div class="shrink-0 flex items-center gap-2">
          <UBadge color="success" variant="subtle" size="xs">{{ scorePercent }}% relevance</UBadge>
          <BookmarkButton :chunk-id="result.chunk_id" />
        </div>
      </div>
    </template>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <p class="text-sm leading-relaxed text-gray-700 dark:text-gray-300" v-html="highlightedText" />
  </UCard>
</template>
