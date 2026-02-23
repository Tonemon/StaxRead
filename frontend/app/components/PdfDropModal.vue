<script setup lang="ts">
const { pendingFiles, clearPending } = usePdfDrop()
const { $api } = useNuxtApp()

interface KB { id: string; name: string }
interface UploadEntry { file: File; title: string; status: 'pending' | 'uploading' | 'done' | 'error' }

const kbs = ref<KB[]>([])
const kbsLoaded = ref(false)
const selectedKbId = ref('')
const entries = ref<UploadEntry[]>([])
const uploading = ref(false)

const open = computed(() => pendingFiles.value.length > 0)

const kbItems = computed(() => kbs.value.map(kb => ({ label: kb.name, value: kb.id })))

const allSettled = computed(() =>
  entries.value.length > 0 && entries.value.every(e => e.status === 'done' || e.status === 'error'),
)

function stemFromFilename(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot > 0 ? filename.substring(0, dot) : filename
}

async function loadKbs() {
  if (kbsLoaded.value) return
  kbs.value = await ($api as typeof $fetch)<KB[]>('/knowledge-bases/')
  kbsLoaded.value = true
}

watch(open, async (val) => {
  if (!val) return
  await loadKbs()
  entries.value = pendingFiles.value.map(f => ({
    file: f,
    title: stemFromFilename(f.name),
    status: 'pending',
  }))
})

async function upload() {
  if (!selectedKbId.value) return
  uploading.value = true
  for (const entry of entries.value) {
    entry.status = 'uploading'
    try {
      const fd = new FormData()
      fd.append('kb', selectedKbId.value)
      fd.append('title', entry.title || stemFromFilename(entry.file.name))
      fd.append('source_type', 'pdf')
      fd.append('file', entry.file)
      await ($api as typeof $fetch)('/sources/', { method: 'POST', body: fd })
      entry.status = 'done'
    } catch {
      entry.status = 'error'
    }
  }
  uploading.value = false
}

function close() {
  clearPending()
  entries.value = []
  selectedKbId.value = ''
}

function onModalUpdate(open: boolean) {
  if (!open) close()
}

const statusIcon: Record<string, string> = {
  pending: 'i-lucide-file',
  uploading: 'i-lucide-loader-circle',
  done: 'i-lucide-circle-check',
  error: 'i-lucide-circle-x',
}

const statusColor: Record<string, string> = {
  pending: 'text-dimmed',
  uploading: 'text-primary animate-spin',
  done: 'text-success',
  error: 'text-error',
}
</script>

<template>
  <UModal :open="open" title="Upload PDF to Knowledge Base" :ui="{ width: 'sm:max-w-lg' }" @update:open="onModalUpdate">
    <template #body>
      <div class="space-y-4">
        <UFormField label="Knowledge Base">
          <USelectMenu
            v-model="selectedKbId"
            :items="kbItems"
            value-key="value"
            placeholder="Select a knowledge base"
            class="w-full"
          />
        </UFormField>

        <div class="space-y-2">
          <p class="text-sm font-medium text-default">Files ({{ entries.length }})</p>
          <div
            v-for="(entry, i) in entries"
            :key="i"
            class="flex items-center gap-3 p-2.5 rounded-lg bg-elevated"
          >
            <UIcon
              :name="statusIcon[entry.status]"
              :class="['size-4 shrink-0', statusColor[entry.status]]"
            />
            <UInput
              v-model="entries[i].title"
              size="sm"
              class="flex-1 min-w-0"
              :disabled="entry.status !== 'pending'"
            />
            <span class="text-xs text-dimmed shrink-0">{{ entry.file.name.split('.').pop()?.toUpperCase() }}</span>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <UButton
        v-if="!allSettled"
        :loading="uploading"
        :disabled="!selectedKbId || uploading"
        @click="upload"
      >
        Upload {{ entries.length > 1 ? `${entries.length} files` : 'file' }}
      </UButton>
      <UButton
        v-if="allSettled"
        color="neutral"
        @click="close"
      >
        Done
      </UButton>
      <UButton
        v-if="!allSettled"
        color="neutral"
        variant="ghost"
        :disabled="uploading"
        @click="close"
      >
        Cancel
      </UButton>
    </template>
  </UModal>
</template>
