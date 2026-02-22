<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const isAdmin = computed(() => route.path.startsWith('/admin'))
</script>

<template>
  <UDashboardNavbar
    class="sticky lg:absolute top-0 inset-x-0 border-b-0 z-10 bg-default/75 backdrop-blur lg:bg-transparent lg:backdrop-blur-none pointer-events-none sm:px-4"
    :ui="{ left: 'pointer-events-auto', right: 'pointer-events-auto' }"
  >
    <template #left>
      <UDashboardSidebarCollapse />
      <UButton
        v-if="isAdmin"
        color="neutral"
        variant="ghost"
        icon="i-lucide-arrow-left"
        size="sm"
        @click="router.back()"
      >
        Back
      </UButton>
    </template>
    <template #right>
      <UColorModeButton />
      <UButton
        color="neutral"
        variant="ghost"
        icon="i-lucide-search"
        to="/"
        class="lg:hidden"
      />
    </template>
  </UDashboardNavbar>
</template>
