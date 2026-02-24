<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string

interface GitCredential { id: string; label: string }
interface FileEntry { file: File; title: string; status: 'pending' | 'uploading' | 'done' | 'error' }

const { data: credentials } = await useFetch<GitCredential[]>('/git-credentials/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as GitCredential[],
})

const fileQueue = ref<FileEntry[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const gitForm = reactive({ title: '', gitUrl: '', gitBranch: 'main', gitCredential: '' })
const submitting = ref(false)
const success = ref('')
const error = ref('')

function stemFromFilename(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot > 0 ? filename.substring(0, dot) : filename
}

const ACCEPTED_FILE_TYPES = ['application/pdf', 'application/epub+zip']

function sourceTypeFromFile(file: File): string {
  return file.type === 'application/epub+zip' ? 'epub' : 'pdf'
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files ?? []).filter(f => ACCEPTED_FILE_TYPES.includes(f.type))
  fileQueue.value = files.map(f => ({
    file: f,
    title: stemFromFilename(f.name),
    status: 'pending',
  }))
}

const allSettled = computed(() =>
  fileQueue.value.length > 0 && fileQueue.value.every(e => e.status === 'done' || e.status === 'error'),
)

const anyPending = computed(() => fileQueue.value.some(e => e.status === 'pending'))

async function submitFiles() {
  if (!fileQueue.value.length) return
  submitting.value = true
  error.value = ''
  success.value = ''

  for (const entry of fileQueue.value) {
    if (entry.status !== 'pending') continue
    entry.status = 'uploading'
    try {
      const fd = new FormData()
      fd.append('kb', kbId)
      fd.append('title', entry.title || stemFromFilename(entry.file.name))
      fd.append('source_type', sourceTypeFromFile(entry.file))
      fd.append('file', entry.file)
      await ($api as typeof $fetch)('/sources/', { method: 'POST', body: fd })
      entry.status = 'done'
    } catch {
      entry.status = 'error'
    }
  }

  submitting.value = false
  if (fileQueue.value.every(e => e.status === 'done')) {
    success.value = `${fileQueue.value.length} file${fileQueue.value.length > 1 ? 's' : ''} uploaded. Ingestion started.`
  }
}

function removeEntry(i: number) {
  fileQueue.value.splice(i, 1)
}

function clearQueue() {
  fileQueue.value = []
  if (fileInputRef.value) fileInputRef.value.value = ''
  success.value = ''
}

async function submitGit() {
  if (!gitForm.title || !gitForm.gitUrl) return
  submitting.value = true
  error.value = ''
  success.value = ''
  try {
    const body: Record<string, string> = {
      kb: kbId,
      title: gitForm.title,
      source_type: 'git',
      git_url: gitForm.gitUrl,
      git_branch: gitForm.gitBranch,
    }
    if (gitForm.gitCredential) body.git_credential = gitForm.gitCredential
    await ($api as typeof $fetch)('/sources/', { method: 'POST', body })
    success.value = 'Git source added. Ingestion started.'
    gitForm.title = ''
    gitForm.gitUrl = ''
  } catch {
    error.value = 'Failed to add git source.'
  } finally {
    submitting.value = false
  }
}

const credentialItems = computed(() => [
  { label: 'None (public repo)', value: '' },
  ...(credentials.value || []).map(c => ({ label: c.label, value: c.id })),
])

const tabs = [
  { label: 'Upload PDF', slot: 'file' as const },
  { label: 'Git Repository', slot: 'git' as const },
]

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
  <UDashboardPanel id="sources" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <div class="flex flex-1">
        <UContainer class="flex-1 flex flex-col gap-4 py-6 max-w-2xl">
          <div>
            <NuxtLink :to="`/settings/knowledge-bases/${kbId}`" class="text-sm text-dimmed hover:text-default">&larr; Back</NuxtLink>
            <h1 class="text-2xl font-bold text-highlighted mt-2">Add Source</h1>
          </div>

          <UAlert v-if="success" color="success" :description="success" />
          <UAlert v-if="error" color="error" :description="error" />

          <UTabs :items="tabs">
            <template #file>
              <div class="space-y-4 pt-4">
                <UFormField label="Files" hint="Select one or more PDFs or EPUBs">
                  <input
                    ref="fileInputRef"
                    type="file"
                    accept=".pdf,.epub"
                    multiple
                    class="text-sm text-default file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-elevated file:text-default hover:file:bg-accented cursor-pointer"
                    @change="onFileChange"
                  />
                </UFormField>

                <div v-if="fileQueue.length" class="space-y-2">
                  <div
                    v-for="(entry, i) in fileQueue"
                    :key="i"
                    class="flex items-center gap-3 p-2.5 rounded-lg bg-elevated"
                  >
                    <UIcon
                      :name="statusIcon[entry.status]"
                      :class="['size-4 shrink-0', statusColor[entry.status]]"
                    />
                    <UInput
                      v-model="fileQueue[i].title"
                      size="sm"
                      class="flex-1 min-w-0"
                      :disabled="entry.status !== 'pending'"
                      placeholder="Title"
                    />
                    <UButton
                      v-if="entry.status === 'pending'"
                      icon="i-lucide-x"
                      size="xs"
                      color="neutral"
                      variant="ghost"
                      @click="removeEntry(i)"
                    />
                  </div>
                </div>

                <div class="flex gap-2">
                  <UButton
                    :loading="submitting"
                    :disabled="!anyPending || submitting"
                    @click="submitFiles"
                  >
                    Upload {{ fileQueue.length > 1 ? `${fileQueue.length} files` : 'file' }}
                  </UButton>
                  <UButton
                    v-if="allSettled"
                    color="neutral"
                    variant="outline"
                    @click="clearQueue"
                  >
                    Clear
                  </UButton>
                </div>
              </div>
            </template>

            <template #git>
              <div class="space-y-4 pt-4">
                <UFormField label="Title">
                  <UInput v-model="gitForm.title" placeholder="e.g. My Project Docs" class="w-full" />
                </UFormField>
                <UFormField label="Repository URL">
                  <UInput v-model="gitForm.gitUrl" placeholder="https://github.com/user/repo" class="w-full" @keydown.enter="submitGit" />
                </UFormField>
                <UFormField label="Branch">
                  <UInput v-model="gitForm.gitBranch" class="w-full" @keydown.enter="submitGit" />
                </UFormField>
                <UFormField label="Git Credential (optional)">
                  <USelectMenu
                    v-model="gitForm.gitCredential"
                    :items="credentialItems"
                    value-key="value"
                    class="w-full"
                  />
                </UFormField>
                <UButton :loading="submitting" :disabled="!gitForm.title || !gitForm.gitUrl" @click="submitGit">
                  Add &amp; Ingest
                </UButton>
              </div>
            </template>
          </UTabs>
        </UContainer>
      </div>
    </template>
  </UDashboardPanel>
</template>
