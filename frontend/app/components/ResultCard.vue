<script setup lang="ts">
import type { SearchResult, ContextChunk } from '~/stores/search'

const props = defineProps<{
  result: SearchResult
  query: string
}>()

const visibleBefore = ref(0)
const visibleAfter = ref(0)

// context_before[0] is the immediately preceding chunk; display furthest-first above the main chunk
const shownBefore = computed(() =>
  props.result.context_before.slice(0, visibleBefore.value).toReversed()
)
const shownAfter = computed(() =>
  props.result.context_after.slice(0, visibleAfter.value)
)

const canExpandBefore = computed(() => visibleBefore.value < props.result.context_before.length)
const canExpandAfter = computed(() => visibleAfter.value < props.result.context_after.length)

function highlight(text: string): string {
  if (!props.query) return text
  const words = props.query.trim().split(/\s+/)
    .map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .filter(w => w.length >= 2)
  if (!words.length) return text
  const pattern = new RegExp(`(${words.join('|')})`, 'gi')
  return text.replace(pattern, '<mark class="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">$1</mark>')
}

const highlightedText = computed(() => highlight(props.result.text))
const scorePercent = computed(() => Math.round(props.result.relevance_score * 100))
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <NuxtLink
            :to="`/documents/${result.source_id}?page=${result.metadata?.page_number ?? 1}`"
            class="font-medium text-sm hover:underline text-highlighted truncate block"
          >
            {{ result.source_title }}
          </NuxtLink>
          <p class="text-xs text-dimmed mt-0.5">{{ result.kb_name }}</p>
        </div>
        <div class="shrink-0 flex items-center gap-2">
          <UBadge color="success" variant="subtle" size="xs">{{ scorePercent }}% relevance</UBadge>
          <BookmarkButton :chunk-id="result.chunk_id" />
        </div>
      </div>
    </template>

    <div>
      <!-- Expand before -->
      <div v-if="canExpandBefore" class="mb-2">
        <button
          class="text-xs text-dimmed hover:text-default transition-colors"
          @click="visibleBefore++"
        >
          ↑ Show more before
        </button>
      </div>

      <!-- Context before (furthest first, closest adjacent to main chunk) -->
      <template v-for="(ctx, i) in shownBefore" :key="ctx.chunk_id">
        <div class="pl-3 border-l-2 border-elevated mb-2">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <p class="text-xs leading-relaxed text-muted" v-html="highlight(ctx.text)" />
        </div>
      </template>

      <div v-if="shownBefore.length" class="border-t border-default mb-3" />

      <!-- Main chunk -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <p class="text-sm leading-relaxed text-default" v-html="highlightedText" />

      <div v-if="shownAfter.length" class="border-t border-default mt-3" />

      <!-- Context after -->
      <template v-for="ctx in shownAfter" :key="ctx.chunk_id">
        <div class="pl-3 border-l-2 border-elevated mt-2">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <p class="text-xs leading-relaxed text-muted" v-html="highlight(ctx.text)" />
        </div>
      </template>

      <!-- Expand after -->
      <div v-if="canExpandAfter" class="mt-2">
        <button
          class="text-xs text-dimmed hover:text-default transition-colors"
          @click="visibleAfter++"
        >
          ↓ Show more after
        </button>
      </div>
    </div>
  </UCard>
</template>
