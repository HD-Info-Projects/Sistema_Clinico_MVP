<script setup lang="ts">
const props = withDefaults(defineProps<{
  // Quando obrigatório, o modal não pode ser fechado sem informar a sala.
  obrigatorio?: boolean
}>(), {
  obrigatorio: false
})

const emit = defineEmits<{
  salva: [sala: string]
}>()

const open = defineModel<boolean>('open', { default: false })

const { sala, definirSala } = useSalaAtendimento()
const inputSala = ref('')
const salaValida = computed(() => /^\d+$/.test(inputSala.value) && Number(inputSala.value) > 0)

watch(open, (val) => {
  if (val) inputSala.value = sala.value ?? ''
}, { immediate: true })

function confirmarSala() {
  if (!salaValida.value) return
  definirSala(inputSala.value)
  open.value = false
  emit('salva', inputSala.value)
}
</script>

<template>
  <UModal
    v-model:open="open"
    :close="!props.obrigatorio"
    :dismissible="!props.obrigatorio"
  >
    <template #header>
      <h2 class="text-lg font-semibold">
        Sala de Atendimento
      </h2>
    </template>

    <template #body>
      <div class="space-y-4">
        <p class="text-sm text-muted">
          Informe o número do consultório:
        </p>
        <UForm class="flex flex-col gap-3">
          <UFormItem
            label="Número do consultório"
            :error="!salaValida ? 'Informe um número de consultório válido' : ''"
          >
            <UInput
              v-model="inputSala"
              min="1"
              step="1"
              placeholder="Ex: 1"
              class="w-full"
              size="lg"
            />
          </UFormItem>
          <div class="flex justify-end gap-2">
            <UButton
              type="submit"
              label="Salvar"
              :disabled="!salaValida"
              @click="confirmarSala"
            />
          </div>
        </UForm>
      </div>
    </template>
  </UModal>
</template>
