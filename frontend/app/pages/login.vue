<script setup lang="ts">
definePageMeta({ layout: false })
const { login } = useAuth()
const route = useRoute()
const form = reactive({ username: '', password: '' })
const error = ref('')
const loading = ref(false)
const sessionExpired = computed(() => route.query.session_expired === '1')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await login(form.username, form.password)
  } catch {
    error.value = 'Invalid credentials'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
    <UCard class="w-full max-w-sm">
      <template #header>
        <div class="flex items-center gap-2 justify-center">
          <Logo class="h-8 w-auto" />
          <span class="text-xl font-bold text-highlighted">StaxRead</span>
        </div>
      </template>
      <form @submit.prevent="submit" class="space-y-4">
        <UFormField label="Username">
          <UInput v-model="form.username" autocomplete="username" :disabled="loading" class="w-full" />
        </UFormField>
        <UFormField label="Password">
          <UInput v-model="form.password" type="password" autocomplete="current-password" :disabled="loading" class="w-full" />
        </UFormField>
        <UAlert v-if="sessionExpired" color="warning" description="Session expired. Please login again." />
        <UAlert v-if="error" color="error" :description="error" />
        <UButton type="submit" block :loading="loading" color="neutral">Sign in</UButton>
      </form>
    </UCard>
  </div>
</template>
