<script setup lang="ts">
const props = defineProps<{
  abrir: boolean
  titulo: string
  descricao: string
  textoConfirma?: string
  corConfirma?: 'error' | 'success' | 'warning' | 'info' | 'neutral'
}>()

const emit = defineEmits<{
  fechar: []
  confirmar: []
}>()

const proxyOpen = computed({
  get: () => props.abrir,
  set: (val) => { if (!val) emit('fechar') }
})
</script>

<template>
  <UModal
    v-model:open="proxyOpen"
    :ui="{ content: 'max-h-[calc(100dvh-2rem)] overflow-y-auto' }"
  >
    <template #content>
      <div class="space-y-4 p-4 sm:p-6">
        <div class="flex min-w-0 items-start gap-2">
          <UIcon
            name="lucide:trash-2"
            class="mt-1 shrink-0"
          />
          <h3 class="min-w-0 break-words text-xl font-black">
            {{ titulo }}
          </h3>
        </div>
        <p class="break-words text-neutral-500 dark:text-neutral-400">
          {{ descricao }}
        </p>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <UButton
            label="Cancelar"
            color="neutral"
            variant="ghost"
            block
            size="lg"
            class="font-bold rounded-xl"
            @click="emit('fechar')"
          />
          <UButton
            :label="textoConfirma ?? 'Confirmar'"
            :color="corConfirma ?? 'error'"
            variant="solid"
            block
            size="lg"
            class="font-bold rounded-xl"
            @click="emit('confirmar')"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
