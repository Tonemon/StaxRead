<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const { $api } = useNuxtApp()

interface GitCredential { id: string; label: string; created_at: string }

const { data: credentials, refresh } = await useFetch<GitCredential[]>('/git-credentials/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as GitCredential[],
})

const showCreate = ref(false)
const form = reactive({ label: '', pat: '' })
const submitting = ref(false)

async function createCredential() {
  submitting.value = true
  try {
    await ($api as typeof $fetch)('/git-credentials/', { method: 'POST', body: { label: form.label, pat: form.pat } })
    form.label = ''
    form.pat = ''
    showCreate.value = false
    refresh()
  } finally {
    submitting.value = false
  }
}

const deleteTargetId = ref<string | null>(null)

function confirmDelete(id: string) {
  deleteTargetId.value = id
}

async function doDelete() {
  if (!deleteTargetId.value) return
  await ($api as typeof $fetch)(`/git-credentials/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}
</script>

<template>
  <UDashboardPanel id="git-credentials" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-highlighted">Git Credentials</h1>
          <UButton icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">Add Credential</UButton>
        </div>

        <UModal v-model:open="showCreate" title="Add Git Credential">
          <template #body>
            <div class="space-y-3">
              <UFormField label="Label"><UInput v-model="form.label" autofocus /></UFormField>
              <UFormField label="Personal Access Token"><UInput v-model="form.pat" type="password" /></UFormField>
            </div>
          </template>
          <template #footer>
            <UButton :loading="submitting" :disabled="!form.label || !form.pat" @click="createCredential">Save</UButton>
            <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
          </template>
        </UModal>

        <UModal :open="!!deleteTargetId" title="Delete Git Credential" @update:open="if (!$event) deleteTargetId = null">
          <template #body>
            <p class="text-sm text-muted">Are you sure you want to delete this credential? This action cannot be undone.</p>
          </template>
          <template #footer>
            <UButton color="error" @click="doDelete">Delete</UButton>
            <UButton color="neutral" variant="ghost" @click="deleteTargetId = null">Cancel</UButton>
          </template>
        </UModal>

        <div class="space-y-2">
          <div v-for="cred in credentials" :key="cred.id" class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default">
            <div>
              <p class="font-medium text-sm text-highlighted">{{ cred.label }}</p>
              <p class="text-xs text-dimmed mt-0.5 font-mono">••••••••••••••••</p>
            </div>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="confirmDelete(cred.id)" />
          </div>
          <p v-if="!credentials?.length" class="text-dimmed text-center mt-8">No credentials yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
