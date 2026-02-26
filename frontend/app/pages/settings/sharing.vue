<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const { $api } = useNuxtApp()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

// ── Types ──────────────────────────────────────────────────────────────────

interface KBOption { id: string; name: string }

interface APIToken {
  id: string
  name: string
  description: string
  token_prefix: string
  knowledge_bases: { id: string; name: string }[]
  is_active: boolean
  created_at: string
  last_used_at: string | null
  last_used_ip: string | null
  expires_at: string | null
}

// ── Data ───────────────────────────────────────────────────────────────────

const { data: tokens, refresh } = await useFetch<APIToken[]>('/api-tokens/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as APIToken[],
})

const { data: kbs } = await useFetch<KBOption[]>('/knowledge-bases/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as KBOption[],
})

// ── Create modal ───────────────────────────────────────────────────────────

const showCreate = ref(false)
const submitting = ref(false)
const newToken = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
  kb_ids: [] as string[],
  expires_in_days: null as number | null,
})

const expiryOptions = [
  { label: 'No expiry', value: null },
  { label: '7 days',    value: 7 },
  { label: '30 days',   value: 30 },
  { label: '90 days',   value: 90 },
  { label: '1 year',    value: 365 },
]

const kbOptions = computed(() =>
  (kbs.value || []).map(kb => ({ label: kb.name, value: kb.id }))
)

function resetForm() {
  form.name = ''
  form.description = ''
  form.kb_ids = []
  form.expires_in_days = null
}

async function createToken() {
  if (!form.name) return
  submitting.value = true
  try {
    const result = await ($api as typeof $fetch)<APIToken & { token: string }>('/api-tokens/', {
      method: 'POST',
      body: {
        name: form.name,
        description: form.description,
        kb_ids: form.kb_ids,
        expires_in_days: form.expires_in_days,
      },
    })
    newToken.value = result.token
    showCreate.value = false
    resetForm()
    refresh()
  } finally {
    submitting.value = false
  }
}

// ── Toggle active ──────────────────────────────────────────────────────────

async function toggleActive(token: APIToken) {
  await ($api as typeof $fetch)(`/api-tokens/${token.id}/`, {
    method: 'PATCH',
    body: { is_active: !token.is_active },
  })
  refresh()
}

// ── Delete ─────────────────────────────────────────────────────────────────

const deleteTargetId = ref<string | null>(null)

async function doDelete() {
  if (!deleteTargetId.value) return
  await ($api as typeof $fetch)(`/api-tokens/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}

function onDeleteModalUpdate(open: boolean) {
  if (!open) deleteTargetId.value = null
}

// ── Helpers ────────────────────────────────────────────────────────────────

function scopeLabel(token: APIToken): string {
  if (!token.knowledge_bases.length) return 'All knowledge bases'
  return token.knowledge_bases.map(kb => kb.name).join(', ')
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function fmtDateTime(iso: string | null): string {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => setRefresh(refresh))
onUnmounted(clearRefresh)
</script>

<template>
  <UDashboardPanel id="sharing" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6">

        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-highlighted">Sharing</h1>
            <p class="text-sm text-dimmed mt-0.5">
              API tokens allow external applications to search your knowledge bases.
            </p>
          </div>
          <UButton icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">
            New Token
          </UButton>
        </div>

        <!-- New-token-revealed banner -->
        <UAlert
          v-if="newToken"
          color="success"
          variant="soft"
          title="Token created — copy it now"
          :close-button="{ icon: 'i-lucide-x', color: 'neutral', variant: 'link' }"
          @close="newToken = null"
        >
          <template #description>
            <p class="text-xs text-muted mb-2">This token will not be shown again.</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 text-xs font-mono bg-elevated px-3 py-2 rounded break-all select-all">{{ newToken }}</code>
              <UButton
                size="xs"
                color="neutral"
                variant="outline"
                icon="i-lucide-copy"
                @click="() => navigator.clipboard.writeText(newToken!)"
              />
            </div>
          </template>
        </UAlert>

        <!-- Active API tokens section -->
        <div class="space-y-3">
          <h2 class="text-sm font-semibold text-dimmed uppercase tracking-wider">Active API Tokens</h2>

          <div v-if="tokens?.length" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-default">
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Token name</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Description</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Scope</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Created</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Last used</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Last used IP</th>
                  <th class="text-left py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Expires</th>
                  <th class="text-right py-2 px-3 text-xs font-semibold text-dimmed uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-default">
                <tr v-for="token in tokens" :key="token.id">
                  <td class="py-3 px-3">
                    <div>
                      <p class="font-medium text-highlighted">{{ token.name }}</p>
                      <p class="text-xs font-mono text-dimmed mt-0.5">{{ token.token_prefix }}…</p>
                    </div>
                  </td>
                  <td class="py-3 px-3 text-muted max-w-[160px] truncate">{{ token.description || '—' }}</td>
                  <td class="py-3 px-3">
                    <UBadge color="neutral" variant="subtle" size="xs">
                      {{ scopeLabel(token) }}
                    </UBadge>
                  </td>
                  <td class="py-3 px-3 text-muted whitespace-nowrap">{{ fmtDate(token.created_at) }}</td>
                  <td class="py-3 px-3 text-muted whitespace-nowrap">{{ fmtDateTime(token.last_used_at) }}</td>
                  <td class="py-3 px-3 text-muted font-mono text-xs">{{ token.last_used_ip || '—' }}</td>
                  <td class="py-3 px-3 text-muted whitespace-nowrap">
                    <span v-if="!token.expires_at">Never</span>
                    <span v-else-if="new Date(token.expires_at) < new Date()" class="text-error text-xs">Expired</span>
                    <span v-else>{{ fmtDate(token.expires_at) }}</span>
                  </td>
                  <td class="py-3 px-3">
                    <div class="flex items-center justify-end gap-3">
                      <div class="flex items-center gap-1.5">
                        <span class="text-xs text-dimmed">{{ token.is_active ? 'Active' : 'Disabled' }}</span>
                        <USwitch
                          :model-value="token.is_active"
                          size="xs"
                          @update:model-value="toggleActive(token)"
                        />
                      </div>
                      <UButton
                        size="xs"
                        color="error"
                        variant="ghost"
                        icon="i-lucide-trash"
                        @click="deleteTargetId = token.id"
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-else class="text-dimmed text-center py-8">No API tokens yet.</p>
        </div>

        <!-- Usage docs -->
        <div class="space-y-3 border-t border-default pt-6">
          <h2 class="text-sm font-semibold text-dimmed uppercase tracking-wider">How to use</h2>
          <div class="space-y-2 text-sm text-muted">
            <p>Send a <code class="text-xs font-mono bg-elevated px-1.5 py-0.5 rounded">POST</code> request to the external search endpoint:</p>
            <pre class="text-xs font-mono bg-elevated p-4 rounded overflow-x-auto">POST /api/external/search/
Authorization: Bearer &lt;your-token&gt;
Content-Type: application/json

{
  "query": "your search query",
  "kb_ids": ["optional-kb-uuid"],
  "limit": 10
}</pre>
          </div>
        </div>

      </UContainer>
    </template>
  </UDashboardPanel>

  <!-- Create token modal -->
  <UModal v-model:open="showCreate" title="New API Token">
    <template #body>
      <div class="space-y-4">
        <UFormField label="Token name" required>
          <UInput v-model="form.name" autofocus placeholder="e.g. My App Integration" @keydown.enter="createToken" />
        </UFormField>
        <UFormField label="Description">
          <UInput v-model="form.description" placeholder="Optional description" @keydown.enter="createToken" />
        </UFormField>
        <UFormField label="Knowledge base scope">
          <USelectMenu
            v-model="form.kb_ids"
            :items="kbOptions"
            value-key="value"
            multiple
            placeholder="All knowledge bases (default)"
            class="w-full"
          />
          <p class="text-xs text-dimmed mt-1">Leave empty to grant access to all your knowledge bases.</p>
        </UFormField>
        <UFormField label="Expiry">
          <USelectMenu
            v-model="form.expires_in_days"
            :items="expiryOptions"
            value-key="value"
            class="w-full"
          />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <UButton :loading="submitting" :disabled="!form.name" @click="createToken">Create Token</UButton>
      <UButton color="neutral" variant="ghost" @click="showCreate = false; resetForm()">Cancel</UButton>
    </template>
  </UModal>

  <!-- Delete confirm modal -->
  <UModal :open="!!deleteTargetId" title="Delete API Token" @update:open="onDeleteModalUpdate">
    <template #body>
      <p class="text-sm text-muted">
        Are you sure you want to delete this token? Any applications using it will immediately lose access.
      </p>
    </template>
    <template #footer>
      <UButton color="error" @click="doDelete">Delete</UButton>
      <UButton color="neutral" variant="ghost" @click="deleteTargetId = null">Cancel</UButton>
    </template>
  </UModal>
</template>
