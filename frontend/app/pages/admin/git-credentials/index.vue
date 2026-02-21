<script setup lang="ts">
definePageMeta({ middleware: "admin", layout: "admin" })
const { $api } = useNuxtApp()

interface GitCredential {
  id: string
  label: string
  created_at: string
}

const { data: credentials, refresh } = await useFetch<GitCredential[]>("/git-credentials/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as GitCredential[],
})

const showCreate = ref(false)
const form = reactive({ label: "", pat: "" })
const submitting = ref(false)

async function createCredential() {
  if (!form.label || !form.pat) return
  submitting.value = true
  try {
    await ($api as typeof $fetch)("/git-credentials/", {
      method: "POST",
      body: { label: form.label, pat: form.pat },
    })
    form.label = ""
    form.pat = ""
    showCreate.value = false
    refresh()
  } finally {
    submitting.value = false
  }
}

async function deleteCredential(id: string) {
  await ($api as typeof $fetch)(`/git-credentials/${id}/`, { method: "DELETE" })
  refresh()
}
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Git Credentials</h1>
      <UButton @click="showCreate = true" icon="i-heroicons-plus">Add Credential</UButton>
    </div>

    <UModal v-model:open="showCreate" title="Add Git Credential">
      <template #body>
        <div class="space-y-3">
          <UFormField label="Label">
            <UInput v-model="form.label" placeholder="My GitHub PAT" autofocus />
          </UFormField>
          <UFormField label="Personal Access Token">
            <UInput v-model="form.pat" type="password" placeholder="ghp_..." />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <UButton :loading="submitting" :disabled="!form.label || !form.pat" @click="createCredential">Save</UButton>
        <UButton variant="ghost" @click="showCreate = false">Cancel</UButton>
      </template>
    </UModal>

    <div class="space-y-3">
      <div
        v-for="cred in credentials"
        :key="cred.id"
        class="flex items-center justify-between p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
      >
        <div>
          <p class="font-medium text-sm">{{ cred.label }}</p>
          <p class="text-xs text-gray-400 mt-0.5 font-mono">••••••••••••••••</p>
        </div>
        <UButton size="xs" variant="ghost" color="error" icon="i-heroicons-trash" @click="deleteCredential(cred.id)" />
      </div>
      <p v-if="!credentials?.length" class="text-gray-400 text-center mt-8">No credentials yet.</p>
    </div>
  </div>
</template>
