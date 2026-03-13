<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

interface KB { id: string; name: string; description: string; owner_username: string; team: string | null; team_name: string | null; user_permission: 'read' | 'write' }
interface Source {
  id: string; title: string; source_type: string; status: string
  file_size_bytes: number | null; chunk_count: number
  created_at: string; updated_at: string; last_synced_at: string | null
  error_message: string; git_url: string; git_branch: string
}

const { data: kb, refresh: refreshKb } = await useFetch<KB>(`/knowledge-bases/${kbId}/`, { $fetch: $api as typeof $fetch })
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
  refreshKb()
}

async function saveDescription() {
  if (!editingDescription.value) return
  editingDescription.value = false
  if (editDescValue.value === kb.value?.description) return
  await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/`, { method: 'PATCH', body: { description: editDescValue.value } })
  refreshKb()
}

function cancelEditName() {
  editingName.value = false
}

function cancelEditDescription() {
  editingDescription.value = false
}

// ── Drag-to-upload ──────────────────────────────────────────────────────────
const { isDragging, suppressGlobal, dropLabel } = usePdfDrop()

interface DropEntry { name: string; status: 'uploading' | 'done' | 'error' }
const dropUploads = ref<DropEntry[]>([])

function stemFromFilename(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot > 0 ? filename.substring(0, dot) : filename
}

const ACCEPTED_DROP_TYPES: Record<string, string> = {
  'application/pdf': 'pdf',
  'application/epub+zip': 'epub',
}

async function onWindowDrop(e: DragEvent) {
  const files = Array.from(e.dataTransfer?.files ?? []).filter(f => f.type in ACCEPTED_DROP_TYPES)
  if (!files.length) return
  for (const file of files) {
    const entry = reactive<DropEntry>({ name: file.name, status: 'uploading' })
    dropUploads.value.push(entry)
    try {
      const fd = new FormData()
      fd.append('kb', kbId)
      fd.append('title', stemFromFilename(file.name))
      fd.append('source_type', ACCEPTED_DROP_TYPES[file.type])
      fd.append('file', file)
      await ($api as typeof $fetch)('/sources/', { method: 'POST', body: fd })
      entry.status = 'done'
      refreshSources()
    } catch {
      entry.status = 'error'
    }
  }
}

onMounted(() => {
  suppressGlobal.value = true
  dropLabel.value = `Drop to add to "${kb.value?.name ?? 'this Knowledge Base'}"`
  window.addEventListener('drop', onWindowDrop)
  setRefresh(() => { refreshKb(); refreshSources() })
})

onUnmounted(() => {
  suppressGlobal.value = false
  dropLabel.value = null
  window.removeEventListener('drop', onWindowDrop)
  clearRefresh()
})

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

function fmtBytes(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return 'Unknown'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function deleteSource(id: string) {
  await ($api as typeof $fetch)(`/sources/${id}/`, { method: 'DELETE' })
  refreshSources()
}

async function downloadSource(id: string) {
  const data = await ($api as typeof $fetch)<{ url: string }>(`/sources/${id}/document/`)
  window.open(data.url, '_blank')
}

// ── Share section ──────────────────────────────────────────────────────────
interface Member {
  user_id: string
  username: string
  status: 'pending' | 'accepted'
  permission: 'read' | 'write'
  is_team_member: boolean
  team_role: string | null
}

const { data: members, refresh: refreshMembers } = await useFetch<Member[]>(`/knowledge-bases/${kbId}/members/`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as Member[],
})

const canManage = computed(() => kb.value?.user_permission === 'write')

const shareUsername = ref('')
const shareError = ref('')
const shareSuccess = ref('')

async function share() {
  shareError.value = ''
  shareSuccess.value = ''
  try {
    const users = await ($api as typeof $fetch)<{ id: string; username: string }[]>('/auth/users/')
    const target = users.find(u => u.username === shareUsername.value)
    if (!target) { shareError.value = 'User not found'; return }
    await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/share/`, { method: 'POST', body: { user_id: target.id } })
    shareSuccess.value = `${shareUsername.value} has been invited.`
    shareUsername.value = ''
    refreshMembers()
  } catch {
    shareError.value = 'Failed to share'
  }
}

async function removeMember(userId: string) {
  shareError.value = ''
  try {
    await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/unshare/`, { method: 'POST', body: { user_id: userId } })
    refreshMembers()
  } catch {
    shareError.value = 'Failed to remove member'
  }
}

async function setPermission(userId: string, permission: 'read' | 'write') {
  shareError.value = ''
  try {
    await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/set-permission/`, {
      method: 'POST',
      body: { user_id: userId, permission },
    })
    refreshMembers()
  } catch {
    shareError.value = 'Failed to update permission'
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
            <NuxtLink
              :to="kb?.team ? `/settings/teams/${kb.team}/knowledge-bases` : '/settings/knowledge-bases'"
              class="text-sm text-dimmed hover:text-default"
            >&larr; {{ kb?.team_name ?? 'Knowledge Bases' }}</NuxtLink>

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
                  @keydown.enter.prevent="saveDescription"
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

          <!-- Drop upload status -->
          <div v-if="dropUploads.length" class="space-y-1.5">
            <div
              v-for="(entry, i) in dropUploads"
              :key="i"
              class="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-elevated"
            >
              <UIcon
                :name="entry.status === 'uploading' ? 'i-lucide-loader-circle' : entry.status === 'done' ? 'i-lucide-circle-check' : 'i-lucide-circle-x'"
                :class="['size-4 shrink-0', entry.status === 'uploading' ? 'text-primary animate-spin' : entry.status === 'done' ? 'text-success' : 'text-error']"
              />
              <span class="truncate text-default">{{ entry.name }}</span>
              <span class="text-xs text-dimmed ml-auto shrink-0">{{ entry.status === 'uploading' ? 'Uploading…' : entry.status === 'done' ? 'Ingestion started' : 'Failed' }}</span>
            </div>
          </div>

          <!-- Sources -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-highlighted">Sources</h2>
              <NuxtLink v-if="canManage" :to="`/settings/knowledge-bases/${kbId}/sources`">
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
                    <th class="px-4 py-2.5 w-20"></th>
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
                      <div class="flex items-center justify-end gap-1">
                        <UPopover mode="hover">
                          <UButton icon="i-lucide-info" size="xs" color="neutral" variant="ghost" />
                          <template #content>
                            <div class="p-3 space-y-1.5 text-xs min-w-52">
                              <div class="flex justify-between gap-4">
                                <span class="text-dimmed">Format</span>
                                <span class="text-default font-medium uppercase">{{ source.source_type }}</span>
                              </div>
                              <div v-if="source.source_type !== 'git'" class="flex justify-between gap-4">
                                <span class="text-dimmed">File size</span>
                                <span class="text-default font-medium">{{ fmtBytes(source.file_size_bytes) }}</span>
                              </div>
                              <div class="flex justify-between gap-4">
                                <span class="text-dimmed">Chunks</span>
                                <span class="text-default font-medium">{{ source.chunk_count.toLocaleString() }}</span>
                              </div>
                              <div class="flex justify-between gap-4">
                                <span class="text-dimmed">Added</span>
                                <span class="text-default font-medium">{{ fmtDate(source.created_at) }}</span>
                              </div>
                              <template v-if="source.source_type === 'git'">
                                <div class="flex justify-between gap-4">
                                  <span class="text-dimmed">Branch</span>
                                  <span class="text-default font-medium font-mono">{{ source.git_branch }}</span>
                                </div>
                                <div v-if="source.last_synced_at" class="flex justify-between gap-4">
                                  <span class="text-dimmed">Last synced</span>
                                  <span class="text-default font-medium">{{ fmtDate(source.last_synced_at) }}</span>
                                </div>
                              </template>
                              <div v-if="source.status === 'error'" class="pt-1 border-t border-default">
                                <p class="text-error text-xs">{{ source.error_message || 'Unknown error' }}</p>
                              </div>
                            </div>
                          </template>
                        </UPopover>
                        <UButton
                          v-if="source.source_type !== 'git' && source.status === 'ready'"
                          icon="i-lucide-download"
                          size="xs"
                          color="neutral"
                          variant="ghost"
                          @click="downloadSource(source.id)"
                        />
                        <UButton
                          v-if="canManage"
                          icon="i-lucide-trash-2"
                          size="xs"
                          color="error"
                          variant="ghost"
                          @click="deleteSource(source.id)"
                        />
                      </div>
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
            <template v-if="canManage">
              <div class="flex gap-2">
                <UInput v-model="shareUsername" placeholder="Username" size="sm" class="flex-1" @keydown.enter="share" />
                <UButton size="sm" :disabled="!shareUsername" @click="share">Share</UButton>
              </div>
              <UAlert v-if="shareSuccess" color="success" :description="shareSuccess" class="mt-2" />
              <UAlert v-if="shareError" color="error" :description="shareError" class="mt-2" />
            </template>
            <div v-if="members?.length" class="mt-3 space-y-1.5">
              <div
                v-for="m in members"
                :key="m.user_id"
                class="flex items-center justify-between text-sm py-1"
              >
                <div class="flex items-center gap-2">
                  <span class="text-default">{{ m.username }}</span>
                  <UBadge v-if="m.team_role" color="neutral" variant="subtle" size="xs">{{ m.team_role }}</UBadge>
                  <UBadge v-if="m.status === 'pending'" color="info" variant="subtle" size="xs">Invited</UBadge>
                </div>
                <div class="flex items-center gap-2">
                  <USelectMenu
                    v-if="!m.is_team_member && m.status === 'accepted' && canManage"
                    :model-value="m.permission"
                    :items="[{ label: 'Read', value: 'read' }, { label: 'Read + Write', value: 'write' }]"
                    value-key="value"
                    size="xs"
                    class="w-32"
                    @update:model-value="setPermission(m.user_id, $event as 'read' | 'write')"
                  />
                  <UBadge
                    v-else
                    :color="m.permission === 'write' ? 'success' : 'neutral'"
                    variant="subtle"
                    size="xs"
                  >{{ m.permission === 'write' ? 'Read + Write' : 'Read' }}</UBadge>
                  <UButton
                    v-if="!m.is_team_member && canManage"
                    icon="i-lucide-user-minus"
                    size="xs"
                    color="error"
                    variant="ghost"
                    @click="removeMember(m.user_id)"
                  />
                </div>
              </div>
            </div>
            <p v-else class="mt-3 text-sm text-dimmed">
              <template v-if="canManage">No one has been invited yet.</template>
              <template v-else>No additional members.</template>
            </p>
          </div>

        </UContainer>
      </div>
    </template>
  </UDashboardPanel>
</template>
