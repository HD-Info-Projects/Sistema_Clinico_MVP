<script setup lang="ts">
import type { AgendamentoComPaciente, DocumentoMedico, Paciente, ProcedimentoCatalogo, ProcedimentoSelecionado, SolicitacaoProcedimentoDocumentoDados } from '~/types'
import { usePdfMake } from '~/utils/pdf'
import { buildSolicitacaoProcedimento } from '~/utils/pdf-documents'

const props = defineProps<{
  paciente?: Paciente
  agendamento?: AgendamentoComPaciente | null
  dataAtendimento?: string
  documento?: DocumentoMedico | null
}>()

const emit = defineEmits<{
  saved: [documento: DocumentoMedico]
}>()

const open = defineModel<boolean>('open', { default: false })

const agendamentosStore = useAgendamentosStore()
const toast = useToast()

const paciente = computed(() => props.paciente ?? props.agendamento?.paciente ?? agendamentosStore.emAtendimento?.paciente ?? null)
const medSpdataAtendimentoId = computed(() => props.agendamento?.id ?? agendamentosStore.emAtendimento?.id ?? null)
const podeEditar = computed(() => props.documento?.podeEditar ?? true)

function hojeIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const dataAtendimentoPadrao = computed(() => props.dataAtendimento ?? props.agendamento?.data ?? hojeIso())

const data = ref(dataAtendimentoPadrao.value)
const procedimentoSelecionado = ref<ProcedimentoCatalogo | null>(null)
const buscaTermoProcedimento = ref('')
const sugestoesProcedimentos = ref<ProcedimentoCatalogo[]>([])
const procedimentosSelecionados = ref<ProcedimentoSelecionado[]>([])
const carregandoProcedimentos = ref(false)
const salvando = ref(false)

let buscaProcedimentoTimeout: ReturnType<typeof setTimeout> | null = null
let procedimentosController: AbortController | null = null
let procedimentosRequestId = 0

function normalizarId(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

function normalizarNumero(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isFinite(numero) ? numero : null
}

function normalizarTexto(valor: unknown) {
  return typeof valor === 'string' ? valor.trim() : ''
}

function normalizarProcedimentoSelecionado(valor: unknown): ProcedimentoSelecionado | null {
  if (typeof valor === 'string') {
    const nome = valor.trim()
    return nome ? { procedimento_id: null, nome } : null
  }

  if (!valor || typeof valor !== 'object') return null

  const item = valor as Record<string, unknown>
  const nome = normalizarTexto(item.nome ?? item.descricao ?? item.label)
  const procedimentoId = normalizarId(item.procedimento_id ?? item.procedimentoId ?? item.id)

  if (!nome) return null

  return {
    procedimento_id: procedimentoId,
    nome,
    codigo_procedimento: normalizarNumero(item.codigo_procedimento ?? item.codigoProcedimento),
    tipo_ato_codigo: normalizarId(item.tipo_ato_codigo ?? item.tipoAtoCodigo),
    tipo_ato_nome: normalizarTexto(item.tipo_ato_nome ?? item.tipoAtoNome) || null,
    exige_autorizacao: normalizarNumero(item.exige_autorizacao ?? item.exigeAutorizacao),
    qtde_max_guia: normalizarNumero(item.qtde_max_guia ?? item.qtdeMaxGuia)
  }
}

function procedimentoExisteNaLista(lista: ProcedimentoSelecionado[], procedimento: ProcedimentoSelecionado) {
  const nome = procedimento.nome.trim().toLocaleLowerCase('pt-BR')

  return lista.some((atual) => {
    if (atual.procedimento_id && procedimento.procedimento_id && atual.procedimento_id === procedimento.procedimento_id) return true
    return atual.nome.trim().toLocaleLowerCase('pt-BR') === nome
  })
}

function normalizarListaProcedimentos(valor: unknown) {
  const procedimentos: ProcedimentoSelecionado[] = []
  const itens = typeof valor === 'string'
    ? valor.split(/\r?\n/).map(linha => linha.replace(/^[-•\s]+/, '').trim()).filter(Boolean)
    : Array.isArray(valor)
      ? valor
      : valor
        ? [valor]
        : []

  for (const item of itens) {
    const procedimento = normalizarProcedimentoSelecionado(item)
    if (!procedimento || procedimentoExisteNaLista(procedimentos, procedimento)) continue
    procedimentos.push(procedimento)
  }

  return procedimentos
}

function procedimentoLabel(procedimento: ProcedimentoSelecionado | ProcedimentoCatalogo) {
  const codigo = procedimento.codigo_procedimento ? `${procedimento.codigo_procedimento} - ` : ''
  return `${codigo}${procedimento.nome}`
}

const descricaoProcedimentos = computed(() => (
  procedimentosSelecionados.value
    .map(procedimentoLabel)
    .join('\n')
))

function limparBuscaProcedimentos() {
  procedimentosRequestId++
  procedimentosController?.abort()
  sugestoesProcedimentos.value = []
}

watch(buscaTermoProcedimento, (val) => {
  if (buscaProcedimentoTimeout) clearTimeout(buscaProcedimentoTimeout)

  const termo = val.trim()
  if (termo.length < 2) {
    limparBuscaProcedimentos()
    return
  }

  buscaProcedimentoTimeout = setTimeout(() => {
    buscarProcedimentos(termo)
  }, 300)
})

async function buscarProcedimentos(q: string) {
  const termo = q.trim()
  if (termo.length < 2) return

  const requestId = ++procedimentosRequestId
  procedimentosController?.abort()
  procedimentosController = new AbortController()

  carregandoProcedimentos.value = true
  try {
    const data = await $fetch<{ procedimentos: ProcedimentoCatalogo[] }>('/api/procedimentos/buscar', {
      query: { q: termo },
      signal: procedimentosController.signal
    })

    if (requestId !== procedimentosRequestId) return
    if (buscaTermoProcedimento.value.trim() !== termo) return

    sugestoesProcedimentos.value = data.procedimentos || []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return
    if (requestId !== procedimentosRequestId) return
    sugestoesProcedimentos.value = []
  } finally {
    carregandoProcedimentos.value = false
  }
}

function adicionarProcedimento(valor: unknown) {
  const procedimento = normalizarProcedimentoSelecionado(valor)
  if (!procedimento) return
  if (procedimentoExisteNaLista(procedimentosSelecionados.value, procedimento)) return

  procedimentosSelecionados.value.push(procedimento)
  procedimentoSelecionado.value = null
  buscaTermoProcedimento.value = ''
  sugestoesProcedimentos.value = []
}

function removerProcedimentoDaLista(index: number) {
  procedimentosSelecionados.value.splice(index, 1)
}

function preencherFormulario() {
  const dados = props.documento?.tipoDocumento === 'SOLICITACAO_PROCEDIMENTO'
    ? props.documento.dados as SolicitacaoProcedimentoDocumentoDados
    : null

  data.value = dados?.data ?? dataAtendimentoPadrao.value
  const procedimentos = normalizarListaProcedimentos(dados?.procedimentos)
  procedimentosSelecionados.value = procedimentos.length
    ? procedimentos
    : normalizarListaProcedimentos(dados?.descricao)
  procedimentoSelecionado.value = null
  buscaTermoProcedimento.value = ''
  sugestoesProcedimentos.value = []
}

watch(
  () => [open.value, props.documento?.id, props.documento?.updatedAt, dataAtendimentoPadrao.value] as const,
  ([isOpen]) => {
    if (isOpen) preencherFormulario()
  },
  { immediate: true }
)

function formatarDataPdf(dataISO: string) {
  if (!dataISO) return ''
  return new Date(dataISO + 'T12:00:00').toLocaleDateString('pt-BR')
}

const podeEnviar = computed(() => {
  if (!podeEditar.value) return Boolean(props.documento)
  return Boolean(medSpdataAtendimentoId.value && data.value && procedimentosSelecionados.value.length)
})

const botaoLabel = computed(() => podeEditar.value ? 'Salvar e Imprimir' : 'Imprimir')

async function gerarPdf(documento: DocumentoMedico) {
  if (documento.tipoDocumento !== 'SOLICITACAO_PROCEDIMENTO') return

  const dados = documento.dados as SolicitacaoProcedimentoDocumentoDados
  const procedimentos = normalizarListaProcedimentos(dados.procedimentos)
  const pdfMake = await usePdfMake()
  const doc = await buildSolicitacaoProcedimento({
    paciente: paciente.value?.nome ?? 'Paciente',
    data: formatarDataPdf(dados.data),
    descricao: dados.descricao,
    procedimentos: procedimentos.length ? procedimentos : normalizarListaProcedimentos(dados.descricao),
    medico: dados.medico ?? undefined,
    crm: dados.crm ?? undefined,
    especialidade: dados.especialidade ?? undefined
  })
  pdfMake.createPdf(doc).open()
}

async function fecharEAbrirPdf(documento: DocumentoMedico) {
  open.value = false
  await nextTick()
  await gerarPdf(documento)
}

async function salvarEImprimir() {
  if (!podeEnviar.value) return

  if (!podeEditar.value && props.documento) {
    await fecharEAbrirPdf(props.documento)
    return
  }

  salvando.value = true
  try {
    const documento = await $fetch<DocumentoMedico>(`/api/documentos-medicos/${medSpdataAtendimentoId.value}/SOLICITACAO_PROCEDIMENTO`, {
      method: 'PUT',
      body: {
        dados: {
          data: data.value,
          descricao: descricaoProcedimentos.value,
          procedimentos: procedimentosSelecionados.value
        }
      }
    })

    emit('saved', documento)
    await fecharEAbrirPdf(documento)
  } catch {
    toast.add({
      title: 'Erro ao salvar solicitação',
      description: 'Não foi possível salvar o documento médico.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    salvando.value = false
  }
}

onUnmounted(() => {
  if (buscaProcedimentoTimeout) clearTimeout(buscaProcedimentoTimeout)
  procedimentosController?.abort()
})
</script>

<template>
  <UModal v-model:open="open">
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">
          Solicitação de Procedimento
        </h2>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="space-y-4 p-4">
        <UFormField label="Paciente">
          <UInput
            :model-value="paciente?.nome ?? '—'"
            disabled
            class="w-full"
          />
        </UFormField>

        <UFormField label="Data">
          <UInput
            v-model="data"
            type="date"
            :disabled="!podeEditar"
            class="w-full"
          />
        </UFormField>

        <UFormField label="Procedimentos">
          <div class="flex gap-2">
            <UInputMenu
              v-model="procedimentoSelecionado"
              v-model:search-term="buscaTermoProcedimento"
              :items="sugestoesProcedimentos"
              :loading="carregandoProcedimentos"
              label-key="nome"
              placeholder="Buscar procedimento por nome, código ou tipo..."
              icon="i-lucide-search"
              clear
              ignore-filter
              :disabled="!podeEditar"
              class="flex-1 w-full"
            >
              <template #item-label="{ item }">
                <div class="min-w-0 flex flex-col">
                  <span class="text-sm truncate">{{ procedimentoLabel(item) }}</span>
                  <span
                    v-if="item.tipo_ato_nome"
                    class="text-xs text-muted truncate"
                  >
                    {{ item.tipo_ato_nome }}
                  </span>
                </div>
              </template>
              <template #empty>
                <p
                  v-if="buscaTermoProcedimento"
                  class="px-3 py-4 text-sm text-muted text-center"
                >
                  Nenhum procedimento encontrado
                </p>
              </template>
            </UInputMenu>
            <UButton
              icon="i-lucide-plus"
              label="Adicionar"
              color="primary"
              variant="soft"
              :disabled="!podeEditar || !procedimentoSelecionado"
              @click="adicionarProcedimento(procedimentoSelecionado)"
            />
          </div>
        </UFormField>

        <UCard
          :ui="{ body: 'p-3' }"
        >
          <template #title>
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium">Procedimentos selecionados</span>
              <span class="text-xs text-muted">{{ procedimentosSelecionados.length }} procedimento(s)</span>
            </div>
          </template>

          <div
            v-if="procedimentosSelecionados.length"
            class="space-y-2"
          >
            <div
              v-for="(procedimento, index) in procedimentosSelecionados"
              :key="procedimento.procedimento_id ?? `${procedimento.nome}-${index}`"
              class="flex items-start justify-between gap-3 p-3 rounded-lg border border-muted"
            >
              <div class="min-w-0 space-y-1">
                <p class="text-sm font-medium truncate">
                  {{ procedimentoLabel(procedimento) }}
                </p>
                <div class="flex flex-wrap gap-2">
                  <UBadge
                    v-if="procedimento.tipo_ato_nome"
                    size="xs"
                    color="neutral"
                    variant="soft"
                  >
                    {{ procedimento.tipo_ato_nome }}
                  </UBadge>
                  <UBadge
                    v-if="procedimento.exige_autorizacao"
                    size="xs"
                    color="warning"
                    variant="soft"
                  >
                    Exige autorização
                  </UBadge>
                  <UBadge
                    v-if="!procedimento.procedimento_id"
                    size="xs"
                    color="neutral"
                    variant="outline"
                  >
                    Legado
                  </UBadge>
                </div>
              </div>
              <UButton
                v-if="podeEditar"
                icon="i-lucide-x"
                color="error"
                variant="ghost"
                size="sm"
                @click="removerProcedimentoDaLista(index)"
              />
            </div>
          </div>
          <p
            v-else
            class="text-sm text-muted italic py-4 text-center"
          >
            Nenhum procedimento selecionado.
          </p>
        </UCard>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
        <UButton
          icon="i-lucide-printer"
          :label="botaoLabel"
          :disabled="!podeEnviar"
          :loading="salvando"
          @click="salvarEImprimir"
        />
      </div>
    </template>
  </UModal>
</template>
