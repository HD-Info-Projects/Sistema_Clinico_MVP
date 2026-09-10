<script setup lang="ts">
const props = defineProps<{
  titulo: string
  cor: 'primary' | 'secondary' | 'tertiary' | 'info' | 'warning' | 'error' | 'success' | 'quinary' | 'quaternary' | 'neutral'
  icone: string
  accordion?: boolean
  abertoInicialmente?: boolean
}>()

const aberto = ref(props.abertoInicialmente ?? false)
</script>

<template>
  <UCard
    v-if="!props.accordion"
    :ui="{
      header: `p-1 px-2 sm:px-2 bg-${props.cor}`,
      body: 'p-2 sm:p-3'
    }"
  >
    <template #header>
      <slot
        name="header"
      >
        <div class="flex items-center text-white">
          <UIcon
            :name="props.icone"
            class="mr-2 h-5 w-5"
          />
          <h3 class="font-semibold">
            {{ props.titulo }}
          </h3>
        </div>
      </slot>
    </template>

    <slot />
  </UCard>

  <UCollapsible
    v-else
    v-model:open="aberto"
    :unmount-on-hide="false"
    class="card-cadastro-accordion overflow-hidden rounded-lg bg-default ring ring-default"
    :ui="{ content: 'overflow-hidden' }"
  >
    <button
      type="button"
      :class="`flex w-full items-center p-1 px-2 text-left text-white bg-${props.cor}`"
    >
      <slot name="header">
        <div class="flex items-center">
          <UIcon
            :name="props.icone"
            class="mr-2 h-5 w-5"
          />
          <h3 class="font-semibold">
            {{ props.titulo }}
          </h3>
        </div>
      </slot>
      <UIcon
        :name="aberto ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
        class="ml-auto h-5 w-5"
      />
    </button>

    <template #content>
      <div class="border-t border-default p-2 sm:p-3">
        <slot />
      </div>
    </template>
  </UCollapsible>
</template>

<style>
@keyframes card-cadastro-expand {
  from {
    height: 0;
  }

  to {
    height: var(--reka-collapsible-content-height);
  }
}

@keyframes card-cadastro-collapse {
  from {
    height: var(--reka-collapsible-content-height);
  }

  to {
    height: 0;
  }
}

.card-cadastro-accordion [data-slot='content'][data-state='open'] {
  animation: card-cadastro-expand 200ms ease-out;
}

.card-cadastro-accordion [data-slot='content'][data-state='closed'] {
  animation: card-cadastro-collapse 200ms ease-out;
}
</style>
