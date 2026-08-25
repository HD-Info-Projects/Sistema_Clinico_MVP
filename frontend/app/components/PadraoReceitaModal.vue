<script setup lang="ts">
import type { ItemMedicamento, PadraoReceita } from '~/types'

const props = defineProps<{
  /** Medico alvo quando um admin gerencia os padroes de outro usuario */
  medicoId?: number | null
  padrao?: PadraoReceita | null
}>()

const open = defineModel<boolean>('open', { default: false })

const padroesStore = usePadroesStore()

const nome = ref('')
const medicamentos = ref<ItemMedicamento[]>([])
const saving = ref(false)

watch(open, (isOpen) => {
  if (isOpen) {
    nome.value = props.padrao?.nome ?? ''
    if (props.padrao?.medicamentos?.length) {
      medicamentos.value = props.padrao.medicamentos.map(m => ({ ...m }))
    } else {
      medicamentos.value = [{ nome: '', dosagem: '', detalhes: '' }]
    }
  }
}, { immediate: true })

function adicionarMedicamento() {
  medicamentos.value.push({ nome: '', dosagem: '', detalhes: '' })
}

function removerMedicamento(i: number) {
  medicamentos.value.splice(i, 1)
}

const medicamentosValidos = computed(() => medicamentos.value.filter(m => m.nome.trim()))

async function salvar() {
  if (!nome.value.trim()) return
  saving.value = true
  try {
    const data = {
      nome: nome.value.trim(),
      tipo: 'receita' as const,
      medicamentos: medicamentosValidos.value
    }
    if (props.padrao) {
      await padroesStore.atualizar(props.padrao.id, data, props.medicoId ?? undefined)
    } else {
      await padroesStore.criar(data, props.medicoId ?? undefined)
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
            {{ padrao ? 'Editar' : 'Novo' }} Padrão de Receita
          </h2>
          <p class="text-sm text-muted mt-0.5">
            Configure o nome e os medicamentos do modelo
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
      <div class="h-full overflow-y-auto p-6 space-y-6">
        <div class="space-y-1 flex flex-col">
          <label class="text-sm font-medium">Nome do modelo</label>
          <UInput
            v-model="nome"
            placeholder="Ex: Hipertensão Padrão"
            size="lg"
          />
        </div>

        <div class="space-y-1">
          <p class="text-sm font-medium">
            Medicamentos
          </p>

          <div class="space-y-3">
            <div
              v-for="(med, i) in medicamentos"
              :key="i"
              class="flex items-center gap-3 w-full p-3 rounded-lg border border-muted"
            >
              <div class="grid grid-cols-1 sm:grid-cols-6 gap-3 w-full">
                <div class="space-y-1 flex flex-col col-span-1 sm:col-span-2">
                  <label class="text-xs font-medium text-muted">Medicamento</label>
                  <UInput
                    v-model="med.nome"
                    placeholder="Ex: Dipirona"
                  />
                </div>
                <div class="space-y-1 flex flex-col ">
                  <label class="text-xs font-medium text-muted">Dosagem</label>
                  <UInput
                    v-model="med.dosagem"
                    placeholder="Ex: 50mg"
                  />
                </div>
                <div class="space-y-1 flex flex-col col-span-1 sm:col-span-3">
                  <label class="text-xs font-medium text-muted">Detalhes</label>
                  <UInput
                    v-model="med.detalhes"
                    placeholder="Ex: 1x ao dia"
                  />
                </div>
              </div>
              <UButton
                icon="i-lucide-x"
                color="error"
                variant="ghost"
                size="sm"
                class="mt-5"
                @click="removerMedicamento(i)"
              />
            </div>

            <UButton
              icon="i-lucide-plus"
              label="Adicionar mais um medicamento"
              variant="outline"
              class="w-full"
              @click="adicionarMedicamento"
            />

            <p
              v-if="!medicamentos.length"
              class="text-sm text-muted italic py-4 text-center"
            >
              Nenhum medicamento adicionado.
            </p>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <p class="text-sm text-muted">
          {{ medicamentosValidos.length }} medicamento{{ medicamentosValidos.length !== 1 ? 's' : '' }} válido{{ medicamentosValidos.length !== 1 ? 's' : '' }}
        </p>
        <div class="flex gap-2">
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
      </div>
    </template>
  </UModal>
</template>
