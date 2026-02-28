<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const teamId = route.params.id as string

interface Team { id: string; name: string; description: string; icon_url: string; my_role: string }

const { data: team, refresh } = await useFetch<Team>(`/teams/${teamId}/`, {
  $fetch: $api as typeof $fetch,
})

const isAdminOrOwner = computed(() => ['admin', 'owner'].includes(team.value?.my_role ?? ''))
const isOwner = computed(() => team.value?.my_role === 'owner')

const form = reactive({ name: '', description: '' })
const saving = ref(false)
const saveSuccess = ref(false)

watch(team, (t) => {
  if (t) { form.name = t.name; form.description = t.description }
}, { immediate: true })

async function save() {
  saving.value = true
  saveSuccess.value = false
  try {
    await ($api as typeof $fetch)(`/teams/${teamId}/`, {
      method: 'PATCH',
      body: { name: form.name, description: form.description },
    })
    saveSuccess.value = true
    refresh()
  } finally {
    saving.value = false
  }
}

const showTransfer = ref(false)
const transferUsername = ref('')
const transferError = ref('')

async function transferOwnership() {
  transferError.value = ''
  try {
    const users = await ($api as typeof $fetch)<{ id: string; username: string }[]>('/auth/users/')
    const target = users.find(u => u.username === transferUsername.value)
    if (!target) { transferError.value = 'User not found'; return }
    await ($api as typeof $fetch)(`/teams/${teamId}/transfer-ownership/`, {
      method: 'POST',
      body: { user_id: target.id },
    })
    showTransfer.value = false
    transferUsername.value = ''
    refresh()
  } catch {
    transferError.value = 'Transfer failed'
  }
}

const showDelete = ref(false)

async function deleteTeam() {
  await ($api as typeof $fetch)(`/teams/${teamId}/`, { method: 'DELETE' })
  await navigateTo('/settings/teams')
}
</script>

<template>
  <UDashboardPanel id="team-general" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header><DashboardNavbar /></template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6 max-w-xl">
        <div>
          <NuxtLink to="/settings/teams" class="text-sm text-dimmed hover:text-default">&larr; Teams</NuxtLink>
          <h1 class="text-2xl font-bold text-highlighted mt-2">{{ team?.name }}</h1>
          <p class="text-xs text-dimmed capitalize mt-0.5">Your role: {{ team?.my_role }}</p>
        </div>

        <div class="space-y-4">
          <UFormField label="Team name">
            <UInput v-model="form.name" :disabled="!isAdminOrOwner" />
          </UFormField>
          <UFormField label="Description">
            <UTextarea v-model="form.description" :disabled="!isAdminOrOwner" :rows="3" />
          </UFormField>
          <UAlert v-if="saveSuccess" color="success" description="Team settings saved." />
          <UButton v-if="isAdminOrOwner" :loading="saving" :disabled="!form.name" @click="save">
            Save
          </UButton>
        </div>

        <div v-if="isOwner" class="space-y-3 border-t border-default pt-6">
          <h2 class="text-sm font-semibold text-dimmed uppercase tracking-wider">Danger Zone</h2>
          <div class="flex items-center justify-between p-4 rounded-lg ring ring-error/30">
            <div>
              <p class="text-sm font-medium text-highlighted">Transfer ownership</p>
              <p class="text-xs text-dimmed">Assign the Owner role to another member. You become Admin.</p>
            </div>
            <UButton color="neutral" variant="outline" size="sm" @click="showTransfer = true">
              Transfer
            </UButton>
          </div>
          <div class="flex items-center justify-between p-4 rounded-lg ring ring-error/30">
            <div>
              <p class="text-sm font-medium text-highlighted">Delete team</p>
              <p class="text-xs text-dimmed">Permanently deletes the team and all its Knowledge Bases.</p>
            </div>
            <UButton color="error" variant="outline" size="sm" @click="showDelete = true">
              Delete
            </UButton>
          </div>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>

  <UModal v-model:open="showTransfer" title="Transfer Ownership">
    <template #body>
      <div class="space-y-3">
        <p class="text-sm text-muted">Enter the username of the team member who should become the new Owner.</p>
        <UInput v-model="transferUsername" placeholder="Username" @keydown.enter="transferOwnership" />
        <UAlert v-if="transferError" color="error" :description="transferError" />
      </div>
    </template>
    <template #footer>
      <UButton color="warning" :disabled="!transferUsername" @click="transferOwnership">Transfer</UButton>
      <UButton color="neutral" variant="ghost" @click="showTransfer = false">Cancel</UButton>
    </template>
  </UModal>

  <UModal v-model:open="showDelete" title="Delete Team">
    <template #body>
      <p class="text-sm text-muted">
        Are you sure? This will permanently delete the team and all its Knowledge Bases. This cannot be undone.
      </p>
    </template>
    <template #footer>
      <UButton color="error" @click="deleteTeam">Delete Team</UButton>
      <UButton color="neutral" variant="ghost" @click="showDelete = false">Cancel</UButton>
    </template>
  </UModal>
</template>
