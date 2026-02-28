<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const teamId = route.params.id as string
const authStore = useAuthStore()
const origin = useRequestURL().origin

// ── Types ──────────────────────────────────────────────────────────────────

interface Member { username: string; role: string }

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

const { data: members } = await useFetch<Member[]>(`/teams/${teamId}/members/`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as Member[],
})

const canManage = computed(() => {
  const role = members.value?.find(m => m.username === authStore.user?.username)?.role ?? ''
  return ['manager', 'admin', 'owner'].includes(role)
})

const { data: tokens, refresh } = await useFetch<APIToken[]>(`/teams/${teamId}/api-tokens/`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as APIToken[],
})

const { data: kbs } = await useFetch<KBOption[]>(`/knowledge-bases/?team=${teamId}`, {
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
    const result = await ($api as typeof $fetch)<APIToken & { token: string }>(`/teams/${teamId}/api-tokens/`, {
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
  await ($api as typeof $fetch)(`/teams/${teamId}/api-tokens/${token.id}/`, {
    method: 'PATCH',
    body: { is_active: !token.is_active },
  })
  refresh()
}

// ── Delete ─────────────────────────────────────────────────────────────────

const deleteTargetId = ref<string | null>(null)

async function doDelete() {
  if (!deleteTargetId.value) return
  await ($api as typeof $fetch)(`/teams/${teamId}/api-tokens/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}

function onDeleteModalUpdate(open: boolean) {
  if (!open) deleteTargetId.value = null
}

// ── Helpers ────────────────────────────────────────────────────────────────

function scopeLabel(token: APIToken): string {
  if (!token.knowledge_bases.length) return 'All team KBs'
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

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const el = document.createElement('textarea')
    el.value = text
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
}

const usageTabs = computed(() => [
  { label: 'CURL', slot: 'curl' as const },
  { label: 'WGET', slot: 'wget' as const },
  { label: 'Python', slot: 'python' as const },
])
</script>

<template>
  <UDashboardPanel id="team-api-tokens" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header><DashboardNavbar /></template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6">

        <!-- Header -->
        <div>
          <NuxtLink :to="`/settings/teams/${teamId}/general`" class="text-sm text-dimmed hover:text-default">&larr; Team Settings</NuxtLink>
          <div class="flex items-center justify-between mt-2">
            <div>
              <h1 class="text-2xl font-bold text-highlighted">Team API Tokens</h1>
              <p class="text-sm text-dimmed mt-0.5">
                Service account tokens for external applications to search this team's knowledge bases.
              </p>
            </div>
            <UButton v-if="canManage" icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">
              New Token
            </UButton>
          </div>
        </div>

        <!-- Service account info banner -->
        <UAlert
          color="info"
          variant="soft"
          icon="i-lucide-info"
          title="Service account tokens"
          description="These tokens are scoped to this team's knowledge bases. They are not tied to any individual user account."
        />

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
                @click="copyToClipboard(newToken!)"
              />
            </div>
          </template>
        </UAlert>

        <!-- Active tokens table -->
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
                      <div v-if="canManage" class="flex items-center gap-1.5">
                        <span class="text-xs text-dimmed">{{ token.is_active ? 'Active' : 'Disabled' }}</span>
                        <USwitch
                          :model-value="token.is_active"
                          size="xs"
                          @update:model-value="toggleActive(token)"
                        />
                      </div>
                      <UButton
                        v-if="canManage"
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
          <p class="text-sm text-muted">
            Send a <code class="text-xs font-mono bg-elevated px-1.5 py-0.5 rounded">POST</code> request to
            <code class="text-xs font-mono bg-elevated px-1.5 py-0.5 rounded">{{ origin }}/api/external/search/</code>
            with your token in the <code class="text-xs font-mono bg-elevated px-1.5 py-0.5 rounded">Authorization</code> header:
          </p>
          <UTabs :items="usageTabs">
            <template #curl>
              <pre class="text-xs font-mono bg-elevated p-4 rounded overflow-x-auto mt-2">curl -X POST {{ origin }}/api/external/search/ \
  -H "Authorization: Bearer &lt;your-token&gt;" \
  -H "Content-Type: application/json" \
  -d '{
  "query": "your search query",
  "kb_ids": ["optional-kb-uuid"],
  "limit": 10
}'</pre>
            </template>
            <template #wget>
              <pre class="text-xs font-mono bg-elevated p-4 rounded overflow-x-auto mt-2">wget -qO- {{ origin }}/api/external/search/ \
  --method=POST \
  --header="Authorization: Bearer &lt;your-token&gt;" \
  --header="Content-Type: application/json" \
  --body-data='{
  "query": "your search query",
  "kb_ids": ["optional-kb-uuid"],
  "limit": 10
}'</pre>
            </template>
            <template #python>
              <pre class="text-xs font-mono bg-elevated p-4 rounded overflow-x-auto mt-2">import requests

response = requests.post(
    "{{ origin }}/api/external/search/",
    headers={
        "Authorization": "Bearer &lt;your-token&gt;",
        "Content-Type": "application/json",
    },
    json={
        "query": "your search query",
        "kb_ids": ["optional-kb-uuid"],  # optional
        "limit": 10,
    },
)
results = response.json()</pre>
            </template>
          </UTabs>
        </div>

      </UContainer>
    </template>
  </UDashboardPanel>

  <!-- Create token modal -->
  <UModal v-model:open="showCreate" title="New Team API Token">
    <template #body>
      <div class="space-y-4">
        <UFormField label="Token name" required>
          <UInput v-model="form.name" autofocus placeholder="e.g. CI Pipeline" @keydown.enter="createToken" />
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
            placeholder="All team knowledge bases (default)"
            class="w-full"
          />
          <p class="text-xs text-dimmed mt-1">Leave empty to grant access to all team knowledge bases.</p>
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
