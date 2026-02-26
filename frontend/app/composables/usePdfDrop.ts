// Module-level singleton — drag state is purely client-side and shared globally
let dragCounter = 0

const isDragging = ref(false)
const pendingFiles = ref<File[]>([])
const suppressGlobal = ref(false)
const dropLabel = ref<string | null>(null)

const ACCEPTED_TYPES = ['application/pdf', 'application/epub+zip']

function hasDocItem(e: DragEvent): boolean {
  const items = e.dataTransfer?.items
  if (items) {
    return Array.from(items).some(i => i.kind === 'file' && ACCEPTED_TYPES.includes(i.type))
  }
  return e.dataTransfer?.types.includes('Files') ?? false
}

function onDragEnter(e: DragEvent) {
  if (!hasDocItem(e)) return
  dragCounter++
  isDragging.value = true
}

function onDragLeave() {
  if (--dragCounter <= 0) {
    dragCounter = 0
    isDragging.value = false
  }
}

function onDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('Files')) e.preventDefault()
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragCounter = 0
  isDragging.value = false

  if (suppressGlobal.value) return

  const files = Array.from(e.dataTransfer?.files ?? []).filter(
    f => ACCEPTED_TYPES.includes(f.type),
  )
  if (files.length) pendingFiles.value = files
}

export function usePdfDrop() {
  function setup() {
    window.addEventListener('dragenter', onDragEnter)
    window.addEventListener('dragleave', onDragLeave)
    window.addEventListener('dragover', onDragOver)
    window.addEventListener('drop', onDrop)
  }

  function teardown() {
    window.removeEventListener('dragenter', onDragEnter)
    window.removeEventListener('dragleave', onDragLeave)
    window.removeEventListener('dragover', onDragOver)
    window.removeEventListener('drop', onDrop)
  }

  function clearPending() {
    pendingFiles.value = []
  }

  return { isDragging, pendingFiles, suppressGlobal, dropLabel, setup, teardown, clearPending }
}
