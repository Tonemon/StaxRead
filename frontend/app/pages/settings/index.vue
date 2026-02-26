<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'admin' })
</script>
<template>
  <NuxtRedirect to="/settings/knowledge-bases" />
</template>
