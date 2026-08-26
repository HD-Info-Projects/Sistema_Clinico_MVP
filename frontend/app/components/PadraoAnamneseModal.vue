<script setup lang="ts">
import type { PadraoAnamnese } from '~/types'

const props = defineProps<{
  /** Medico alvo quando um admin gerencia os padroes de outro usuario */
  medicoId?: number | null
  padrao?: PadraoAnamnese | null
}>()

const open = defineModel<boolean>('open', { default: false })

const padroesAnamneseStore = usePadroesAnamneseStore()

const nome = ref('')
const conteudo = ref('')
const saving = ref(false)

watch(open, (isOpen) => {
  if (isOpen) {
    nome.value = props.padrao?.nome ?? ''
    conteudo.value = props.padrao?.conteudo ?? ''
  }
}, { immediate: true })

async function salvar() {
  if (!nome.value.trim()) return
  saving.value = true
  try {
    const data = {
      nome: nome.value.trim(),
      conteudo: conteudo.value
    }
    if (props.padrao) {
      await padroesAnamneseStore.atualizar(props.padrao.id, data, props.medicoId ?? undefined)
    } else {
      await padroesAnamneseStore.criar(data, props.medicoId ?? undefined)
    }
    open.value = false
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    fullscreen
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h2 class="text-lg font-semibold">
            {{ padrao ? 'Editar' : 'Novo' }} Padrão de Anamnese
          </h2>
          <p class="text-sm text-muted mt-0.5">
            Configure o nome e o conteúdo do modelo de anamnese
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="h-full overflow-y-auto p-6 space-y-6 flex flex-col">
        <div class="space-y-1 flex flex-col">
          <label class="text-sm font-medium">Nome do modelo</label>
          <UInput
            v-model="nome"
            placeholder="Ex: Consulta de Rotina"
            size="lg"
          />
        </div>

        <div class="space-y-1 flex flex-col grow">
          <label class="text-sm font-medium">Conteúdo da Anamnese</label>
          <EditorRichText
            v-model="conteudo"
            placeholder="Descreva o padrão de anamnese..."
            class="grow flex flex-col min-h-96"
          />
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-end gap-2 w-full">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
        <UButton
          label="Salvar"
          :loading="saving"
          :disabled="!nome.trim()"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
