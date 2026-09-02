<script setup lang="ts">
const props = defineProps<{
  titulo: string
  cor: 'primary' | 'secondary' | 'tertiary' | 'info' | 'warning' | 'error' | 'success' | 'quinary'
  icone: string
}>()
</script>

<template>
  <UCard
    :ui="{
      header: `p-1 px-2 sm:px-2 bg-${props.cor}`,
      body: 'p-2 sm:p-3'
    }"
  >
    <template #header>
      <div class="flex items-center text-white">
        <UIcon
          :name="props.icone"
          class="mr-2 h-5 w-5"
        />
        <h3 class="font-semibold">
          {{ props.titulo }}
        </h3>
      </div>
    </template>

    <slot />
  </UCard>
</template>
