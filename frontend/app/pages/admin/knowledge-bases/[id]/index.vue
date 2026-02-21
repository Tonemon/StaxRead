<script setup lang="ts">
definePageMeta({ middleware: "admin", layout: "admin" })
const route = useRoute()
const { $api } = useNuxtApp()
const kbId = route.params.id as string

interface KB {
  id: string
  name: string
  description: string
  owner: string
  owner_username: string
}

interface Source {
  id: string
  title: string
  source_type: string
  status: string
  git_url: string
  created_at: string
}

const { data: kb } = await useFetch<KB>(`/knowledge-bases/${kbId}/`, {
  $fetch: $api as typeof $fetch,
})

const { data: sources, refresh: refreshSources } = await useFetch<Source[]>("/sources/", {
  $fetch: $api as typeof $fetch,
  query: { kb: kbId },
  default: () => [] as Source[],
})

// Share management
const shareUsername = ref("")
const shareError = ref("")

async function share() {
  shareError.value = ""
  try {
    // Need user_id — look up by username via users list
    const users = await ($api as typeof $fetch)<{ id: string; username: string }[]>("/auth/users/")
    const target = users.find((u) => u.username === shareUsername.value)
    if (!target) { shareError.value = "User not found"; return }
    await ($api as typeof $fetch)(`/knowledge-bases/${kbId}/share/`, {
      method: "POST",
      body: { user_id: target.id },
    })
    shareUsername.value = ""
  } catch {
    shareError.value = "Failed to share"
  }
}

const statusColors: Record<string, string> = {
  pending: "warning",
  processing: "info",
  ready: "success",
  error: "error",
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <NuxtLink to="/admin/knowledge-bases" class="text-sm text-gray-400 hover:text-gray-600">&larr; Knowledge Bases</NuxtLink>
      <h1 class="text-2xl font-bold mt-2 text-gray-900 dark:text-white">{{ kb?.name }}</h1>
      <p v-if="kb?.description" class="text-sm text-gray-500 mt-1">{{ kb.description }}</p>
    </div>

    <!-- Sources -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold">Sources</h2>
        <NuxtLink :to="`/admin/knowledge-bases/${kbId}/sources`">
          <UButton size="sm" icon="i-heroicons-plus">Add Source</UButton>
        </NuxtLink>
      </div>
      <div class="space-y-2">
        <div
          v-for="source in sources"
          :key="source.id"
          class="flex items-center justify-between p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
        >
          <div>
            <span class="text-sm font-medium">{{ source.title }}</span>
            <span class="text-xs text-gray-400 ml-2">{{ source.source_type }}</span>
          </div>
          <UBadge :color="statusColors[source.status] || 'neutral'" size="xs">{{ source.status }}</UBadge>
        </div>
        <p v-if="!sources?.length" class="text-sm text-gray-400">No sources yet.</p>
      </div>
    </div>

    <!-- Share management -->
    <div>
      <h2 class="text-lg font-semibold mb-3">Share Access</h2>
      <div class="flex gap-2">
        <UInput v-model="shareUsername" placeholder="Username" size="sm" class="flex-1" />
        <UButton size="sm" @click="share" :disabled="!shareUsername">Share</UButton>
      </div>
      <UAlert v-if="shareError" color="error" :description="shareError" class="mt-2" />
    </div>
  </div>
</template>
