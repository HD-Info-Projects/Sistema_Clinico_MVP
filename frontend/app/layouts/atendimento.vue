<!-- eslint-disable vue/no-v-html -->
<script setup lang="ts">
import type { HistoricoRecord, HistoricoResponse, HistoricoLocalRecord } from '~/types'
import { formatarDataHistorico } from '~/utils/time'

const { sanitizeHtml } = useSanitize()

const open = ref(true)
const isMobile = useMediaQuery('(max-width: 1023px)')
const route = useRoute()

watch(
  () => route.fullPath,
  () => {
    if (isMobile.value) open.value = false
  }
)

provide('openNav', () => {
  open.value = !open.value
})

const agendamentosStore = useAgendamentosStore()

const expandedContent = ref<Record<string, boolean>>({})

function toggleContent(id: string) {
  expandedContent.value[id] = !expandedContent.value[id]
}

onMounted(() => {
  if (!agendamentosStore.emAtendimento) {
    navigateTo('/dashboard', { replace: true })
    return
  }
  fetchHistorico()
})

const agendamento = computed(() => agendamentosStore.emAtendimento)

watch(
  () => agendamentosStore.emAtendimento,
  (atendimento, anterior) => {
    if (anterior && !atendimento) {
      void navigateTo('/dashboard', { replace: true })
    }
  }
)

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
const localHistorico = ref<HistoricoLocalRecord[]>([])
const biodataOffset = ref(0)
const biodataHasMore = ref(false)

const HISTORICO_BIODATA_LIMIT = 10

useInfiniteScroll(
  historicoScrollRef,
  () => {
    if (biodataHasMore.value && !isLoadingHistorico.value && !isLoadingMaisHistorico.value) {
      void carregarMaisHistoricoBiodata()
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

async function fetchHistorico() {
  const paciente = agendamento.value?.paciente
  const pacienteId = paciente?.id
  if (!pacienteId) return

  isLoadingHistorico.value = true
  biodataHistorico.value = []
  localHistorico.value = []
  historicoItems.value = []
  biodataOffset.value = 0
  biodataHasMore.value = false

  try {
    const [biodataResult, localResult] = await Promise.allSettled([
      buscarHistoricoBiodata(0),
      $fetch<HistoricoLocalRecord[]>(`/api/historico-local/${pacienteId}`)
    ])

    const biodataResponse = biodataResult.status === 'fulfilled' ? biodataResult.value : null
    localHistorico.value = localResult.status === 'fulfilled' ? localResult.value : []

    if (biodataResponse) {
      adicionarRegistrosBiodata(biodataResponse.items)
      biodataOffset.value = biodataResponse.offset + biodataResponse.items.length
      biodataHasMore.value = biodataResponse.has_more
    }

    if (biodataResult.status === 'rejected') {
      console.error('Erro ao buscar histórico BioData')
    }
    if (localResult.status === 'rejected') {
      console.error('Erro ao buscar histórico local')
    }

    remontarHistoricoItems()
  } catch {
    console.error('Erro ao buscar histórico')
    historicoItems.value = []
  } finally {
    isLoadingHistorico.value = false
  }
}

async function buscarHistoricoBiodata(offset: number): Promise<HistoricoResponse> {
  const paciente = agendamento.value?.paciente
  const pacienteId = paciente?.id
  if (!pacienteId) {
    return { items: [], limit: HISTORICO_BIODATA_LIMIT, offset, has_more: false }
  }

  return await $fetch<HistoricoResponse>(`/api/historico-paciente/${pacienteId}`, {
    query: {
      cpf: cpfHistorico(paciente.cpf),
      nome: paciente.nome || undefined,
      limit: HISTORICO_BIODATA_LIMIT,
      offset
    }
  })
}

async function carregarMaisHistoricoBiodata() {
  if (!biodataHasMore.value || isLoadingMaisHistorico.value || isLoadingHistorico.value) return

  isLoadingMaisHistorico.value = true
  try {
    const response = await buscarHistoricoBiodata(biodataOffset.value)
    adicionarRegistrosBiodata(response.items)
    biodataOffset.value = response.offset + response.items.length
    biodataHasMore.value = response.has_more
    remontarHistoricoItems()
  } catch {
    console.error('Erro ao carregar mais histórico BioData')
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

function chaveHistoricoBiodata(registro: HistoricoRecord) {
  return registro.ID_ANAMNESE || `${registro.ID_ATENDIMENTO || ''}-${registro.DATA_ANAMNESE || ''}-${registro.ANAMNESE || ''}`
}

function remontarHistoricoItems() {
  historicoItems.value = montarHistoricoItems(biodataHistorico.value, localHistorico.value)
}

function montarHistoricoItems(biodata: HistoricoRecord[], local: HistoricoLocalRecord[]) {
  const items: HistoricoTimelineItem[] = []
  const biodataPorAtendimento = new Map<string, HistoricoTimelineItem>()

  for (const r of biodata) {
    const dataHistorico = r.DATA_ANAMNESE || r.DATA_CONSULTA || r.DATA_ENCERRAMENTO || ''
    const idGrupo = `biodata-${dataHistorico || r.ID_ANAMNESE}`
    let item = biodataPorAtendimento.get(idGrupo)

    if (!item) {
      item = {
        id: idGrupo,
        title: formatarDataHistorico(dataHistorico),
        time: formatarHoraHistorico(dataHistorico),
        icon: 'i-lucide-calendar',
        subtitle: r.MEDICO || undefined,
        _sortKey: r.DATA_ANAMNESE || r.DATA_CONSULTA || r.DATA_ENCERRAMENTO || '',
        cards: []
      }
      biodataPorAtendimento.set(idGrupo, item)
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
  // Formata CID principal + secundários para exibição no card de diagnóstico
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

function calcularIdade(dataNascimento: string) {
  const hoje = new Date()
  const nasc = new Date(dataNascimento)
  let idade = hoje.getFullYear() - nasc.getFullYear()
  const mes = hoje.getMonth() - nasc.getMonth()
  if (mes < 0 || (mes === 0 && hoje.getDate() < nasc.getDate())) idade--
  return idade
}

function voltarDashboard() {
  navigateTo('/dashboard', { replace: true })
}
</script>

<template>
  <div
    v-if="agendamento"
    class="h-screen flex overflow-hidden"
  >
    <USidebar
      v-model:open="open"
      collapsible="icon"
      :style="{ '--sidebar-width': '35rem' }"
    >
      <template #header>
        <UButton
          icon="i-lucide-arrow-left"
          label="Voltar pro Dashboard"
          variant="ghost"
          color="neutral"
          @click="voltarDashboard"
        />
      </template>
      <div class="flex justify-center items-center py-2 gap-2">
        <UAvatar
          size="3xl"
          color="primary"
          :alt="agendamento.paciente.nome"
        />
        <div>
          <p class="text-md font-semibold">
            {{ agendamento.paciente.nome }}
          </p>
          <p class="text-sm text-muted">
            {{ calcularIdade(agendamento.paciente.dataNascimento) }} anos
            · {{ agendamento.paciente.sexo === 'masculino' ? 'Masculino' : 'Feminino' }}
            · Convênio: {{ agendamento.paciente.convenio }}
          </p>
        </div>
      </div>
      <div class="space-y-2 flex flex-col gap-1 justify-center items-center overflow-y-hidden">
        <USeparator />
        <div class="flex flex-col items-center justify-center gap-2">
          <div class="flex items-center gap-1">
            <UIcon
              name="i-lucide-shield-alert"
              class="text-error mt-0.5 shrink-0"
            />
            <p class="text-xs text-error font-bold uppercase tracking-wider">
              Alergias
            </p>
          </div>

          <div class="flex flex-wrap gap-1 mt-1">
            <template v-if="agendamento.paciente.alergias.length">
              <UBadge
                v-for="(alergia, i) in agendamento.paciente.alergias"
                :key="i"
                :label="alergia"
                color="error"
                variant="subtle"
              />
            </template>
            <UBadge
              v-else
              label="Nenhuma"
              color="success"
              variant="subtle"
            />
          </div>
        </div>
        <USeparator />
        <div class="flex flex-col items-center justify-center gap-2">
          <div class="flex items-center gap-1">
            <UIcon
              name="i-lucide-pill"
              class="text-tertiary mt-0.5 shrink-0"
            />
            <p class="text-xs text-tertiary font-bold uppercase tracking-wider">
              Medicação em Uso
            </p>
          </div>
          <div class="flex flex-wrap gap-1 mt-1">
            <template v-if="agendamento.paciente.medicamentosEmUso.length">
              <UBadge
                v-for="(med, i) in agendamento.paciente.medicamentosEmUso"
                :key="i"
                :label="med.nome"
                color="tertiary"
                variant="subtle"
              />
            </template>
            <UBadge
              v-else
              label="Nenhuma"
              color="success"
              variant="subtle"
            />
          </div>
        </div>
        <USeparator />
        <div
          ref="historicoScrollRef"
          class="overflow-y-auto max-h-[calc(100vh-18rem)] w-full px-2"
        >
          <UTimeline
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
                        class="text-sm cursor-pointer whitespace-pre-line"
                        :class="expandedContent[item.id + '-' + card.id] ? '' : 'line-clamp-3'"
                        @click="toggleContent(item.id + '-' + card.id)"
                        v-html="sanitizeHtml(card.description)"
                      />
                      <!-- eslint-enable vue/no-v-html -->
                      <UIcon
                        v-if="card.description.length > 100"
                        :name="expandedContent[item.id + '-' + card.id] ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                        class="absolute bottom-0 right-0 dark:bg-neutral-900 px-1 cursor-pointer text-muted"
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
              v-else-if="biodataHasMore"
              label="Carregar mais histórico"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="void carregarMaisHistoricoBiodata()"
            />
          </div>
        </div>
      </div>
    </USidebar>
    <main class="flex-1 overflow-y-auto bg-neutral-100 dark:bg-neutral-950">
      <slot />
    </main>
  </div>
  <div
    v-else
    class="h-screen flex items-center justify-center bg-neutral-100 dark:bg-neutral-950"
  >
    <UCard>
      <div class="flex flex-col items-center py-12 gap-4">
        <div class="text-muted">
          <div class="i-lucide-stethoscope text-6xl mx-auto" />
        </div>
        <p class="text-xl font-medium">
          Nenhum paciente em atendimento
        </p>
        <p class="text-sm text-muted">
          Selecione um paciente no Dashboard e clique em "Atender" para iniciar o atendimento.
        </p>
        <UButton
          label="Ir para o Dashboard"
          color="primary"
          @click="voltarDashboard"
        />
      </div>
    </UCard>
  </div>
</template>
