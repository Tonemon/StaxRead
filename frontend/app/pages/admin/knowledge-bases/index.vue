<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const { $api } = useNuxtApp()

interface KB { id: string; name: string; description: string; owner_username: string; created_at: string }

const { data: kbs, refresh } = await useFetch<KB[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

const showCreate = ref(false)
const form = reactive({ name: '', description: '' })

async function createKB() {
  await ($api as typeof $fetch)('/knowledge-bases/', { method: 'POST', body: { name: form.name, description: form.description } })
  form.name = ''
  form.description = ''
  showCreate.value = false
  refresh()
}

async function deleteKB(id: string) {
  await ($api as typeof $fetch)(`/knowledge-bases/${id}/`, { method: 'DELETE' })
  refresh()
}
</script>

<template>
  <UDashboardPanel id="kb-list" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-highlighted">Knowledge Bases</h1>
          <UButton icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">New KB</UButton>
        </div>

        <UModal v-model:open="showCreate" title="Create Knowledge Base">
          <template #body>
            <div class="space-y-3">
              <UFormField label="Name"><UInput v-model="form.name" autofocus /></UFormField>
              <UFormField label="Description"><UTextarea v-model="form.description" :rows="2" /></UFormField>
            </div>
          </template>
          <template #footer>
            <UButton :disabled="!form.name" @click="createKB">Create</UButton>
            <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
          </template>
        </UModal>

        <div class="space-y-2">
          <div v-for="kb in kbs" :key="kb.id" class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default">
            <div>
              <NuxtLink :to="`/admin/knowledge-bases/${kb.id}`" class="font-medium hover:underline text-highlighted">{{ kb.name }}</NuxtLink>
              <p class="text-xs text-dimmed mt-0.5">Owner: {{ kb.owner_username }}</p>
              <p v-if="kb.description" class="text-sm text-muted mt-1">{{ kb.description }}</p>
            </div>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="deleteKB(kb.id)" />
          </div>
          <p v-if="!kbs?.length" class="text-dimmed text-center mt-8">No knowledge bases yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
