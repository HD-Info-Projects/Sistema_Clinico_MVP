<script setup lang="ts">
import type { ExameCatalogo, ExameSelecionado, PadraoExame } from '~/types'

const props = defineProps<{
  /** Medico alvo quando um admin gerencia os padroes de outro usuario */
  medicoId?: number | null
  padrao?: PadraoExame | null
}>()

const open = defineModel<boolean>('open', { default: false })

const padroesStore = usePadroesStore()

const nome = ref('')
const exames = ref<ExameSelecionado[]>([])
const saving = ref(false)

const selectedExame = ref<ExameCatalogo | null>(null)
const buscaTermo = ref('')
const sugestoesExames = ref<ExameCatalogo[]>([])
const carregandoExames = ref(false)

let buscaTimeout: ReturnType<typeof setTimeout> | null = null
let examesController: AbortController | null = null
let examesRequestId = 0

function normalizarIdExame(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

function normalizarExameSelecionado(valor: unknown): ExameSelecionado | null {
  if (typeof valor === 'string') {
    const nome = valor.trim()
    return nome ? { nome, exameId: null } : null
  }

  if (!valor || typeof valor !== 'object') return null

  const item = valor as Record<string, unknown>
  const nome = typeof item.nome === 'string' ? item.nome.trim() : ''
  const exameId = normalizarIdExame(item.exameId ?? item.exame_id ?? item.id)

  if (!nome) return null

  return { nome, exameId }
}

function exameExisteNaLista(lista: ExameSelecionado[], exame: ExameSelecionado) {
  const nome = exame.nome.trim().toLocaleLowerCase('pt-BR')

  return lista.some((atual) => {
    if (atual.exameId && exame.exameId && atual.exameId === exame.exameId) return true
    return atual.nome.trim().toLocaleLowerCase('pt-BR') === nome
  })
}

function normalizarListaExames(valor: unknown) {
  if (!Array.isArray(valor)) return []

  const itens: ExameSelecionado[] = []
  for (const item of valor) {
    const exame = normalizarExameSelecionado(item)
    if (!exame || exameExisteNaLista(itens, exame)) continue
    itens.push(exame)
  }

  return itens
}

function adicionarExame(valor: unknown) {
  const exame = normalizarExameSelecionado(valor)
  if (!exame) return
  if (exameExisteNaLista(exames.value, exame)) return

  exames.value.push(exame)
  selectedExame.value = null
  buscaTermo.value = ''
  sugestoesExames.value = []
}

function adicionarExameManual() {
  adicionarExame(buscaTermo.value)
}

watch(selectedExame, (val) => {
  if (val) adicionarExame(val)
})

watch(buscaTermo, (val) => {
  if (buscaTimeout) clearTimeout(buscaTimeout)

  if (!val || val.length < 2) {
    sugestoesExames.value = []
    return
  }

  buscaTimeout = setTimeout(() => {
    buscarExames(val)
  }, 300)
})

async function buscarExames(q: string) {
  const termo = q.trim()
  if (termo.length < 2) return

  const requestId = ++examesRequestId
  examesController?.abort()
  examesController = new AbortController()

  carregandoExames.value = true
  try {
    const data = await $fetch<{ exames: ExameCatalogo[] }>('/api/exames/buscar', {
      query: { q: termo },
      signal: examesController.signal
    })

    if (requestId !== examesRequestId) return
    if (buscaTermo.value.trim() !== termo) return

    sugestoesExames.value = data.exames || []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return
    if (requestId !== examesRequestId) return
    sugestoesExames.value = []
  } finally {
    carregandoExames.value = false
  }
}

watch(open, (isOpen) => {
  if (isOpen) {
    nome.value = props.padrao?.nome ?? ''
    exames.value = normalizarListaExames(props.padrao?.exames)
    selectedExame.value = null
    buscaTermo.value = ''
    sugestoesExames.value = []
  }
})

function removerExame(i: number) {
  exames.value.splice(i, 1)
}

async function salvar() {
  if (!nome.value.trim()) return
  saving.value = true
  try {
    const data = {
      nome: nome.value.trim(),
      tipo: 'exame' as const,
      exames: exames.value
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
    :ui="{ content: 'max-h-dvh', body: 'min-h-0 overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h2 class="text-lg font-semibold">
            {{ padrao ? 'Editar' : 'Novo' }} Padrão de Exames
          </h2>
          <p class="text-sm text-muted mt-0.5">
            Configure o nome e os exames do modelo
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar padrão de exames"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="space-y-6 p-4 sm:p-6">
        <div class="space-y-1 flex flex-col">
          <label class="text-sm font-medium">Nome do modelo</label>
          <UInput
            v-model="nome"
            placeholder="Ex: Check-up anual"
            size="lg"
          />
        </div>

        <div class="space-y-1">
          <p class="text-sm font-medium">
            Exames
          </p>

          <div class="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center">
            <UInputMenu
              v-model="selectedExame"
              v-model:search-term="buscaTermo"
              :items="sugestoesExames"
              :loading="carregandoExames"
              label-key="nome"
              placeholder="Digite o nome do exame..."
              class="flex-1"
              clear
              ignore-filter
            >
              <template #item-label="{ item }">
                <span class="text-sm">
                  {{ item.codigo_alfanumerico ? `${item.codigo_alfanumerico} — ` : '' }}{{ item.nome }}{{ item.codigo_amb ? ` (${item.codigo_amb})` : '' }}
                </span>
              </template>
            </UInputMenu>
            <UButton
              icon="i-lucide-plus"
              label="Adicionar"
              color="primary"
              variant="soft"
              :disabled="!buscaTermo.trim()"
              @click="adicionarExameManual"
            />
          </div>

          <div class="space-y-2">
            <div
              v-for="(exame, i) in exames"
              :key="i"
              class="flex items-start justify-between gap-2 rounded-lg border border-muted p-3"
            >
              <span class="min-w-0 break-words text-sm">{{ exame.nome }}</span>
              <UButton
                icon="i-lucide-x"
                :aria-label="`Remover exame ${exame.nome}`"
                color="error"
                variant="ghost"
                size="sm"
                @click="removerExame(i)"
              />
            </div>

            <p
              v-if="!exames.length"
              class="text-sm text-muted italic py-4 text-center"
            >
              Nenhum exame adicionado.
            </p>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm text-muted">
          {{ exames.length }} exame{{ exames.length !== 1 ? 's' : '' }} válido{{ exames.length !== 1 ? 's' : '' }}
        </p>
        <div class="flex flex-col-reverse gap-2 sm:flex-row">
          <UButton
            label="Cancelar"
            color="neutral"
            variant="ghost"
            class="w-full justify-center sm:w-auto"
            @click="void (open = false)"
          />
          <UButton
            label="Salvar"
            :loading="saving"
            :disabled="!nome.trim()"
            class="w-full justify-center sm:w-auto"
            @click="salvar"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
