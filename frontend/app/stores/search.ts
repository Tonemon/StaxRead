import { defineStore } from "pinia"

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

export const useSearchStore = defineStore("search", {
  state: () => ({
    activeKbIds: [] as string[],
    lastQuery: "",
    results: [] as SearchResult[],
  }),
})
