<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string

interface KB { id: string; name: string; description: string; owner_username: string }
interface Source { id: string; title: string; source_type: string; status: string }

const { data: kb } = await useFetch<KB>(`/knowledge-bases/${kbId}/`, { $fetch: $api as typeof $fetch })
const { data: sources, refresh: refreshSources } = await useFetch<Source[]>('/sources/', {
  $fetch: $api as typeof $fetch,
  query: { kb: kbId },
  default: () => [] as Source[],
})

const shareUsername = ref('')
const shareError = ref('')

async function share() {
  shareError.value = ''
  try {
    const users = await ($api as typeof $fetch)<{ id: string; username: string }[]>('/auth/users/')
    const target = users.find(u => u.username === shareUsername.value)
    if (!target) { shareError.value = 'User not found'; return }
    await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/share/`, { method: 'POST', body: { user_id: target.id } })
    shareUsername.value = ''
  } catch {
    shareError.value = 'Failed to share'
  }
}

const statusColor: Record<string, string> = { pending: 'warning', processing: 'info', ready: 'success', error: 'error' }
</script>

<template>
  <UDashboardPanel id="kb-detail" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6">
        <div>
          <NuxtLink to="/admin/knowledge-bases" class="text-sm text-dimmed hover:text-default">&larr; Knowledge Bases</NuxtLink>
          <h1 class="text-2xl font-bold text-highlighted mt-2">{{ kb?.name }}</h1>
          <p v-if="kb?.description" class="text-sm text-muted mt-1">{{ kb.description }}</p>
        </div>

        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-semibold text-highlighted">Sources</h2>
            <NuxtLink :to="`/admin/knowledge-bases/${kbId}/sources`">
              <UButton size="sm" icon="i-lucide-plus" color="neutral" variant="outline">Add Source</UButton>
            </NuxtLink>
          </div>
          <div class="space-y-2">
            <div v-for="source in sources" :key="source.id" class="flex items-center justify-between p-3 bg-default rounded-lg ring ring-default">
              <div>
                <span class="text-sm font-medium">{{ source.title }}</span>
                <span class="text-xs text-dimmed ml-2">{{ source.source_type }}</span>
              </div>
              <UBadge :color="statusColor[source.status] || 'neutral'" size="xs">{{ source.status }}</UBadge>
            </div>
            <p v-if="!sources?.length" class="text-sm text-dimmed">No sources yet.</p>
          </div>
        </div>

        <div>
          <h2 class="text-lg font-semibold text-highlighted mb-3">Share Access</h2>
          <div class="flex gap-2">
            <UInput v-model="shareUsername" placeholder="Username" size="sm" class="flex-1" />
            <UButton size="sm" :disabled="!shareUsername" @click="share">Share</UButton>
          </div>
          <UAlert v-if="shareError" color="error" :description="shareError" class="mt-2" />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
