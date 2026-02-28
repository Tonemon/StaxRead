<script setup lang="ts">
const route = useRoute()
await navigateTo(`/settings/teams/${route.params.id}/general`, { replace: true })
</script>
<template></template>
