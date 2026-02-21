<script setup lang="ts">
definePageMeta({ middleware: "admin", layout: "admin" })
const { $api } = useNuxtApp()

interface KB {
  id: string
  name: string
  description: string
  owner_username: string
  created_at: string
}

const { data: kbs, refresh } = await useFetch<KB[]>("/knowledge-bases/", {
  $fetch: $api as typeof $fetch,
  default: () => [] as KB[],
})

const showCreate = ref(false)
const form = reactive({ name: "", description: "" })

async function createKB() {
  await ($api as typeof $fetch)("/knowledge-bases/", {
    method: "POST",
    body: { name: form.name, description: form.description },
  })
  form.name = ""
  form.description = ""
  showCreate.value = false
  refresh()
}

async function deleteKB(id: string) {
  await ($api as typeof $fetch)(`/knowledge-bases/${id}/`, { method: "DELETE" })
  refresh()
}
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Bases</h1>
      <UButton @click="showCreate = true" icon="i-heroicons-plus">New KB</UButton>
    </div>

    <UModal v-model:open="showCreate" title="Create Knowledge Base">
      <template #body>
        <div class="space-y-3">
          <UFormField label="Name">
            <UInput v-model="form.name" placeholder="My KB" autofocus />
          </UFormField>
          <UFormField label="Description">
            <UTextarea v-model="form.description" placeholder="Optional description" :rows="2" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <UButton @click="createKB" :disabled="!form.name">Create</UButton>
        <UButton variant="ghost" @click="showCreate = false">Cancel</UButton>
      </template>
    </UModal>

    <div class="space-y-3">
      <div
        v-for="kb in kbs"
        :key="kb.id"
        class="flex items-center justify-between p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
      >
        <div>
          <NuxtLink :to="`/admin/knowledge-bases/${kb.id}`" class="font-medium hover:underline">
            {{ kb.name }}
          </NuxtLink>
          <p class="text-xs text-gray-400 mt-0.5">Owner: {{ kb.owner_username }}</p>
          <p v-if="kb.description" class="text-sm text-gray-500 mt-1">{{ kb.description }}</p>
        </div>
        <UButton size="xs" variant="ghost" color="error" icon="i-heroicons-trash" @click="deleteKB(kb.id)" />
      </div>
      <p v-if="!kbs?.length" class="text-gray-400 text-center mt-8">No knowledge bases yet.</p>
    </div>
  </div>
</template>
