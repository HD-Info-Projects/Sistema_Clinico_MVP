<script setup lang="ts">
const props = defineProps<{
  titulo: string
  valor: number | string
  cor: 'primary' | 'secondary' | 'tertiary' | 'info' | 'warning' | 'error' | 'success' | 'quinary'
  icone: string
  medida?: string
}>()
</script>

<template>
  <UCard
    class="w-full min-w-0"
    :ui="{
      body: 'p-4 sm:p-4 sm:py-5 min-w-0'
    }"
  >
    <div class="flex min-w-0 items-center gap-3">
      <UBadge
        class="aspect-square shrink-0"
        variant="soft"
        :color="props.cor"
      >
        <UIcon
          :name="props.icone"
          :class="`size-8 text-primary bg-${props.cor}`"
        />
      </UBadge>
      <div class="flex min-w-0 flex-1 flex-col">
        <p class="break-words text-sm font-bold">
          {{ props.titulo }}
        </p>
        <p :class="`break-words text-2xl font-black text-${props.cor}`">
          {{ props.valor }}{{ props.medida }}
        </p>
      </div>
    </div>

    <slot />
  </UCard>
</template>
