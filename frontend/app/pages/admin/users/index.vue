<script setup lang="ts">
definePageMeta({ middleware: "admin", layout: "admin" })
const { $api } = useNuxtApp()

interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  date_joined: string
}

const { data: users, refresh } = await useFetch<User[]>("/auth/users/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as User[],
})

const showCreate = ref(false)
const form = reactive({ username: "", email: "", password: "", is_superuser: false })
const submitting = ref(false)

async function createUser() {
  submitting.value = true
  try {
    await ($api as typeof $fetch)("/auth/users/", {
      method: "POST",
      body: { ...form },
    })
    form.username = ""
    form.email = ""
    form.password = ""
    form.is_superuser = false
    showCreate.value = false
    refresh()
  } finally {
    submitting.value = false
  }
}

async function toggleActive(user: User) {
  await ($api as typeof $fetch)(`/auth/users/${user.id}/`, {
    method: "PATCH",
    body: { is_active: !user.is_active },
  })
  refresh()
}
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Users</h1>
      <UButton @click="showCreate = true" icon="i-heroicons-plus">New User</UButton>
    </div>

    <UModal v-model:open="showCreate" title="Create User">
      <template #body>
        <div class="space-y-3">
          <UFormField label="Username">
            <UInput v-model="form.username" autofocus />
          </UFormField>
          <UFormField label="Email">
            <UInput v-model="form.email" type="email" />
          </UFormField>
          <UFormField label="Password">
            <UInput v-model="form.password" type="password" />
          </UFormField>
          <UFormField label="Superuser">
            <UToggle v-model="form.is_superuser" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <UButton :loading="submitting" :disabled="!form.username || !form.password" @click="createUser">Create</UButton>
        <UButton variant="ghost" @click="showCreate = false">Cancel</UButton>
      </template>
    </UModal>

    <UTable
      :data="users || []"
      :columns="[
        { key: 'username', label: 'Username' },
        { key: 'email', label: 'Email' },
        { key: 'is_superuser', label: 'Superuser' },
        { key: 'is_active', label: 'Active' },
        { key: 'actions', label: '' },
      ]"
    >
      <template #is_superuser-data="{ row }">
        <UBadge v-if="row.is_superuser" color="warning" size="xs">Superuser</UBadge>
      </template>
      <template #is_active-data="{ row }">
        <UToggle :model-value="row.is_active" @update:model-value="toggleActive(row)" size="xs" />
      </template>
      <template #actions-data="{ row }">
        <span class="text-xs text-gray-400">{{ new Date(row.date_joined).toLocaleDateString() }}</span>
      </template>
    </UTable>
  </div>
</template>
