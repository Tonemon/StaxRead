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

// ── Inline editing ──────────────────────────────────────────────────────────
const editingName = ref(false)
const editingDescription = ref(false)
const editNameValue = ref('')
const editDescValue = ref('')

function startEditName() {
  editNameValue.value = kb.value?.name || ''
  editingName.value = true
}

function startEditDescription() {
  editDescValue.value = kb.value?.description || ''
  editingDescription.value = true
}

async function saveName() {
  if (!editingName.value) return
  editingName.value = false
  if (editNameValue.value === kb.value?.name || !editNameValue.value) return
  await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/`, { method: 'PATCH', body: { name: editNameValue.value } })
  if (kb.value) kb.value.name = editNameValue.value
}

async function saveDescription() {
  if (!editingDescription.value) return
  editingDescription.value = false
  if (editDescValue.value === kb.value?.description) return
  await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/`, { method: 'PATCH', body: { description: editDescValue.value } })
  if (kb.value) kb.value.description = editDescValue.value
}

function cancelEditName() {
  editingName.value = false
}

function cancelEditDescription() {
  editingDescription.value = false
}

// ── Sources section ────────────────────────────────────────────────────────
const sourceTabs = [
  { label: 'PDF', value: 'pdf' },
  { label: 'EPUB', value: 'epub' },
  { label: 'Git Repositories', value: 'git' },
]
const activeSourceTab = ref('pdf')
const sourceSearch = ref('')
const sourcePage = ref(1)
const PAGE_SIZE = 10

const filteredSources = computed(() => {
  const q = sourceSearch.value.toLowerCase().trim()
  return (sources.value || [])
    .filter(s => s.source_type === activeSourceTab.value)
    .filter(s => !q || s.title.toLowerCase().includes(q))
})

const totalSourcePages = computed(() => Math.max(1, Math.ceil(filteredSources.value.length / PAGE_SIZE)))

const pagedSources = computed(() => {
  const start = (sourcePage.value - 1) * PAGE_SIZE
  return filteredSources.value.slice(start, start + PAGE_SIZE)
})

watch([sourceSearch, activeSourceTab], () => { sourcePage.value = 1 })

const statusColor: Record<string, string> = {
  pending: 'warning',
  processing: 'info',
  ready: 'success',
  error: 'error',
}

const emptyLabel: Record<string, string> = {
  pdf: 'No PDF sources yet.',
  epub: 'No EPUB sources yet.',
  git: 'No Git repository sources yet.',
}

async function deleteSource(id: string) {
  await ($api as typeof $fetch)(`/sources/${id}/`, { method: 'DELETE' })
  refreshSources()
}

// ── Share section ──────────────────────────────────────────────────────────
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
</script>

<template>
  <UDashboardPanel id="kb-detail" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <div class="flex flex-1">
        <UContainer class="flex-1 flex flex-col gap-6 py-6">

          <!-- Header -->
          <div>
            <NuxtLink to="/admin/knowledge-bases" class="text-sm text-dimmed hover:text-default">&larr; Knowledge Bases</NuxtLink>

            <!-- Editable name -->
            <div class="mt-2">
              <template v-if="editingName">
                <UInput
                  v-model="editNameValue"
                  autofocus
                  size="lg"
                  class="text-2xl font-bold w-full"
                  @blur="saveName"
                  @keydown.enter="saveName"
                  @keydown.escape="cancelEditName"
                />
              </template>
              <h1
                v-else
                class="text-2xl font-bold text-highlighted cursor-pointer hover:text-primary transition-colors"
                title="Click to edit"
                @click="startEditName"
              >
                {{ kb?.name }}
              </h1>
            </div>

            <!-- Editable description -->
            <div class="mt-1">
              <template v-if="editingDescription">
                <UTextarea
                  v-model="editDescValue"
                  autofocus
                  :rows="2"
                  class="w-full text-sm"
                  @blur="saveDescription"
                  @keydown.escape="cancelEditDescription"
                />
              </template>
              <p
                v-else
                class="text-sm cursor-pointer hover:text-default transition-colors"
                :class="kb?.description ? 'text-muted' : 'text-dimmed italic'"
                title="Click to edit"
                @click="startEditDescription"
              >
                {{ kb?.description || 'Add a description...' }}
              </p>
            </div>
          </div>

          <!-- Sources -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-highlighted">Sources</h2>
              <NuxtLink :to="`/admin/knowledge-bases/${kbId}/sources`">
                <UButton size="sm" icon="i-lucide-plus" color="neutral" variant="outline">Add Source</UButton>
              </NuxtLink>
            </div>

            <!-- Type tabs -->
            <UTabs v-model="activeSourceTab" :items="sourceTabs" class="mb-4" />

            <!-- Search -->
            <UInput
              v-model="sourceSearch"
              icon="i-lucide-search"
              placeholder="Search sources..."
              size="sm"
              class="w-full mb-3"
            />

            <!-- Table -->
            <div class="border border-default rounded-lg overflow-hidden">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-elevated border-b border-default">
                    <th class="px-4 py-2.5 text-left text-xs font-semibold text-dimmed uppercase tracking-wider">Title</th>
                    <th class="px-4 py-2.5 text-left text-xs font-semibold text-dimmed uppercase tracking-wider w-28">Status</th>
                    <th class="px-4 py-2.5 w-12"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-default">
                  <tr
                    v-for="source in pagedSources"
                    :key="source.id"
                    class="hover:bg-elevated/50 transition-colors"
                  >
                    <td class="px-4 py-3 text-default">{{ source.title }}</td>
                    <td class="px-4 py-3">
                      <UBadge :color="statusColor[source.status] || 'neutral'" size="xs">
                        {{ source.status }}
                      </UBadge>
                    </td>
                    <td class="px-4 py-3 text-right">
                      <UButton
                        icon="i-lucide-trash-2"
                        size="xs"
                        color="error"
                        variant="ghost"
                        @click="deleteSource(source.id)"
                      />
                    </td>
                  </tr>
                  <tr v-if="!pagedSources.length">
                    <td colspan="3" class="px-4 py-10 text-center text-sm text-dimmed">
                      {{ sourceSearch ? 'No sources match your search.' : emptyLabel[activeSourceTab] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination -->
            <div class="flex items-center justify-between mt-3">
              <p class="text-xs text-dimmed">
                {{ filteredSources.length }}
                {{ filteredSources.length === 1 ? 'source' : 'sources' }}
                <span v-if="totalSourcePages > 1"> &middot; Page {{ sourcePage }} of {{ totalSourcePages }}</span>
              </p>
              <div class="flex gap-2">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="outline"
                  icon="i-lucide-chevron-left"
                  :disabled="sourcePage === 1"
                  @click="sourcePage--"
                >
                  Previous
                </UButton>
                <UButton
                  size="xs"
                  color="neutral"
                  variant="outline"
                  trailing-icon="i-lucide-chevron-right"
                  :disabled="sourcePage >= totalSourcePages"
                  @click="sourcePage++"
                >
                  Next
                </UButton>
              </div>
            </div>
          </div>

          <!-- Share Access -->
          <div>
            <h2 class="text-lg font-semibold text-highlighted mb-3">Share Access</h2>
            <div class="flex gap-2">
              <UInput v-model="shareUsername" placeholder="Username" size="sm" class="flex-1" />
              <UButton size="sm" :disabled="!shareUsername" @click="share">Share</UButton>
            </div>
            <UAlert v-if="shareError" color="error" :description="shareError" class="mt-2" />
          </div>

        </UContainer>
      </div>
    </template>
  </UDashboardPanel>
</template>
