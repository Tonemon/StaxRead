<script setup lang="ts">
import type { SearchResult } from '~/stores/search'

const props = defineProps<{
  result: SearchResult
  query: string
}>()

const highlightedText = computed(() => {
  const text = props.result.text
  if (!props.query) return text
  const words = props.query.trim().split(/\s+/)
    .map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .filter(w => w.length >= 2)
  if (!words.length) return text
  const pattern = new RegExp(`(${words.join('|')})`, 'gi')
  return text.replace(pattern, '<mark class="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">$1</mark>')
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
            class="font-medium text-sm hover:underline text-highlighted truncate block"
          >
            {{ result.source_title }}
          </NuxtLink>
          <p class="text-xs text-dimmed mt-0.5">{{ result.kb_name }}</p>
        </div>
        <div class="shrink-0 flex items-center gap-2">
          <UBadge color="success" variant="subtle" size="xs">{{ scorePercent }}% relevance</UBadge>
        </div>
      </div>
    </template>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <p class="text-sm leading-relaxed text-default" v-html="highlightedText" />
  </UCard>
</template>
