<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const route = useRoute()
const { $api } = useNuxtApp()
const teamId = route.params.id as string
const authStore = useAuthStore()

interface Member {
  id: string
  username: string
  role: string
  joined_at: string
}

const { data: members, refresh } = await useFetch<Member[]>(`/teams/${teamId}/members/`, {
  $fetch: $api as typeof $fetch,
  default: () => [] as Member[],
})

const myRole = computed(() =>
  members.value?.find(m => m.username === authStore.user?.username)?.role ?? ''
)
const canManage = computed(() => ['admin', 'owner'].includes(myRole.value))
const isOwner = computed(() => myRole.value === 'owner')

const roleOptions = computed(() => {
  const all = [
    { label: 'Guest', value: 'guest' },
    { label: 'Member', value: 'member' },
    { label: 'Manager', value: 'manager' },
    { label: 'Admin', value: 'admin' },
  ]
  if (isOwner.value) all.push({ label: 'Owner', value: 'owner' })
  return all
})

const pendingRoles = ref<Record<string, string>>({})

function onRoleChange(member: Member, newRole: string) {
  pendingRoles.value[member.id] = newRole
}

function hasPendingChange(member: Member) {
  return pendingRoles.value[member.id] !== undefined && pendingRoles.value[member.id] !== member.role
}

async function saveRole(member: Member) {
  const newRole = pendingRoles.value[member.id]
  if (!newRole) return
  await ($api as typeof $fetch)(`/teams/${teamId}/members/${member.id}/`, {
    method: 'PATCH',
    body: { role: newRole },
  })
  delete pendingRoles.value[member.id]
  refresh()
}

async function removeMember(member: Member) {
  await ($api as typeof $fetch)(`/teams/${teamId}/members/${member.id}/`, { method: 'DELETE' })
  refresh()
}

const inviteUsername = ref('')
const inviteError = ref('')
const inviteSuccess = ref('')

async function invite() {
  inviteError.value = ''
  inviteSuccess.value = ''
  try {
    const users = await ($api as typeof $fetch)<{ id: string; username: string }[]>('/auth/users/')
    const target = users.find(u => u.username === inviteUsername.value)
    if (!target) { inviteError.value = 'User not found'; return }
    await ($api as typeof $fetch)(`/teams/${teamId}/members/`, {
      method: 'POST',
      body: { user_id: target.id, role: 'member' },
    })
    inviteSuccess.value = `${inviteUsername.value} added as Member.`
    inviteUsername.value = ''
    refresh()
  } catch (e: any) {
    inviteError.value = e?.data?.detail ?? 'Failed to add member'
  }
}

const ROLE_DESCRIPTIONS = [
  { role: 'Guest', desc: 'Read-only access to explicitly assigned Knowledge Bases.' },
  { role: 'External', desc: 'Same as Guest, but for users outside the team invited to specific KBs.' },
  { role: 'Member', desc: 'Can edit sources and KB properties on assigned Knowledge Bases.' },
  { role: 'Manager', desc: 'Implicit access to all team KBs. Can create/delete KBs, manage API tokens and Git credentials.' },
  { role: 'Admin', desc: 'All Manager permissions. Can manage team members and roles (up to Admin), and edit team settings.' },
  { role: 'Owner', desc: 'Full control. One per team. Can transfer ownership and delete the team.' },
]
</script>

<template>
  <UDashboardPanel id="team-members" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header><DashboardNavbar /></template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-6 py-6">
        <div>
          <NuxtLink :to="`/settings/teams/${teamId}/general`" class="text-sm text-dimmed hover:text-default">&larr; Team Settings</NuxtLink>
          <h1 class="text-2xl font-bold text-highlighted mt-2">Members</h1>
        </div>

        <div v-if="canManage" class="space-y-2">
          <h2 class="text-sm font-semibold text-dimmed uppercase tracking-wider">Add member</h2>
          <div class="flex gap-2">
            <UInput v-model="inviteUsername" placeholder="Username" size="sm" class="flex-1" @keydown.enter="invite" />
            <UButton size="sm" :disabled="!inviteUsername" @click="invite">Add</UButton>
          </div>
          <UAlert v-if="inviteSuccess" color="success" :description="inviteSuccess" />
          <UAlert v-if="inviteError" color="error" :description="inviteError" />
        </div>

        <div class="space-y-3">
          <h2 class="text-sm font-semibold text-dimmed uppercase tracking-wider">Users</h2>
          <div class="border border-default rounded-lg overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-elevated border-b border-default">
                  <th class="px-4 py-2.5 text-left text-xs font-semibold text-dimmed uppercase tracking-wider">User</th>
                  <th class="px-4 py-2.5 text-left text-xs font-semibold text-dimmed uppercase tracking-wider">Role</th>
                  <th class="px-4 py-2.5 text-left text-xs font-semibold text-dimmed uppercase tracking-wider">Joined</th>
                  <th class="px-4 py-2.5 w-24"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-default">
                <tr v-for="m in members" :key="m.id" class="hover:bg-elevated/50 transition-colors">
                  <td class="px-4 py-3 font-medium text-highlighted">{{ m.username }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <USelectMenu
                        :model-value="pendingRoles[m.id] ?? m.role"
                        :items="roleOptions"
                        value-key="value"
                        size="xs"
                        class="w-32"
                        :disabled="!canManage || m.role === 'owner'"
                        @update:model-value="(val: string) => onRoleChange(m, val)"
                      />
                      <UButton
                        v-if="hasPendingChange(m)"
                        size="xs"
                        color="primary"
                        @click="saveRole(m)"
                      >
                        Save
                      </UButton>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-muted text-xs">
                    {{ new Date(m.joined_at).toLocaleDateString() }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <UButton
                      v-if="canManage && m.role !== 'owner'"
                      icon="i-lucide-user-minus"
                      size="xs"
                      color="error"
                      variant="ghost"
                      @click="removeMember(m)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <UAccordion
          :items="[{ label: 'Role descriptions', slot: 'roles' }]"
          class="border-t border-default pt-4"
        >
          <template #roles>
            <div class="space-y-2 py-2">
              <div v-for="r in ROLE_DESCRIPTIONS" :key="r.role" class="flex gap-3 text-sm">
                <span class="font-medium text-highlighted w-20 shrink-0">{{ r.role }}</span>
                <span class="text-muted">{{ r.desc }}</span>
              </div>
            </div>
          </template>
        </UAccordion>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
