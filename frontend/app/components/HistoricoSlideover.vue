<!-- eslint-disable vue/no-v-html -->
<script setup lang="ts">
import type { Paciente, AgendamentoComPaciente, HistoricoRecord, HistoricoResponse, HistoricoLocalRecord } from '~/types'
import { formatarDataHistorico } from '~/utils/time'

const props = defineProps<{
  paciente?: Paciente | null
  agendamento?: AgendamentoComPaciente | null
}>()

const open = defineModel<boolean>('open', { default: false })

const { sanitizeHtml } = useSanitize()

const expandedContent = ref<Record<string, boolean>>({})

const pacienteAtual = computed(() => props.agendamento?.paciente ?? props.paciente ?? null)

function toggleContent(id: string) {
  expandedContent.value[id] = !expandedContent.value[id]
}

type HistoricoCardType = 'Anamnese' | 'diagnostico' | 'receita' | 'exames'

type HistoricoCard = {
  id: string
  type: HistoricoCardType
  title: string
  icon: string
  description: string
}

type HistoricoTimelineItem = {
  id: string
  title: string
  time?: string
  subtitle?: string
  icon: string
  cards: HistoricoCard[]
  _sortKey: string
}

const historicoItems = ref<HistoricoTimelineItem[]>([])
const isLoadingHistorico = ref(false)
const isLoadingMaisHistorico = ref(false)
const historicoScrollRef = ref<HTMLElement | null>(null)
const biodataHistorico = ref<HistoricoRecord[]>([])
const spdataHistorico = ref<HistoricoRecord[]>([])
const localHistorico = ref<HistoricoLocalRecord[]>([])
const biodataOffset = ref(0)
const biodataHasMore = ref(false)
const spdataOffset = ref(0)
const spdataHasMore = ref(false)

const HISTORICO_BIODATA_LIMIT = 10
const HISTORICO_SPDATA_LIMIT = 10

const historicoExternoHasMore = computed(() => biodataHasMore.value || spdataHasMore.value)

type HistoricoCacheEntry = {
  biodata: HistoricoRecord[]
  spdata: HistoricoRecord[]
  local: HistoricoLocalRecord[]
  biodataOffset: number
  biodataHasMore: boolean
  spdataOffset: number
  spdataHasMore: boolean
}

const historicoCache = new Map<string, HistoricoCacheEntry>()
let historicoRequestId = 0

useInfiniteScroll(
  historicoScrollRef,
  () => {
    if (historicoExternoHasMore.value && !isLoadingHistorico.value && !isLoadingMaisHistorico.value) {
      void carregarMaisHistoricoExterno()
    }
  },
  { distance: 160 }
)

function temConteudoUtil(descricao: string): boolean {
  const texto = descricao?.trim() || ''
  if (!texto) return false

  const textoVisivel = texto
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#160;|&#xA0;/gi, ' ')
    .replace(/[\u00A0\u200B-\u200D\uFEFF]/g, '')
    .trim()

  if (!textoVisivel) return false

  const lower = textoVisivel.toLowerCase()
  if (lower === 'não informado' || lower === 'nao informado') return false
  if (/^[\s—–-]+$/.test(textoVisivel)) return false
  return true
}

const historicoItemsVisiveis = computed(() => {
  return historicoItems.value.filter((item) => {
    if (!item.title) return false
    return item.cards.some(c => temConteudoUtil(c.description))
  })
})

const cardHeaderColors: Record<HistoricoCardType, string> = {
  Anamnese: 'bg-primary dark:bg-primary-800',
  diagnostico: 'bg-neutral-600 dark:bg-neutral-800',
  receita: 'bg-secondary dark:bg-secondary-800',
  exames: 'bg-tertiary dark:bg-tertiary-800'
}

function cpfHistorico(valor?: string | null): string | undefined {
  const texto = String(valor || '').trim()
  const semDecimal = texto.endsWith('.0') && [10, 11].includes(texto.slice(0, -2).replace(/\D/g, '').length)
    ? texto.slice(0, -2)
    : texto
  const digitos = semDecimal.replace(/\D/g, '')
  const cpf = digitos.length === 10 ? digitos.padStart(11, '0') : digitos
  if (cpf.length !== 11) return undefined
  if (new Set(cpf).size === 1) return undefined
  return cpf
}

const historicoCacheKey = computed(() => {
  const paciente = pacienteAtual.value
  if (!paciente?.id) return ''

  return [
    paciente.id,
    cpfHistorico(paciente.cpf) || '',
    paciente.nome || '',
    props.agendamento?.spdataAtendimentoId || ''
  ].join(':')
})

watch([open, historicoCacheKey], ([val]) => {
  if (val && pacienteAtual.value) {
    void fetchHistorico()
  } else if (!val) {
    resetHistoricoState()
  }
})

function resetHistoricoState() {
  historicoItems.value = []
  biodataHistorico.value = []
  spdataHistorico.value = []
  localHistorico.value = []
  biodataOffset.value = 0
  biodataHasMore.value = false
  spdataOffset.value = 0
  spdataHasMore.value = false
  isLoadingHistorico.value = false
  isLoadingMaisHistorico.value = false
}

function restaurarHistoricoCache(cache: HistoricoCacheEntry) {
  biodataHistorico.value = [...cache.biodata]
  spdataHistorico.value = [...cache.spdata]
  localHistorico.value = [...cache.local]
  biodataOffset.value = cache.biodataOffset
  biodataHasMore.value = cache.biodataHasMore
  spdataOffset.value = cache.spdataOffset
  spdataHasMore.value = cache.spdataHasMore
  remontarHistoricoItems()
}

function salvarHistoricoCache(cacheKey: string) {
  if (!cacheKey) return

  historicoCache.set(cacheKey, {
    biodata: [...biodataHistorico.value],
    spdata: [...spdataHistorico.value],
    local: [...localHistorico.value],
    biodataOffset: biodataOffset.value,
    biodataHasMore: biodataHasMore.value,
    spdataOffset: spdataOffset.value,
    spdataHasMore: spdataHasMore.value
  })
}

function isHistoricoAtual(requestId: number, cacheKey: string) {
  return open.value && requestId === historicoRequestId && cacheKey === historicoCacheKey.value
}

async function fetchHistorico() {
  const paciente = pacienteAtual.value
  const pacienteId = paciente?.id
  if (!pacienteId) return

  const cacheKey = historicoCacheKey.value
  const cache = historicoCache.get(cacheKey)
  if (cache) {
    restaurarHistoricoCache(cache)
    return
  }

  const requestId = ++historicoRequestId

  isLoadingHistorico.value = true
  biodataHistorico.value = []
  spdataHistorico.value = []
  localHistorico.value = []
  historicoItems.value = []
  biodataOffset.value = 0
  biodataHasMore.value = false
  spdataOffset.value = 0
  spdataHasMore.value = false

  try {
    const localPromise = buscarHistoricoLocal(pacienteId)
      .then((local) => {
        if (!isHistoricoAtual(requestId, cacheKey)) return
        localHistorico.value = local
        remontarHistoricoItems()
        if (historicoItemsVisiveis.value.length > 0) isLoadingHistorico.value = false
      })
      .catch(() => {
        if (isHistoricoAtual(requestId, cacheKey)) console.error('Erro ao buscar histórico local')
      })

    const biodataPromise = buscarHistoricoBiodata(0)
      .then((biodataResponse) => {
        if (!isHistoricoAtual(requestId, cacheKey)) return
        adicionarRegistrosBiodata(biodataResponse.items)
        biodataOffset.value = biodataResponse.offset + biodataResponse.items.length
        biodataHasMore.value = biodataResponse.has_more
        remontarHistoricoItems()
      })
      .catch(() => {
        if (isHistoricoAtual(requestId, cacheKey)) console.error('Erro ao buscar histórico BioData')
      })

    const spdataPromise = buscarHistoricoSpdata(0)
      .then((spdataResponse) => {
        if (!isHistoricoAtual(requestId, cacheKey)) return
        adicionarRegistrosSpdata(spdataResponse.items)
        spdataOffset.value = spdataResponse.offset + spdataResponse.items.length
        spdataHasMore.value = spdataResponse.has_more
        remontarHistoricoItems()
      })
      .catch(() => {
        if (isHistoricoAtual(requestId, cacheKey)) console.error('Erro ao buscar histórico SPDATA')
      })

    await Promise.allSettled([localPromise, biodataPromise, spdataPromise])

    if (isHistoricoAtual(requestId, cacheKey)) salvarHistoricoCache(cacheKey)
  } catch {
    historicoItems.value = []
  } finally {
    if (isHistoricoAtual(requestId, cacheKey)) isLoadingHistorico.value = false
  }
}

async function buscarHistoricoLocal(pacienteId: number): Promise<HistoricoLocalRecord[]> {
  const paciente = pacienteAtual.value

  return await $fetch<HistoricoLocalRecord[]>(`/api/historico-local/${pacienteId}`, {
    query: {
      cpf: cpfHistorico(paciente?.cpf),
      nome: paciente?.nome || undefined,
      spdataAtendimentoId: props.agendamento?.spdataAtendimentoId || undefined
    }
  })
}

async function buscarHistoricoBiodata(offset: number): Promise<HistoricoResponse> {
  const paciente = pacienteAtual.value
  const pacienteId = paciente?.id
  if (!pacienteId) {
    return { items: [], limit: HISTORICO_BIODATA_LIMIT, offset, has_more: false }
  }

  return await $fetch<HistoricoResponse>(`/api/historico-paciente/${pacienteId}`, {
    query: {
      cpf: cpfHistorico(paciente.cpf),
      nome: paciente.nome || undefined,
      spdataAtendimentoId: props.agendamento?.spdataAtendimentoId || undefined,
      limit: HISTORICO_BIODATA_LIMIT,
      offset
    }
  })
}

async function buscarHistoricoSpdata(offset: number): Promise<HistoricoResponse> {
  const paciente = pacienteAtual.value
  const pacienteId = paciente?.id
  if (!pacienteId) {
    return { items: [], limit: HISTORICO_SPDATA_LIMIT, offset, has_more: false }
  }

  return await $fetch<HistoricoResponse>(`/api/historico-spdata/${pacienteId}`, {
    query: {
      cpf: cpfHistorico(paciente.cpf),
      nome: paciente.nome || undefined,
      spdataAtendimentoId: props.agendamento?.spdataAtendimentoId || undefined,
      limit: HISTORICO_SPDATA_LIMIT,
      offset
    }
  })
}

async function carregarMaisHistoricoExterno() {
  if (!historicoExternoHasMore.value || isLoadingMaisHistorico.value || isLoadingHistorico.value) return

  isLoadingMaisHistorico.value = true
  try {
    const requests: Promise<{ origem: 'biodata' | 'spdata', response: HistoricoResponse }>[] = []

    if (biodataHasMore.value) {
      requests.push(buscarHistoricoBiodata(biodataOffset.value).then(response => ({ origem: 'biodata' as const, response })))
    }
    if (spdataHasMore.value) {
      requests.push(buscarHistoricoSpdata(spdataOffset.value).then(response => ({ origem: 'spdata' as const, response })))
    }

    const results = await Promise.allSettled(requests)
    for (const result of results) {
      if (result.status === 'rejected') {
        console.error('Erro ao carregar mais histórico externo')
        continue
      }

      const { origem, response } = result.value
      if (origem === 'biodata') {
        adicionarRegistrosBiodata(response.items)
        biodataOffset.value = response.offset + response.items.length
        biodataHasMore.value = response.has_more
      } else {
        adicionarRegistrosSpdata(response.items)
        spdataOffset.value = response.offset + response.items.length
        spdataHasMore.value = response.has_more
      }
    }

    remontarHistoricoItems()
    salvarHistoricoCache(historicoCacheKey.value)
  } finally {
    isLoadingMaisHistorico.value = false
  }
}

function adicionarRegistrosBiodata(registros: HistoricoRecord[]) {
  const existentes = new Set(biodataHistorico.value.map(chaveHistoricoBiodata))
  const novos = registros.filter((registro) => {
    const chave = chaveHistoricoBiodata(registro)
    if (existentes.has(chave)) return false
    existentes.add(chave)
    return true
  })

  biodataHistorico.value.push(...novos)
}

function adicionarRegistrosSpdata(registros: HistoricoRecord[]) {
  const existentes = new Set(spdataHistorico.value.map(chaveHistoricoSpdata))
  const novos = registros.filter((registro) => {
    const chave = chaveHistoricoSpdata(registro)
    if (existentes.has(chave)) return false
    existentes.add(chave)
    return true
  })

  spdataHistorico.value.push(...novos)
}

function chaveHistoricoBiodata(registro: HistoricoRecord) {
  return registro.ID_ANAMNESE || `${registro.ID_ATENDIMENTO || ''}-${registro.DATA_ANAMNESE || ''}-${registro.ANAMNESE || ''}`
}

function chaveHistoricoSpdata(registro: HistoricoRecord) {
  return registro.ID_ANAMNESE || `spdata-${registro.ID_ATENDIMENTO || ''}-${registro.DATA_ANAMNESE || ''}-${registro.ANAMNESE || ''}`
}

function remontarHistoricoItems() {
  historicoItems.value = montarHistoricoItems(biodataHistorico.value, spdataHistorico.value, localHistorico.value)
}

function montarHistoricoItems(biodata: HistoricoRecord[], spdata: HistoricoRecord[], local: HistoricoLocalRecord[]) {
  const items: HistoricoTimelineItem[] = []
  const historicoExternoPorAtendimento = new Map<string, HistoricoTimelineItem>()

  for (const r of [...biodata, ...spdata]) {
    const origemSpdata = r.ORIGEM === 'SPDATA'
    const dataHistorico = r.DATA_ANAMNESE || r.DATA_CONSULTA || r.DATA_ENCERRAMENTO || ''
    const idGrupo = origemSpdata
      ? `spdata-${r.ID_ANAMNESE || dataHistorico || r.ID_ATENDIMENTO}`
      : `biodata-${dataHistorico || r.ID_ANAMNESE}`
    let item = historicoExternoPorAtendimento.get(idGrupo)

    if (!item) {
      item = {
        id: idGrupo,
        title: formatarDataHistorico(dataHistorico),
        time: formatarHoraHistorico(dataHistorico),
        icon: 'i-lucide-calendar',
        subtitle: montarSubtituloHistoricoExterno(r),
        _sortKey: r.DATA_ANAMNESE || r.DATA_CONSULTA || r.DATA_ENCERRAMENTO || '',
        cards: []
      }
      historicoExternoPorAtendimento.set(idGrupo, item)
      items.push(item)
    }

    const anamnese = montarAnamneseBiodata(r)
    if (temConteudoUtil(anamnese)) {
      item.cards.push({
        id: `anamnese-${r.ID_ANAMNESE || item.cards.length}`,
        type: 'Anamnese',
        title: 'Anamnese',
        icon: 'i-lucide-file-text',
        description: anamnese
      })
    }

    adicionarCardUnico(item, {
      id: `diagnostico-${r.ID_ANAMNESE || item.cards.length}`,
      type: 'diagnostico',
      title: 'diagnostico',
      icon: 'i-lucide-clipboard-check',
      description: montarDiagnosticosBiodata(r)
    })
  }

  for (const l of local) {
    const dataHistorico = l.data_consulta || ''
    items.push({
      id: `local-${l.spdata_atendimento_id || dataHistorico || items.length}`,
      title: formatarDataHistorico(dataHistorico),
      time: formatarHoraHistorico(dataHistorico),
      icon: 'i-lucide-calendar',
      subtitle: l.medico_nome || undefined,
      _sortKey: dataHistorico,
      cards: [
        { id: 'anamnese-local', type: 'Anamnese', title: 'Anamnese', icon: 'i-lucide-file-text', description: l.anamnese || '' },
        { id: 'diagnostico-local', type: 'diagnostico', title: 'diagnostico', icon: 'i-lucide-clipboard-check', description: montarDiagnosticos(l) },
        { id: 'receita-local', type: 'receita', title: 'receita', icon: 'i-lucide-pill', description: l.medicamentos?.join('\n') || '' },
        { id: 'exames-local', type: 'exames', title: 'exames', icon: 'i-lucide-flask-conical', description: montarExames(l.exames) }
      ]
    })
  }

  items.sort((a, b) => timestampHistorico(b._sortKey) - timestampHistorico(a._sortKey))

  return items
}

function montarSubtituloHistoricoExterno(item: HistoricoRecord): string | undefined {
  if (item.ORIGEM !== 'SPDATA') return item.MEDICO || undefined

  return ['SPDATA', item.MODELO_EVOLUCAO, item.MEDICO]
    .filter(Boolean)
    .join(' · ') || undefined
}

function timestampHistorico(valor: string): number {
  const timestamp = new Date(valor).getTime()
  return Number.isNaN(timestamp) ? 0 : timestamp
}

function formatarHoraHistorico(dataStr: string): string {
  if (!dataStr) return ''
  const data = new Date(dataStr)
  if (Number.isNaN(data.getTime())) return ''
  return data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function adicionarCardUnico(item: HistoricoTimelineItem, card: HistoricoCard) {
  if (!temConteudoUtil(card.description)) return
  const existe = item.cards.some(c => c.type === card.type && c.description === card.description)
  if (!existe) item.cards.push(card)
}

function montarAnamneseBiodata(item: HistoricoRecord): string {
  return item.ANAMNESE || item.QUEIXA_PRINCIPAL || item.OBS_ATENDIMENTO || ''
}

function montarDiagnosticosBiodata(item: HistoricoRecord): string {
  const partes: string[] = []

  if (item.CID_PRINCIPAL || item.DIAGNOSTICO_PRINCIPAL) {
    partes.push([item.CID_PRINCIPAL, item.DIAGNOSTICO_PRINCIPAL].filter(Boolean).join(' — '))
  }

  for (const cid of [item.CID_SECUNDARIO, item.CID_TERCIARIO, item.CID_QUATERNARIO]) {
    if (!cid) continue
    partes.push(...cid.split('\n').map(c => c.trim()).filter(Boolean))
  }

  if (item.DIAGNOSTICO_SECUNDARIO) {
    partes.push(item.DIAGNOSTICO_SECUNDARIO)
  }

  return partes.join('\n')
}

function montarDiagnosticos(item: HistoricoLocalRecord): string {
  const partes: string[] = []
  if (item.cid_principal) {
    partes.push(`${item.cid_principal} — ${item.cid_principal_descricao || ''} (principal)`)
  }
  for (const s of item.cids_secundarios) {
    partes.push(`${s.codigo} — ${s.descricao || ''}`)
  }
  return partes.join('\n')
}

function escapeHtml(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

function montarExames(exames?: HistoricoLocalRecord['exames']): string {
  if (!exames?.length) return ''

  return exames
    .map((exame) => {
      if (typeof exame === 'string') return exame
      const nome = exame.nome || exame.descricao || exame.tipo_exame || ''
      if (!temConteudoUtil(exame.orientacao || '')) return nome

      return `${escapeHtml(nome)}\n<strong>Orientação:</strong>\n${exame.orientacao}`
    })
    .filter(Boolean)
    .join('\n')
}
</script>

<template>
  <USlideover
    v-model:open="open"
    side="left"
    :ui="{ content: 'h-dvh max-h-dvh w-[35rem] max-w-full', body: 'min-h-0 overflow-hidden p-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div
          v-if="pacienteAtual"
          class="flex items-center gap-3"
        >
          <UAvatar
            :alt="pacienteAtual.nome"
            color="primary"
            size="sm"
          />
          <div>
            <h2 class="text-lg font-semibold">
              Histórico
            </h2>
            <p class="text-sm text-muted">
              {{ pacienteAtual.nome }}
            </p>
          </div>
        </div>
        <h2
          v-else
          class="text-lg font-semibold"
        >
          Histórico do Paciente
        </h2>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar histórico"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div
        ref="historicoScrollRef"
        class="h-full overflow-y-auto p-4 sm:p-6"
      >
        <div
          v-if="isLoadingHistorico"
          class="flex justify-center py-8"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="size-6 animate-spin text-muted"
          />
        </div>

        <div
          v-else-if="historicoItemsVisiveis.length === 0"
          class="flex flex-col items-center py-12 gap-2 text-center"
        >
          <UIcon
            name="i-lucide-folder-open"
            class="size-8 text-muted"
          />
          <p class="text-sm text-muted">
            Nenhum registro encontrado.
          </p>
        </div>

        <UTimeline
          v-else
          :items="historicoItemsVisiveis"
          color="primary"
          :default-value="historicoItemsVisiveis.length"
          size="xs"
        >
          <template #title="{ item }">
            <div class="flex items-start justify-between w-full gap-2">
              <div class="leading-tight">
                <span>{{ item.title }}</span>
                <span
                  v-if="item.time"
                  class="block text-xs text-muted"
                >{{ item.time }}</span>
              </div>
              <span
                v-if="item.subtitle"
                class="text-xs text-muted truncate ml-2"
              >{{ item.subtitle }}</span>
            </div>
          </template>
          <template #description="{ item }">
            <div class="space-y-2 py-2">
              <template
                v-for="card in item.cards"
                :key="card.id"
              >
                <UCard
                  v-if="temConteudoUtil(card.description)"
                  class="rounded-lg border border-muted hover:bg-muted/50"
                  :ui="{
                    header: `p-0.5 sm:px-2 ${cardHeaderColors[card.type]}`,
                    body: 'p-2 sm:p-2'
                  }"
                >
                  <template #title>
                    <div class="flex items-center gap-2">
                      <UIcon
                        :name="card.icon"
                        class="text-white"
                      />
                      <p class="font-semibold text-sm text-white capitalize">
                        {{ card.title }}
                      </p>
                    </div>
                  </template>
                  <div class="relative">
                    <!-- eslint-disable vue/no-v-html -->
                    <div
                      class="cursor-pointer overflow-hidden break-words text-sm whitespace-pre-line [&_*]:max-w-full"
                      :class="expandedContent[item.id + '-' + card.id] ? '' : 'line-clamp-3'"
                      @click="toggleContent(item.id + '-' + card.id)"
                      v-html="sanitizeHtml(card.description)"
                    />
                    <!-- eslint-enable vue/no-v-html -->
                    <UButton
                      v-if="card.description.length > 100"
                      :icon="expandedContent[item.id + '-' + card.id] ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                      :aria-label="expandedContent[item.id + '-' + card.id] ? 'Recolher conteúdo' : 'Expandir conteúdo'"
                      :aria-expanded="expandedContent[item.id + '-' + card.id]"
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      class="absolute right-0 bottom-0 dark:bg-neutral-900"
                      @click.stop="toggleContent(item.id + '-' + card.id)"
                    />
                  </div>
                </UCard>
              </template>
            </div>
          </template>
        </UTimeline>

        <div class="flex justify-center py-3">
          <UIcon
            v-if="isLoadingMaisHistorico"
            name="i-lucide-loader-circle"
            class="size-5 animate-spin text-muted"
          />
          <UButton
            v-else-if="historicoExternoHasMore"
            label="Carregar mais histórico"
            color="neutral"
            variant="ghost"
            size="sm"
            @click="void carregarMaisHistoricoExterno()"
          />
        </div>
      </div>
    </template>
  </USlideover>
</template>
