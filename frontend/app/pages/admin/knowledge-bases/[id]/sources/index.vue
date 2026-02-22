<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string

interface GitCredential { id: string; label: string }

const { data: credentials } = await useFetch<GitCredential[]>('/git-credentials/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as GitCredential[],
})

const fileForm = reactive({ title: '', sourceType: 'pdf', file: null as File | null })
const gitForm = reactive({ title: '', gitUrl: '', gitBranch: 'main', gitCredential: '' })
const submitting = ref(false)
const success = ref('')
const error = ref('')

async function submitFile() {
  if (!fileForm.file || !fileForm.title) return
  submitting.value = true
  error.value = ''
  success.value = ''
  try {
    const fd = new FormData()
    fd.append('kb', kbId)
    fd.append('title', fileForm.title)
    fd.append('source_type', fileForm.sourceType)
    fd.append('file', fileForm.file)
    await ($api as typeof $fetch)('/sources/', { method: 'POST', body: fd })
    success.value = 'Source added. Ingestion started.'
    fileForm.title = ''
    fileForm.file = null
  } catch {
    error.value = 'Failed to add source.'
  } finally {
    submitting.value = false
  }
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

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  fileForm.file = input.files?.[0] ?? null
}

const credentialItems = computed(() => [
  { label: 'None (public repo)', value: '' },
  ...(credentials.value || []).map(c => ({ label: c.label, value: c.id })),
])

const tabs = [
  { label: 'Upload File', slot: 'file' as const },
  { label: 'Git Repository', slot: 'git' as const },
]
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
            <NuxtLink :to="`/admin/knowledge-bases/${kbId}`" class="text-sm text-dimmed hover:text-default">&larr; Back</NuxtLink>
            <h1 class="text-2xl font-bold text-highlighted mt-2">Add Source</h1>
          </div>

          <UAlert v-if="success" color="success" :description="success" />
          <UAlert v-if="error" color="error" :description="error" />

          <UTabs :items="tabs">
            <template #file>
              <div class="space-y-4 pt-4">
                <UFormField label="Title">
                  <UInput v-model="fileForm.title" placeholder="e.g. Annual Report 2024" class="w-full" />
                </UFormField>
                <UFormField label="Type">
                  <USelectMenu v-model="fileForm.sourceType" :items="['pdf', 'epub']" class="w-full" />
                </UFormField>
                <UFormField label="File">
                  <input
                    type="file"
                    :accept="fileForm.sourceType === 'pdf' ? '.pdf' : '.epub'"
                    class="text-sm text-default file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-elevated file:text-default hover:file:bg-accented cursor-pointer"
                    @change="onFileChange"
                  />
                </UFormField>
                <UButton :loading="submitting" :disabled="!fileForm.file || !fileForm.title" @click="submitFile">
                  Upload &amp; Ingest
                </UButton>
              </div>
            </template>

            <template #git>
              <div class="space-y-4 pt-4">
                <UFormField label="Title">
                  <UInput v-model="gitForm.title" placeholder="e.g. My Project Docs" class="w-full" />
                </UFormField>
                <UFormField label="Repository URL">
                  <UInput v-model="gitForm.gitUrl" placeholder="https://github.com/user/repo" class="w-full" />
                </UFormField>
                <UFormField label="Branch">
                  <UInput v-model="gitForm.gitBranch" class="w-full" />
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
