<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const { $api } = useNuxtApp()

interface Team { id: string; name: string; description: string; my_role: string }

const { data: teams, refresh } = await useFetch<Team[]>('/teams/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as Team[],
})

const showCreate = ref(false)
const form = reactive({ name: '', description: '' })
const submitting = ref(false)

async function createTeam() {
  if (!form.name) return
  submitting.value = true
  try {
    await ($api as typeof $fetch)('/teams/', { method: 'POST', body: { ...form } })
    form.name = ''
    form.description = ''
    showCreate.value = false
    refresh()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <UDashboardPanel id="teams" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header><DashboardNavbar /></template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-highlighted">Teams</h1>
            <p class="text-sm text-dimmed mt-0.5">Collaborate with others on shared Knowledge Bases.</p>
          </div>
          <UButton icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">
            New Team
          </UButton>
        </div>

        <div class="space-y-2">
          <NuxtLink
            v-for="team in teams"
            :key="team.id"
            :to="`/settings/teams/${team.id}/general`"
            class="flex items-center justify-between p-4 bg-default rounded-lg ring ring-default hover:bg-elevated/50 transition-colors"
          >
            <div>
              <p class="font-medium text-highlighted">{{ team.name }}</p>
              <p v-if="team.description" class="text-xs text-dimmed mt-0.5">{{ team.description }}</p>
            </div>
            <UBadge color="neutral" variant="subtle" size="xs" class="capitalize">{{ team.my_role }}</UBadge>
          </NuxtLink>
          <p v-if="!teams.length" class="text-dimmed text-center py-8">You are not in any teams yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>

  <UModal v-model:open="showCreate" title="New Team">
    <template #body>
      <div class="space-y-3">
        <UFormField label="Team name" required>
          <UInput v-model="form.name" autofocus @keydown.enter="createTeam" />
        </UFormField>
        <UFormField label="Description">
          <UInput v-model="form.description" @keydown.enter="createTeam" />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <UButton :loading="submitting" :disabled="!form.name" @click="createTeam">Create</UButton>
      <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
    </template>
  </UModal>
</template>
