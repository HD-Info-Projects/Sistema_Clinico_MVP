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
    :ui="{
      header: `p-1 px-2 sm:px-2 bg-${props.cor}`,
      body: props.accordion && !aberto ? 'hidden' : 'p-2 sm:p-3'
    }"
  >
    <template #header>
      <UCollapsible
        v-if="props.accordion"
        v-model:open="aberto"
      >
        <button
          type="button"
          class="flex w-full items-center text-left text-white"
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
      </UCollapsible>

      <slot
        v-else
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

    <div
      v-show="!props.accordion || aberto"
      class=""
    >
      <slot />
    </div>
  </UCard>
</template>
