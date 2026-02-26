// Singleton refresh trigger so any page can tell the sidebar to re-fetch KBs
let _refreshFn: (() => void) | null = null

export function useKbList() {
  function registerRefresh(fn: () => void) {
    _refreshFn = fn
  }

  function refreshKbList() {
    _refreshFn?.()
  }

  return { registerRefresh, refreshKbList }
}
