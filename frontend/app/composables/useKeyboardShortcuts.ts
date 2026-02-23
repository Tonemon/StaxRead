import type { Router } from '#vue-router'

const _refreshFn = ref<(() => void) | null>(null)
const _focusSearchFlag = ref(false)
const _showHelp = ref(false)
let _router: Router | null = null

function isInInput(e: KeyboardEvent): boolean {
  const t = e.target as HTMLElement
  return t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || !!t.isContentEditable
}

function onKeydown(e: KeyboardEvent) {
  if (e.ctrlKey && !e.altKey && e.key === 'r') {
    e.preventDefault()
    _refreshFn.value?.()
    return
  }
  if (e.ctrlKey && !e.altKey && e.key === ' ') {
    e.preventDefault()
    _focusSearchFlag.value = true
    if (_router?.currentRoute.value.path !== '/') {
      _router?.push('/')
    }
    return
  }
  if (e.ctrlKey && !e.altKey && e.key === 'k') {
    e.preventDefault()
    _router?.push('/admin/knowledge-bases')
    return
  }
  if (e.ctrlKey && !e.altKey && e.key === 'b') {
    e.preventDefault()
    _router?.push('/bookmarks')
    return
  }
  if (e.key === '?' && !e.ctrlKey && !e.altKey && !isInInput(e)) {
    _showHelp.value = !_showHelp.value
    return
  }
}

export function useKeyboardShortcuts() {
  const router = useRouter()
  _router = router

  function setup() {
    window.addEventListener('keydown', onKeydown)
  }

  function teardown() {
    window.removeEventListener('keydown', onKeydown)
  }

  function setRefresh(fn: () => void) {
    _refreshFn.value = fn
  }

  function clearRefresh() {
    _refreshFn.value = null
  }

  return {
    setup,
    teardown,
    setRefresh,
    clearRefresh,
    focusSearchFlag: _focusSearchFlag,
    showHelp: _showHelp,
  }
}
