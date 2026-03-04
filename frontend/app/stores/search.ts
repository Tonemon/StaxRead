import { defineStore } from 'pinia'

export interface ContextChunk {
  chunk_id: string
  text: string
  metadata: Record<string, unknown>
}

export interface SearchResult {
  chunk_id: string
  text: string
  relevance_score: number
  source_title: string
  source_id: string
  kb_id: string
  kb_name: string
  metadata: Record<string, unknown>
  context_before: ContextChunk[]
  context_after: ContextChunk[]
}

export const useSearchStore = defineStore('search', () => {
  // null = all KBs active (default); [] = explicitly none; [...] = specific subset
  // Uses v2 key to avoid conflicts with old [] default stored in localStorage
  const activeKbIds = useLocalStorage<string[] | null>('staxread_active_kb_ids_v2', null, {
    serializer: {
      read: (v: string) => {
        if (!v || v === 'null') return null
        try { return JSON.parse(v) as string[] } catch { return null }
      },
      write: (v: string[] | null) => JSON.stringify(v),
    },
  })
  const lastQuery = ref('')
  const results = ref<SearchResult[]>([])

  const noKbsSelected = computed(
    () => activeKbIds.value !== null && activeKbIds.value.length === 0,
  )

  // kb_ids to send to the backend: null → [] (backend treats as "all accessible")
  const searchKbIds = computed(() => [...new Set(activeKbIds.value ?? [])])

  return { activeKbIds, results, lastQuery, noKbsSelected, searchKbIds }
})
