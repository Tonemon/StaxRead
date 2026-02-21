<script setup lang="ts">
definePageMeta({ layout: false })
const { login } = useAuth()
const form = reactive({ username: "", password: "" })
const error = ref("")
const loading = ref(false)

async function submit() {
  error.value = ""
  loading.value = true
  try {
    await login(form.username, form.password)
  } catch {
    error.value = "Invalid credentials"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
    <UCard class="w-full max-w-sm">
      <template #header>
        <h1 class="text-xl font-bold text-center text-gray-900 dark:text-white">StaxRead</h1>
      </template>
      <form @submit.prevent="submit" class="space-y-4">
        <UFormField label="Username">
          <UInput v-model="form.username" autocomplete="username" :disabled="loading" />
        </UFormField>
        <UFormField label="Password">
          <UInput v-model="form.password" type="password" autocomplete="current-password" :disabled="loading" />
        </UFormField>
        <UAlert v-if="error" color="error" :description="error" />
        <UButton type="submit" block :loading="loading">Sign in</UButton>
      </form>
    </UCard>
  </div>
</template>
