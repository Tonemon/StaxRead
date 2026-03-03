<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const teamId = route.params.id as string
const authStore = useAuthStore()

interface Member { username: string; role: string }
interface KnowledgeBase { id: string; name: string; description?: string }

const { data: members } = await useFetch<Member[]>(`/teams/${teamId}/members/`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as Member[],
})

const canManage = computed(() => {
  const role = members.value?.find(m => m.username === authStore.user?.username)?.role ?? ''
  return ['manager', 'admin', 'owner'].includes(role)
})

const { data: knowledgeBases, refresh } = await useFetch<KnowledgeBase[]>(`/knowledge-bases/?team=${teamId}`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as KnowledgeBase[],
})

const showCreate = ref(false)
const form = reactive({ name: '', description: '' })
const submitting = ref(false)

async function createKnowledgeBase() {
  if (!form.name) return
  submitting.value = true
  try {
    await ($api as typeof $fetch)('/knowledge-bases/', {
      method: 'POST',
      body: { name: form.name, description: form.description, team: teamId },
    })
    form.name = ''
    form.description = ''
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
  await ($api as typeof $fetch)(`/knowledge-bases/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}

function onDeleteModalUpdate(open: boolean) {
  if (!open) deleteTargetId.value = null
}
</script>

<template>
  <UDashboardPanel id="team-knowledge-bases" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header><DashboardNavbar /></template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6">
        <div>
          <NuxtLink :to="`/settings/teams/${teamId}/general`" class="text-sm text-dimmed hover:text-default">&larr; Team Settings</NuxtLink>
          <div class="flex items-center justify-between mt-2">
            <h1 class="text-2xl font-bold text-highlighted">Team Knowledge Bases</h1>
            <UButton v-if="canManage" icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">
              New KB
            </UButton>
          </div>
        </div>

        <UModal v-model:open="showCreate" title="New Knowledge Base">
          <template #body>
            <div class="space-y-3">
              <UFormField label="Name" required>
                <UInput v-model="form.name" autofocus @keydown.enter="createKnowledgeBase" />
              </UFormField>
              <UFormField label="Description">
                <UTextarea v-model="form.description" :rows="3" />
              </UFormField>
            </div>
          </template>
          <template #footer>
            <UButton :loading="submitting" :disabled="!form.name" @click="createKnowledgeBase">Create</UButton>
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

        <div class="space-y-2">
          <div v-for="kb in knowledgeBases" :key="kb.id" class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default">
            <div>
              <NuxtLink :to="`/settings/knowledge-bases/${kb.id}`" class="font-medium text-sm text-highlighted hover:underline">
                {{ kb.name }}
              </NuxtLink>
              <p v-if="kb.description" class="text-xs text-dimmed mt-0.5">{{ kb.description }}</p>
            </div>
            <UButton v-if="canManage" size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="confirmDelete(kb.id)" />
          </div>
          <p v-if="!knowledgeBases?.length" class="text-dimmed text-center mt-8">No knowledge bases yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
