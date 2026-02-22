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

const activeTab = ref('file')
const fileForm = reactive({ title: '', sourceType: 'pdf', file: null as File | null })
const gitForm = reactive({ title: '', gitUrl: '', gitBranch: 'main', gitCredential: '' })
const submitting = ref(false)
const success = ref('')
const error = ref('')

async function submitFile() {
  if (!fileForm.file || !fileForm.title) return
  submitting.value = true
  error.value = ''
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
  try {
    const body: Record<string, string> = { kb: kbId, title: gitForm.title, source_type: 'git', git_url: gitForm.gitUrl, git_branch: gitForm.gitBranch }
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

const tabs = [
  { label: 'Upload File', value: 'file' },
  { label: 'Git Repository', value: 'git' },
]
</script>

<template>
  <UDashboardPanel id="sources" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6 max-w-2xl">
        <div>
          <NuxtLink :to="`/admin/knowledge-bases/${kbId}`" class="text-sm text-dimmed hover:text-default">&larr; Back</NuxtLink>
          <h1 class="text-2xl font-bold text-highlighted mt-2">Add Source</h1>
        </div>

        <UAlert v-if="success" color="success" :description="success" />
        <UAlert v-if="error" color="error" :description="error" />

        <UTabs v-model="activeTab" :items="tabs">
          <template #item="{ item }">
            <div v-if="item.value === 'file'" class="space-y-4 pt-4">
              <UFormField label="Title"><UInput v-model="fileForm.title" /></UFormField>
              <UFormField label="Type">
                <USelectMenu v-model="fileForm.sourceType" :items="['pdf', 'epub']" />
              </UFormField>
              <UFormField label="File">
                <input type="file" :accept="fileForm.sourceType === 'pdf' ? '.pdf' : '.epub'" @change="onFileChange" class="text-sm" />
              </UFormField>
              <UButton :loading="submitting" :disabled="!fileForm.file || !fileForm.title" @click="submitFile">Upload &amp; Ingest</UButton>
            </div>
            <div v-else-if="item.value === 'git'" class="space-y-4 pt-4">
              <UFormField label="Title"><UInput v-model="gitForm.title" /></UFormField>
              <UFormField label="Repository URL"><UInput v-model="gitForm.gitUrl" placeholder="https://github.com/user/repo" /></UFormField>
              <UFormField label="Branch"><UInput v-model="gitForm.gitBranch" /></UFormField>
              <UFormField label="Git Credential (optional)">
                <USelectMenu
                  v-model="gitForm.gitCredential"
                  :items="[{ label: 'None (public repo)', value: '' }, ...(credentials || []).map(c => ({ label: c.label, value: c.id }))]"
                  value-key="value"
                />
              </UFormField>
              <UButton :loading="submitting" :disabled="!gitForm.title || !gitForm.gitUrl" @click="submitGit">Add &amp; Ingest</UButton>
            </div>
          </template>
        </UTabs>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
