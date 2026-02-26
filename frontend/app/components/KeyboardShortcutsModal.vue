<script setup lang="ts">
const { showHelp } = useKeyboardShortcuts()

const shortcuts = [
  { key: 'Ctrl+Space', description: 'Go to search / focus search box' },
  { key: 'Ctrl+K', description: 'Knowledge bases' },
  { key: 'Ctrl+B', description: 'Bookmarks' },
  { key: 'Ctrl+R', description: 'Refresh current page data' },
  { key: '?', description: 'Show this help' },
]
</script>

<template>
  <UModal v-model:open="showHelp" title="Keyboard Shortcuts">
    <template #body>
      <table class="w-full text-sm">
        <tbody class="divide-y divide-default">
          <tr v-for="s in shortcuts" :key="s.key">
            <td class="py-2.5 pr-6 w-36">
              <kbd class="px-2 py-1 text-xs font-mono bg-elevated rounded ring ring-default text-default">{{ s.key }}</kbd>
            </td>
            <td class="py-2.5 text-muted">{{ s.description }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </UModal>
</template>
