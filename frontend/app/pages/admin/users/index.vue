<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'superadmin' })
const { $api } = useNuxtApp()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

interface User {
  id: string; username: string; email: string
  first_name: string; last_name: string
  is_active: boolean; is_superuser: boolean
  show_greeting: boolean; greeting_display: string
  date_joined: string
}

const { data: users, refresh } = await useFetch<User[]>('/auth/users/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as User[],
})

// ── Create ──────────────────────────────────────────────────────────────────

const showCreate = ref(false)
const createForm = reactive({ username: '', email: '', password: '', is_superuser: false })
const createSubmitting = ref(false)

async function createUser() {
  if (!createForm.username || !createForm.password) return
  createSubmitting.value = true
  try {
    await ($api as typeof $fetch)('/auth/users/', { method: 'POST', body: { ...createForm } })
    createForm.username = ''
    createForm.email = ''
    createForm.password = ''
    createForm.is_superuser = false
    showCreate.value = false
    refresh()
  } finally {
    createSubmitting.value = false
  }
}

// ── Edit ────────────────────────────────────────────────────────────────────

const editTarget = ref<User | null>(null)
const editForm = reactive({
  username: '', email: '', password: '',
  first_name: '', last_name: '',
  is_active: true, is_superuser: false,
  show_greeting: true, greeting_display: 'username',
})
const editSubmitting = ref(false)

const greetingDisplayOptions = [
  { label: 'Username', value: 'username' },
  { label: 'First name', value: 'first_name' },
  { label: 'Full name', value: 'full_name' },
]

function openEdit(user: User) {
  editTarget.value = user
  editForm.username = user.username
  editForm.email = user.email
  editForm.password = ''
  editForm.first_name = user.first_name
  editForm.last_name = user.last_name
  editForm.is_active = user.is_active
  editForm.is_superuser = user.is_superuser
  editForm.show_greeting = user.show_greeting
  editForm.greeting_display = user.greeting_display
}

async function saveEdit() {
  if (!editTarget.value) return
  editSubmitting.value = true
  try {
    const body: Record<string, unknown> = {
      username: editForm.username,
      email: editForm.email,
      first_name: editForm.first_name,
      last_name: editForm.last_name,
      is_active: editForm.is_active,
      is_superuser: editForm.is_superuser,
      show_greeting: editForm.show_greeting,
      greeting_display: editForm.greeting_display,
    }
    if (editForm.password) body.password = editForm.password
    await ($api as typeof $fetch)(`/auth/users/${editTarget.value.id}/`, { method: 'PATCH', body })
    editTarget.value = null
    refresh()
  } finally {
    editSubmitting.value = false
  }
}

// ── Delete ──────────────────────────────────────────────────────────────────

const deleteTargetId = ref<string | null>(null)

async function doDelete() {
  if (!deleteTargetId.value) return
  await ($api as typeof $fetch)(`/auth/users/${deleteTargetId.value}/`, { method: 'DELETE' })
  deleteTargetId.value = null
  refresh()
}

onMounted(() => setRefresh(refresh))
onUnmounted(clearRefresh)
</script>

<template>
  <UDashboardPanel id="users" class="min-h-0" :ui="{ body: 'p-0 sm:p-0' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-highlighted">Users</h1>
          <UButton icon="i-lucide-plus" color="neutral" variant="outline" @click="showCreate = true">New User</UButton>
        </div>

        <!-- Users list -->
        <div class="space-y-2">
          <div
            v-for="user in users"
            :key="user.id"
            class="flex items-center justify-between p-3 bg-default rounded-lg ring ring-default cursor-pointer hover:bg-elevated/50 transition-colors"
            @click="openEdit(user)"
          >
            <div>
              <span class="text-sm font-medium text-highlighted">{{ user.username }}</span>
              <span v-if="user.is_superuser" class="ml-2 text-xs text-warning">superuser</span>
              <p class="text-xs text-dimmed">{{ user.email || '—' }}</p>
            </div>
            <div class="flex items-center gap-3" @click.stop>
              <span class="text-xs text-dimmed">{{ new Date(user.date_joined).toLocaleDateString() }}</span>
              <USwitch :model-value="user.is_active" size="xs" @update:model-value="($api as typeof $fetch)(`/auth/users/${user.id}/`, { method: 'PATCH', body: { is_active: !user.is_active } }).then(refresh)" />
              <UButton size="xs" color="error" variant="ghost" icon="i-lucide-trash-2" @click="deleteTargetId = user.id" />
            </div>
          </div>
          <p v-if="!users?.length" class="text-dimmed text-center mt-8">No users yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>

  <!-- Create modal -->
  <UModal v-model:open="showCreate" title="Create User">
    <template #body>
      <div class="space-y-3">
        <UFormField label="Username" required><UInput v-model="createForm.username" autofocus @keydown.enter="createUser" /></UFormField>
        <UFormField label="Email"><UInput v-model="createForm.email" type="email" @keydown.enter="createUser" /></UFormField>
        <UFormField label="Password" required><UInput v-model="createForm.password" type="password" @keydown.enter="createUser" /></UFormField>
        <UFormField label="Superuser"><USwitch v-model="createForm.is_superuser" /></UFormField>
      </div>
    </template>
    <template #footer>
      <UButton :loading="createSubmitting" :disabled="!createForm.username || !createForm.password" @click="createUser">Create</UButton>
      <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
    </template>
  </UModal>

  <!-- Edit modal -->
  <UModal :open="!!editTarget" title="Edit User" @update:open="(v) => { if (!v) editTarget = null }">
    <template #body>
      <div class="space-y-4">
        <p class="text-xs font-semibold text-dimmed uppercase tracking-wider">Account</p>
        <div class="space-y-3">
          <UFormField label="Username"><UInput v-model="editForm.username" /></UFormField>
          <UFormField label="Email"><UInput v-model="editForm.email" type="email" /></UFormField>
          <UFormField label="New password" description="Leave blank to keep current password">
            <UInput v-model="editForm.password" type="password" placeholder="New password" />
          </UFormField>
          <div class="flex gap-6">
            <UFormField label="Active"><USwitch v-model="editForm.is_active" /></UFormField>
            <UFormField label="Superuser"><USwitch v-model="editForm.is_superuser" /></UFormField>
          </div>
        </div>

        <p class="text-xs font-semibold text-dimmed uppercase tracking-wider pt-2 border-t border-default">Preferences</p>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="First name"><UInput v-model="editForm.first_name" /></UFormField>
            <UFormField label="Last name"><UInput v-model="editForm.last_name" /></UFormField>
          </div>
          <UFormField label="Display name">
            <USelectMenu
              v-model="editForm.greeting_display"
              :items="greetingDisplayOptions"
              value-key="value"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Show greeting on home page"><USwitch v-model="editForm.show_greeting" /></UFormField>
        </div>
      </div>
    </template>
    <template #footer>
      <UButton :loading="editSubmitting" :disabled="!editForm.username" @click="saveEdit">Save</UButton>
      <UButton color="neutral" variant="ghost" @click="editTarget = null">Cancel</UButton>
    </template>
  </UModal>

  <!-- Delete confirm modal -->
  <UModal :open="!!deleteTargetId" title="Delete User" @update:open="(v) => { if (!v) deleteTargetId = null }">
    <template #body>
      <p class="text-sm text-muted">Are you sure you want to delete this user? This cannot be undone.</p>
    </template>
    <template #footer>
      <UButton color="error" @click="doDelete">Delete</UButton>
      <UButton color="neutral" variant="ghost" @click="deleteTargetId = null">Cancel</UButton>
    </template>
  </UModal>
</template>
