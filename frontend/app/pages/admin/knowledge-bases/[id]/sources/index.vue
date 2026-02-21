<script setup lang="ts">
definePageMeta({ middleware: "admin", layout: "admin" })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string

const activeTab = ref<"file" | "git">("file")
const fileForm = reactive({ title: "", sourceType: "pdf" as "pdf" | "epub", file: null as File | null })
const gitForm = reactive({ title: "", gitUrl: "", gitBranch: "main", gitCredential: "" })
const submitting = ref(false)
const success = ref("")
const error = ref("")

interface GitCredential {
  id: string
  label: string
}

const { data: credentials } = await useFetch<GitCredential[]>("/git-credentials/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as GitCredential[],
})

async function submitFile() {
  if (!fileForm.file || !fileForm.title) return
  submitting.value = true
  error.value = ""
  try {
    const fd = new FormData()
    fd.append("kb", kbId)
    fd.append("title", fileForm.title)
    fd.append("source_type", fileForm.sourceType)
    fd.append("file", fileForm.file)
    await ($api as typeof $fetch)("/sources/", { method: "POST", body: fd })
    success.value = "Source added. Ingestion started."
    fileForm.title = ""
    fileForm.file = null
  } catch {
    error.value = "Failed to add source."
  } finally {
    submitting.value = false
  }
}

async function submitGit() {
  if (!gitForm.title || !gitForm.gitUrl) return
  submitting.value = true
  error.value = ""
  try {
    const body: Record<string, string> = {
      kb: kbId,
      title: gitForm.title,
      source_type: "git",
      git_url: gitForm.gitUrl,
      git_branch: gitForm.gitBranch,
    }
    if (gitForm.gitCredential) body.git_credential = gitForm.gitCredential
    await ($api as typeof $fetch)("/sources/", { method: "POST", body })
    success.value = "Git source added. Ingestion started."
    gitForm.title = ""
    gitForm.gitUrl = ""
  } catch {
    error.value = "Failed to add git source."
  } finally {
    submitting.value = false
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  fileForm.file = input.files?.[0] ?? null
}
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto">
    <NuxtLink :to="`/admin/knowledge-bases/${kbId}`" class="text-sm text-gray-400 hover:text-gray-600">&larr; Back</NuxtLink>
    <h1 class="text-2xl font-bold mt-2 mb-6 text-gray-900 dark:text-white">Add Source</h1>

    <UAlert v-if="success" color="success" :description="success" class="mb-4" />
    <UAlert v-if="error" color="error" :description="error" class="mb-4" />

    <UTabs v-model="activeTab" :items="[{ label: 'Upload File', value: 'file' }, { label: 'Git Repository', value: 'git' }]">
      <template #file>
        <div class="space-y-4 pt-4">
          <UFormField label="Title">
            <UInput v-model="fileForm.title" placeholder="My document" />
          </UFormField>
          <UFormField label="Type">
            <USelect v-model="fileForm.sourceType" :options="['pdf', 'epub']" />
          </UFormField>
          <UFormField label="File">
            <input type="file" :accept="fileForm.sourceType === 'pdf' ? '.pdf' : '.epub'" @change="onFileChange" class="text-sm" />
          </UFormField>
          <UButton :loading="submitting" :disabled="!fileForm.file || !fileForm.title" @click="submitFile">
            Upload & Ingest
          </UButton>
        </div>
      </template>
      <template #git>
        <div class="space-y-4 pt-4">
          <UFormField label="Title">
            <UInput v-model="gitForm.title" placeholder="My repo" />
          </UFormField>
          <UFormField label="Repository URL">
            <UInput v-model="gitForm.gitUrl" placeholder="https://github.com/user/repo" />
          </UFormField>
          <UFormField label="Branch">
            <UInput v-model="gitForm.gitBranch" />
          </UFormField>
          <UFormField label="Git Credential (optional)">
            <USelect
              v-model="gitForm.gitCredential"
              :options="[{ label: 'None (public repo)', value: '' }, ...(credentials || []).map(c => ({ label: c.label, value: c.id }))]"
            />
          </UFormField>
          <UButton :loading="submitting" :disabled="!gitForm.title || !gitForm.gitUrl" @click="submitGit">
            Add & Ingest
          </UButton>
        </div>
      </template>
    </UTabs>
  </div>
</template>
