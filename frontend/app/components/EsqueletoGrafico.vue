<script setup lang="ts">
defineProps<{
  tipo: 'donut' | 'barras' | 'donut-lista'
}>()
</script>

<template>
  <div aria-hidden="true">
    <div
      v-if="tipo === 'donut'"
      class="flex h-56 w-full min-w-0 items-center justify-center sm:h-64"
    >
      <div class="aspect-square size-40 animate-pulse rounded-full bg-neutral-200 sm:size-48 dark:bg-neutral-800" />
    </div>

    <div
      v-else-if="tipo === 'barras'"
      class="flex h-56 w-full min-w-0 items-center justify-center sm:h-64"
    >
      <div class="h-48 w-full animate-pulse rounded bg-neutral-200 dark:bg-neutral-800" />
    </div>

    <div
      v-else
      class="flex w-full min-w-0 items-center justify-center gap-3 sm:gap-4"
    >
      <div class="aspect-square size-40 shrink-0 animate-pulse rounded-full bg-neutral-200 sm:size-48 dark:bg-neutral-800" />
      <div class="min-w-0 flex-1 space-y-2.5">
        <div
          v-for="i in 4"
          :key="i"
          class="h-4 animate-pulse rounded bg-neutral-200 dark:bg-neutral-800"
          :class="i % 2 ? 'w-full' : 'w-3/4'"
        />
      </div>
    </div>
  </div>
</template>
