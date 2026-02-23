<script setup lang="ts">
const { isDragging, dropLabel } = usePdfDrop()
</script>

<template>
  <Transition
    enter-active-class="transition duration-150 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-100 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isDragging"
      class="fixed inset-0 z-50 pointer-events-none"
    >
      <div class="absolute inset-3 rounded-xl border-2 border-dashed border-primary bg-primary/5" />
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="bg-default rounded-2xl shadow-xl ring ring-default px-10 py-7 flex flex-col items-center gap-3">
          <UIcon name="i-lucide-file-up" class="size-10 text-primary" />
          <p class="text-lg font-semibold text-highlighted">
            {{ dropLabel ?? 'Drop PDF to add to a Knowledge Base' }}
          </p>
          <p class="text-sm text-dimmed">PDF files only</p>
        </div>
      </div>
    </div>
  </Transition>
</template>
