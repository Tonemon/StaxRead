<script setup lang="ts">
definePageMeta({ middleware: "auth" })
const route = useRoute()
const { $api } = useNuxtApp()

interface DocumentResponse {
  url?: string
  content?: string
  file?: string
  source_type: string
  title?: string
}

const { data: doc, error } = await useFetch<DocumentResponse>(
  `/sources/${route.params.id}/document/`,
  {
    $fetch: $api as typeof $fetch,
  }
)
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="border-b border-gray-200 dark:border-gray-800 p-4 bg-white dark:bg-gray-900">
      <NuxtLink to="/search" class="text-sm text-gray-400 hover:text-gray-600">&larr; Back to search</NuxtLink>
    </div>
    <div class="flex-1 overflow-hidden">
      <div v-if="error" class="p-6 text-red-500">Failed to load document.</div>
      <div v-else-if="!doc" class="p-6 text-gray-400">Loading...</div>
      <!-- PDF: open in iframe via presigned URL -->
      <iframe
        v-else-if="doc.source_type === 'pdf'"
        :src="doc.url"
        class="w-full h-full border-0"
        title="PDF document"
      />
      <!-- EPUB: open in iframe via presigned URL -->
      <iframe
        v-else-if="doc.source_type === 'epub'"
        :src="doc.url"
        class="w-full h-full border-0"
        title="EPUB document"
      />
      <!-- Git: render markdown -->
      <div
        v-else-if="doc.source_type === 'git' && doc.content"
        class="p-6 overflow-y-auto h-full prose dark:prose-invert max-w-none"
      >
        <!-- eslint-disable-next-line vue/no-v-html -->
        <pre class="whitespace-pre-wrap text-sm">{{ doc.content }}</pre>
      </div>
    </div>
  </div>
</template>
