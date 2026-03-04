<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
const { $api } = useNuxtApp()
const authStore = useAuthStore()
const colorMode = useColorMode()

const themeOptions = [
  { label: 'System', value: 'system' },
  { label: 'Light', value: 'light' },
  { label: 'Dark', value: 'dark' },
]

const themePreference = ref<'system' | 'light' | 'dark'>('system')

async function saveTheme(value: string) {
  const theme = value as 'system' | 'light' | 'dark'
  colorMode.preference = theme
  themePreference.value = theme
  await ($api as typeof $fetch)('/auth/me/', { method: 'PATCH', body: { theme } })
}

const profileForm = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
})

const greetingForm = reactive({
  show_greeting: true,
  greeting_display: 'username' as 'username' | 'full_name' | 'first_name',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const profileLoading = ref(false)
const greetingLoading = ref(false)
const passwordLoading = ref(false)
const profileError = ref('')
const greetingError = ref('')
const passwordError = ref('')
const profileSuccess = ref(false)
const greetingSuccess = ref(false)
const passwordSuccess = ref(false)

const greetingDisplayOptions = [
  { label: 'Show username', value: 'username' },
  { label: 'Show first and last name', value: 'full_name' },
  { label: 'Show first name only', value: 'first_name' },
]

// Load current profile
const { data: profile } = await useFetch<{
  id: string; username: string; email: string; first_name: string; last_name: string;
  show_greeting: boolean; greeting_display: string; theme: string
}>('/auth/me/', { $fetch: $api as typeof $fetch })

watch(profile, (p) => {
  if (!p) return
  profileForm.first_name = p.first_name || ''
  profileForm.last_name = p.last_name || ''
  profileForm.username = p.username
  profileForm.email = p.email || ''
  greetingForm.show_greeting = p.show_greeting
  greetingForm.greeting_display = p.greeting_display as 'username' | 'full_name' | 'first_name'
  themePreference.value = (p.theme as 'system' | 'light' | 'dark') || 'system'
}, { immediate: true })

async function saveProfile() {
  profileLoading.value = true
  profileError.value = ''
  profileSuccess.value = false
  try {
    const updated = await ($api as typeof $fetch)<typeof profile.value>('/auth/me/', {
      method: 'PATCH',
      body: { first_name: profileForm.first_name, last_name: profileForm.last_name, username: profileForm.username, email: profileForm.email },
    })
    if (authStore.user && updated) {
      authStore.user = { ...authStore.user, ...updated }
    }
    profileSuccess.value = true
    setTimeout(() => { profileSuccess.value = false }, 3000)
  } catch (e: unknown) {
    profileError.value = (e as { data?: { detail?: string } })?.data?.detail || 'Failed to save profile.'
  } finally {
    profileLoading.value = false
  }
}

async function saveGreeting() {
  greetingLoading.value = true
  greetingError.value = ''
  greetingSuccess.value = false
  try {
    const updated = await ($api as typeof $fetch)<typeof profile.value>('/auth/me/', {
      method: 'PATCH',
      body: { show_greeting: greetingForm.show_greeting, greeting_display: greetingForm.greeting_display },
    })
    if (authStore.user && updated) {
      authStore.user = { ...authStore.user, ...updated }
    }
    greetingSuccess.value = true
    setTimeout(() => { greetingSuccess.value = false }, 3000)
  } catch (e: unknown) {
    greetingError.value = (e as { data?: { detail?: string } })?.data?.detail || 'Failed to save greeting preferences.'
  } finally {
    greetingLoading.value = false
  }
}

async function changePassword() {
  passwordError.value = ''
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = 'New passwords do not match.'
    return
  }
  passwordLoading.value = true
  passwordSuccess.value = false
  try {
    await ($api as typeof $fetch)('/auth/me/change-password/', {
      method: 'POST',
      body: { current_password: passwordForm.current_password, new_password: passwordForm.new_password },
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordSuccess.value = true
    setTimeout(() => { passwordSuccess.value = false }, 3000)
  } catch (e: unknown) {
    const data = (e as { data?: { current_password?: string[]; detail?: string } })?.data
    passwordError.value = data?.current_password?.[0] || data?.detail || 'Failed to change password.'
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <UDashboardPanel id="account">
    <template #header>
      <UDashboardNavbar title="Account" />
    </template>

    <template #body>
      <div class="max-w-xl mx-auto py-8 px-4 space-y-8">

        <!-- Profile -->
        <UCard>
          <template #header>
            <h2 class="text-base font-semibold text-highlighted">Profile</h2>
          </template>
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="First name">
                <UInput v-model="profileForm.first_name" placeholder="First name" @keydown.enter.prevent="saveProfile" />
              </UFormField>
              <UFormField label="Last name">
                <UInput v-model="profileForm.last_name" placeholder="Last name" @keydown.enter.prevent="saveProfile" />
              </UFormField>
            </div>
            <UFormField label="Username">
              <UInput v-model="profileForm.username" placeholder="Username" @keydown.enter.prevent="saveProfile" />
            </UFormField>
            <UFormField label="Email">
              <UInput v-model="profileForm.email" type="email" placeholder="Email" @keydown.enter.prevent="saveProfile" />
            </UFormField>
            <p v-if="profileError" class="text-sm text-error">{{ profileError }}</p>
            <p v-if="profileSuccess" class="text-sm text-success">Profile saved.</p>
          </div>
          <template #footer>
            <div class="flex justify-end">
              <UButton :loading="profileLoading" @click="saveProfile">Save</UButton>
            </div>
          </template>
        </UCard>

        <!-- Greeting preferences -->
        <UCard>
          <template #header>
            <h2 class="text-base font-semibold text-highlighted">Greeting</h2>
          </template>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm text-default">Show greeting on home page</span>
              <USwitch v-model="greetingForm.show_greeting" />
            </div>
            <UFormField v-if="greetingForm.show_greeting" label="Display name">
              <USelectMenu
                v-model="greetingForm.greeting_display"
                :items="greetingDisplayOptions"
                value-key="value"
                class="w-full"
              />
            </UFormField>
            <p v-if="greetingError" class="text-sm text-error">{{ greetingError }}</p>
            <p v-if="greetingSuccess" class="text-sm text-success">Greeting preferences saved.</p>
          </div>
          <template #footer>
            <div class="flex justify-end">
              <UButton :loading="greetingLoading" @click="saveGreeting">Save</UButton>
            </div>
          </template>
        </UCard>

        <!-- Appearance -->
        <UCard>
          <template #header>
            <h2 class="text-base font-semibold text-highlighted">Appearance</h2>
          </template>
          <UFormField label="Theme">
            <USelectMenu
              v-model="themePreference"
              :items="themeOptions"
              value-key="value"
              class="w-48"
              @update:model-value="saveTheme"
            />
          </UFormField>
        </UCard>

        <!-- Change password -->
        <UCard>
          <template #header>
            <h2 class="text-base font-semibold text-highlighted">Change Password</h2>
          </template>
          <div class="space-y-4">
            <UFormField label="Current password">
              <UInput v-model="passwordForm.current_password" type="password" placeholder="Current password" @keydown.enter.prevent="changePassword" />
            </UFormField>
            <UFormField label="New password">
              <UInput v-model="passwordForm.new_password" type="password" placeholder="New password (min 8 chars)" @keydown.enter.prevent="changePassword" />
            </UFormField>
            <UFormField label="Confirm new password">
              <UInput v-model="passwordForm.confirm_password" type="password" placeholder="Confirm new password" @keydown.enter.prevent="changePassword" />
            </UFormField>
            <p v-if="passwordError" class="text-sm text-error">{{ passwordError }}</p>
            <p v-if="passwordSuccess" class="text-sm text-success">Password changed successfully.</p>
          </div>
          <template #footer>
            <div class="flex justify-end">
              <UButton :loading="passwordLoading" @click="changePassword">Change Password</UButton>
            </div>
          </template>
        </UCard>

      </div>
    </template>
  </UDashboardPanel>
</template>
