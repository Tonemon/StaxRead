<script setup lang="ts">
definePageMeta({ middleware: 'admin', layout: 'admin' })
const { $api } = useNuxtApp()
const { setRefresh, clearRefresh } = useKeyboardShortcuts()

interface User { id: string; username: string; email: string; is_active: boolean; is_superuser: boolean; date_joined: string }

const { data: users, refresh } = await useFetch<User[]>('/auth/users/', {
  $fetch: $api as typeof $fetch,
  default: () => [] as User[],
})

const showCreate = ref(false)
const form = reactive({ username: '', email: '', password: '', is_superuser: false })
const submitting = ref(false)

async function createUser() {
  if (!form.username || !form.password) return
  submitting.value = true
  try {
    await ($api as typeof $fetch)('/auth/users/', { method: 'POST', body: { ...form } })
    form.username = ''
    form.email = ''
    form.password = ''
    form.is_superuser = false
    showCreate.value = false
    refresh()
  } finally {
    submitting.value = false
  }
}

async function toggleActive(user: User) {
  await ($api as typeof $fetch)(`/auth/users/${user.id}/`, { method: 'PATCH', body: { is_active: !user.is_active } })
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

        <UModal v-model:open="showCreate" title="Create User">
          <template #body>
            <div class="space-y-3">
              <UFormField label="Username"><UInput v-model="form.username" autofocus @keydown.enter="createUser" /></UFormField>
              <UFormField label="Email"><UInput v-model="form.email" type="email" @keydown.enter="createUser" /></UFormField>
              <UFormField label="Password"><UInput v-model="form.password" type="password" @keydown.enter="createUser" /></UFormField>
              <UFormField label="Superuser"><USwitch v-model="form.is_superuser" /></UFormField>
            </div>
          </template>
          <template #footer>
            <UButton :loading="submitting" :disabled="!form.username || !form.password" @click="createUser">Create</UButton>
            <UButton color="neutral" variant="ghost" @click="showCreate = false">Cancel</UButton>
          </template>
        </UModal>

        <div class="space-y-2">
          <div v-for="user in users" :key="user.id" class="flex items-center justify-between p-3 bg-default rounded-lg ring ring-default">
            <div>
              <span class="text-sm font-medium text-highlighted">{{ user.username }}</span>
              <span v-if="user.is_superuser" class="ml-2 text-xs text-warning">superuser</span>
              <p class="text-xs text-dimmed">{{ user.email }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-dimmed">{{ new Date(user.date_joined).toLocaleDateString() }}</span>
              <USwitch :model-value="user.is_active" size="xs" @update:model-value="toggleActive(user)" />
            </div>
          </div>
          <p v-if="!users?.length" class="text-dimmed text-center mt-8">No users yet.</p>
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
