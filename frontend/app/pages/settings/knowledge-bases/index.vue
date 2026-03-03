<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const { $api } = useNuxtApp()
const authStore = useAuthStore()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

interface KB { id: string; name: string; description: string; owner_username: string; created_at: string; team: string | null }
interface Invitation { id: string; kb_id: string; kb_name: string; kb_description: string; owner_username: string }
interface Team { id: string; name: string; my_role: string }

const { data: kbs, refresh } = await useFetch<KB[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

const personalKbs = computed(() => (kbs.value ?? []).filter(kb => kb.team === null))

const { data: invitations, refresh: refreshInvitations } = await useFetch<Invitation[]>('/kb-invitations/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Invitation[],
})

const { data: teams } = await useFetch<Team[]>('/teams/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Team[],
})

const MANAGER_ROLES = ['manager', 'admin', 'owner']

const locationOptions = computed(() => {
  const opts = [{ label: 'Personal', value: 'personal' }]
  for (const t of (teams.value || [])) {
    if (MANAGER_ROLES.includes(t.my_role)) {
      opts.push({ label: t.name, value: t.id })
    }
  }
  return opts
})

const showCreate = ref(false)
const form = reactive({ name: '', description: '', team_id: 'personal' })

async function createKB() {
  if (!form.name) return
  const body: Record<string, unknown> = { name: form.name, description: form.description }
  if (form.team_id !== 'personal') body.team = form.team_id
  await ($api as typeof $fetch)('/knowledge-bases/', { method: 'POST', body })
  form.name = ''
  form.description = ''
  form.team_id = 'personal'
  showCreate.value = false
  refresh()
}

const deleteTargetId = ref<string | null>(null)

const deleteTargetIsShared = computed(() => {
  const kb = kbs.value?.find(k => k.id === deleteTargetId.value)
  return kb ? kb.owner_username !== authStore.user?.username : false
})

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
  if (deleteTargetIsShared.value) {
    await ($api as typeof $fetch)(`/knowledge-bases/${deleteTargetId.value}/leave/`, { method: 'POST' })
  } else {
    await ($api as typeof $fetch)(`/knowledge-bases/${deleteTargetId.value}/`, { method: 'DELETE' })
  }
  deleteTargetId.value = null
  refresh()
}

function onDeleteModalUpdate(open: boolean) {
  if (!open) deleteTargetId.value = null
}

onMounted(() => setRefresh(() => { refresh(); refreshInvitations() }))
onUnmounted(clearRefresh)
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
              <UFormField label="Name"><UInput v-model="form.name" autofocus @keydown.enter="createKB" /></UFormField>
              <UFormField label="Description"><UTextarea v-model="form.description" :rows="2" /></UFormField>
              <UFormField v-if="locationOptions.length > 1" label="Location">
                <USelectMenu v-model="form.team_id" :items="locationOptions" value-key="value" class="w-full" />
              </UFormField>
            </div>
          </template>
          <template #footer>
            <UButton :disabled="!form.name" @click="createKB">Create</UButton>
            <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
          </template>
        </UModal>

        <UModal :open="!!deleteTargetId" :title="deleteTargetIsShared ? 'Leave Knowledge Base' : 'Delete Knowledge Base'" @update:open="onDeleteModalUpdate">
          <template #body>
            <p class="text-sm text-muted">
              <template v-if="deleteTargetIsShared">Are you sure you want to leave this knowledge base? You will lose access to it.</template>
              <template v-else>Are you sure you want to delete this knowledge base? This action cannot be undone.</template>
            </p>
          </template>
          <template #footer>
            <UButton color="error" @click="doDelete">{{ deleteTargetIsShared ? 'Leave' : 'Delete' }}</UButton>
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
          <div v-for="kb in personalKbs" :key="kb.id" class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default">
            <div>
              <div class="flex items-center gap-1.5">
                <UIcon v-if="kb.owner_username !== authStore.user?.username" name="i-lucide-share-2" class="size-3.5 text-dimmed shrink-0" />
                <NuxtLink :to="`/settings/knowledge-bases/${kb.id}`" class="font-medium hover:underline text-highlighted">{{ kb.name }}</NuxtLink>
              </div>
              <p class="text-xs text-dimmed mt-0.5">Owner: {{ kb.owner_username }}</p>
              <p v-if="kb.description" class="text-sm text-muted mt-1">{{ kb.description }}</p>
            </div>
            <UButton size="xs" variant="ghost" color="error" icon="i-lucide-trash" @click="confirmDelete(kb.id)" />
          </div>
          <p v-if="!personalKbs.length" class="text-dimmed text-center mt-8">No knowledge bases yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
