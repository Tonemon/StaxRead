<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const route = useRoute()
const { $api } = useNuxtApp()

interface DocumentResponse {
  url?: string
  content?: string
  source_type: string
}

const { data: doc, error } = await useFetch<DocumentResponse>(
  `/sources/${route.params.id}/document/`,
  { $fetch: $api as typeof $fetch }
)

const iframeSrc = computed(() => {
  if (!doc.value?.url) return undefined
  const page = Number(route.query.page)
  if (doc.value.source_type === 'pdf' && Number.isFinite(page) && page > 1) {
    return `${doc.value.url}#page=${page}`
  }
  return doc.value.url
})
</script>

<template>
  <UDashboardPanel id="document" class="min-h-0" :ui="{ body: 'p-0 sm:p-0 flex flex-col' }">
    <template #header>
      <DashboardNavbar />
    </template>
    <template #body>
      <div v-if="error" class="p-6 text-error">Failed to load document.</div>
      <div v-else-if="!doc" class="p-6 text-dimmed">Loading...</div>
      <iframe v-else-if="doc.source_type === 'pdf' || doc.source_type === 'epub'" :src="iframeSrc" class="flex-1 w-full border-0" title="Document" />
      <div v-else-if="doc.source_type === 'git' && doc.content" class="flex-1 overflow-y-auto p-6">
        <pre class="whitespace-pre-wrap text-sm font-mono text-default">{{ doc.content }}</pre>
      </div>
    </template>
  </UDashboardPanel>
</template>
