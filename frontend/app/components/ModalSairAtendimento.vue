<script setup lang="ts">
const props = defineProps<{
  abrir: boolean
  nomePaciente?: string | null
  finalizando?: boolean
  cancelando?: boolean
}>()

const emit = defineEmits<{
  fechar: []
  pausar: []
  cancelar: []
  finalizar: []
}>()

const proxyOpen = computed({
  get: () => props.abrir,
  set: (val) => { if (!val) emit('fechar') }
})

const ocupado = computed(() => !!props.finalizando || !!props.cancelando)
</script>

<template>
  <UModal
    v-model:open="proxyOpen"
    :ui="{ content: 'max-h-[calc(100dvh-2rem)] min-w-3xl overflow-y-auto' }"
  >
    <template #content>
      <div class="space-y-4 p-4 sm:p-6">
        <div class="flex min-w-0 items-start justify-between gap-2">
          <div class="flex min-w-0 items-start gap-2">
            <UIcon
              name="i-lucide-stethoscope"
              class="mt-1 shrink-0 text-warning"
            />
            <h3 class="min-w-0 wrap-break-word text-xl font-black">
              Atendimento em andamento
            </h3>
          </div>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="sm"
            aria-label="Fechar"
            :disabled="ocupado"
            @click="emit('fechar')"
          />
        </div>
        <p class="wrap-break-word text-neutral-500 dark:text-neutral-400">
          <template v-if="nomePaciente">
            Você está atendendo <span class="font-semibold text-highlighted">{{ nomePaciente }}</span>.
          </template>
          <template v-else>
            Há um atendimento em andamento.
          </template>
          O que deseja fazer antes de sair desta tela?
        </p>
        <p class="wrap-break-word text-sm text-neutral-500 dark:text-neutral-400">
          Ao pausar, o atendimento continua em andamento e você poderá retomá-lo pelo dashboard.
        </p>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <UButton
            label="Pausar atendimento"
            icon="i-lucide-pause"
            color="neutral"
            variant="soft"
            block
            size="lg"
            class="font-bold rounded-xl"
            :disabled="ocupado"
            @click="emit('pausar')"
          />
          <UButton
            label="Cancelar atendimento"
            icon="i-lucide-x-circle"
            color="error"
            variant="soft"
            block
            size="lg"
            class="font-bold rounded-xl"
            :loading="cancelando"
            :disabled="ocupado"
            @click="emit('cancelar')"
          />
          <UButton
            label="Finalizar atendimento"
            icon="i-lucide-check-circle"
            color="success"
            variant="solid"
            block
            size="lg"
            class="font-bold rounded-xl"
            :loading="finalizando"
            :disabled="ocupado"
            @click="emit('finalizar')"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
