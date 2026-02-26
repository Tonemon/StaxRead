import { defineStore } from 'pinia'

export interface SearchResult {
  chunk_id: string
  text: string
  relevance_score: number
  source_title: string
  source_id: string
  kb_id: string
  kb_name: string
  metadata: Record<string, unknown>
}

export const useSearchStore = defineStore('search', () => {
  // null = all KBs active (default); [] = explicitly none; [...] = specific subset
  // Uses v2 key to avoid conflicts with old [] default stored in localStorage
  const activeKbIds = useLocalStorage<string[] | null>('staxread_active_kb_ids_v2', null)
  const lastQuery = ref('')
  const results = ref<SearchResult[]>([])

  const noKbsSelected = computed(
    () => activeKbIds.value !== null && activeKbIds.value.length === 0,
  )

  // kb_ids to send to the backend: null → [] (backend treats as "all accessible")
  const searchKbIds = computed(() => activeKbIds.value ?? [])

  return { activeKbIds, results, lastQuery, noKbsSelected, searchKbIds }
})
