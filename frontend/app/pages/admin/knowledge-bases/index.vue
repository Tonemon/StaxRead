<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const { $api } = useNuxtApp()

interface KB { id: string; name: string; description: string; owner_username: string; created_at: string }
interface Invitation { id: string; kb_id: string; kb_name: string; kb_description: string; owner_username: string }

const { data: kbs, refresh } = await useFetch<KB[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

const { data: invitations, refresh: refreshInvitations } = await useFetch<Invitation[]>('/kb-invitations/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Invitation[],
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

const deleteTargetId = ref<string | null>(null)

function confirmDelete(id: string) {
  deleteTargetId.value = id
}

async function acceptInvitation(id: string) {
  await ($api as typeof $fetch)(`/kb-invitations/${id}/accept/`, { method: 'POST' })
  refreshInvitations()
  refresh()
}

async function declineInvitation(id: string) {
  await ($api as typeof $fetch)(`/kb-invitations/${id}/decline/`, { method: 'POST' })
  refreshInvitations()
}

async function doDelete() {
  if (!deleteTargetId.value) return
  await ($api as typeof $fetch)(`/knowledge-bases/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}

function onDeleteModalUpdate(open: boolean) {
  if (!open) deleteTargetId.value = null
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

        <UModal :open="!!deleteTargetId" title="Delete Knowledge Base" @update:open="onDeleteModalUpdate">
          <template #body>
            <p class="text-sm text-muted">Are you sure you want to delete this knowledge base? This action cannot be undone.</p>
          </template>
          <template #footer>
            <UButton color="error" @click="doDelete">Delete</UButton>
            <UButton color="neutral" variant="ghost" @click="deleteTargetId = null">Cancel</UButton>
          </template>
        </UModal>

        <div v-if="invitations?.length" class="space-y-2">
          <p class="text-xs font-semibold text-dimmed uppercase tracking-wider">Pending Invitations</p>
          <div v-for="inv in invitations" :key="inv.id" class="flex items-center justify-between gap-3 p-4 bg-default rounded-lg ring ring-default">
            <div class="min-w-0">
              <p class="font-medium text-highlighted">{{ inv.kb_name }}</p>
              <p class="text-xs text-dimmed mt-0.5">Shared by {{ inv.owner_username }}</p>
              <p v-if="inv.kb_description" class="text-sm text-muted mt-1">{{ inv.kb_description }}</p>
            </div>
            <div class="flex gap-2 shrink-0">
              <UButton size="xs" color="neutral" variant="outline" icon="i-lucide-check" @click="acceptInvitation(inv.id)">Accept</UButton>
              <UButton size="xs" color="error" variant="ghost" icon="i-lucide-x" @click="declineInvitation(inv.id)">Decline</UButton>
            </div>
          </div>
        </div>

        <div class="space-y-2">
          <div v-for="kb in kbs" :key="kb.id" class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default">
            <div>
              <NuxtLink :to="`/admin/knowledge-bases/${kb.id}`" class="font-medium hover:underline text-highlighted">{{ kb.name }}</NuxtLink>
              <p class="text-xs text-dimmed mt-0.5">Owner: {{ kb.owner_username }}</p>
              <p v-if="kb.description" class="text-sm text-muted mt-1">{{ kb.description }}</p>
            </div>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="confirmDelete(kb.id)" />
          </div>
          <p v-if="!kbs?.length" class="text-dimmed text-center mt-8">No knowledge bases yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
