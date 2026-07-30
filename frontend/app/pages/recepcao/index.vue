<script setup lang="ts">
type AtendimentoStatus = 'agendado' | 'em-espera' | 'em-atendimento' | 'atendido' | 'faltou' | 'desconhecido'

interface AtendimentoRecepcao {
  id: number | string
  registro: string
  horario: string
  paciente: string
  cpf: string
  prontuario: string
  convenio: string
  telefone: string
  celular: string
  email: string
  medico: string
  especialidade: string
  dataNascimento: string | null
  status: AtendimentoStatus
}

interface MedicoDia {
  id: string
  nome: string
  especialidade: string
  pacientesCount: number
}

interface ResumoRecepcao {
  agendados: number
  emEspera: number
  emAtendimento: number
  atendidos: number
  faltas: number
  desconhecidos: number
}

interface CheckInResponse {
  items: AtendimentoRecepcao[]
  page: number
  pageSize: number
  total: number
  medicos: MedicoDia[]
  resumo: ResumoRecepcao
  data: string
}

const auth = useAuthStore()

const { agora, dataFormatada } = useRelogio(60000)
const userName = computed(() => auth.user?.nome || 'Usuário')

const page = ref(1)
const pageSize = ref(20)
const loading = ref(true)
const errorMsg = ref('')
const busca = ref('')
const selectedStatus = ref<AtendimentoStatus | ''>('')
const selectedMedico = ref<string | null>(null)
const selectedEspecialidade = ref<string | undefined>('Todas as especialidades')

let buscaTimer: ReturnType<typeof setTimeout> | null = null
let requestId = 0

function respostaVazia(): CheckInResponse {
  return {
    items: [],
    page: 1,
    pageSize: pageSize.value,
    total: 0,
    medicos: [],
    resumo: {
      agendados: 0,
      emEspera: 0,
      emAtendimento: 0,
      atendidos: 0,
      faltas: 0,
      desconhecidos: 0
    },
    data: ''
  }
}

const dados = ref<CheckInResponse>(respostaVazia())

const filtrosStatus: { label: string, value: AtendimentoStatus | '' }[] = [
  { label: 'Todos', value: '' },
  { label: 'Agendados', value: 'agendado' },
  { label: 'Em espera', value: 'em-espera' },
  { label: 'Em atendimento', value: 'em-atendimento' },
  { label: 'Atendidos', value: 'atendido' },
  { label: 'Faltosos', value: 'faltou' }
]

const medicosColunas = [
  { accessorKey: 'nome', header: 'Médico' },
  { accessorKey: 'pacientesCount', header: 'Pacientes' }
]

const atendimentosColunas = [
  { accessorKey: 'horario', header: 'Horário' },
  { accessorKey: 'paciente', header: 'Paciente' },
  { accessorKey: 'contato', header: 'Contato' },
  { accessorKey: 'medico', header: 'Médico' },
  { accessorKey: 'status', header: 'Status' }
]

const especialidades = computed(() => {
  const all = new Set<string>()
  dados.value.medicos.forEach((m) => {
    const especialidade = textoInformado(m.especialidade)
    if (especialidade) all.add(especialidade)
  })
  return ['Todas as especialidades', ...Array.from(all).sort()]
})

const medicosDoDia = computed(() => {
  let lista = dados.value.medicos
  if (selectedEspecialidade.value && selectedEspecialidade.value !== 'Todas as especialidades') {
    lista = lista.filter(m => textoInformado(m.especialidade) === selectedEspecialidade.value)
  }
  return lista
})

const selectedMedicoNome = computed(() => {
  if (!selectedMedico.value) return null
  return dados.value.medicos.find(m => m.id === selectedMedico.value)?.nome ?? ''
})

const resumoTotal = computed(() => {
  const resumo = dados.value.resumo
  return resumo.agendados + resumo.emEspera + resumo.emAtendimento + resumo.atendidos + resumo.faltas
})

const tituloTabela = computed(() => {
  const partes = ['Atendimentos do Dia']
  if (selectedMedicoNome.value) partes.push(selectedMedicoNome.value)
  const status = filtrosStatus.find(s => s.value === selectedStatus.value)
  if (status?.value) partes.push(status.label)
  return partes.join(' - ')
})

function formatarData(iso: string) {
  if (!iso) return dataFormatada.value
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

function corStatus(s: string) {
  switch (s) {
    case 'agendado': return 'secondary'
    case 'em-espera': return 'primary'
    case 'em-atendimento': return 'warning'
    case 'atendido': return 'success'
    case 'faltou': return 'error'
    default: return 'neutral'
  }
}

function rotuloStatus(s: string) {
  switch (s) {
    case 'agendado': return 'Agendado'
    case 'em-espera': return 'Em espera'
    case 'em-atendimento': return 'Em atendimento'
    case 'atendido': return 'Atendido'
    case 'faltou': return 'Faltou'
    default: return 'Desconhecido'
  }
}

function textoInformado(valor: string | number | null | undefined) {
  const texto = String(valor ?? '').trim()
  return texto && texto !== '0' ? texto : ''
}

function textoNaoInformado(valor: string | number | null | undefined, fallback = 'Não informado') {
  return textoInformado(valor) || fallback
}

function contatoPrincipal(atendimento: AtendimentoRecepcao) {
  return textoInformado(atendimento.celular) || textoInformado(atendimento.telefone) || 'Não informado'
}

function idadePaciente(dataNascimento: string | null | undefined) {
  if (!dataNascimento) return 'Idade não informada'

  const data = new Date(dataNascimento)
  if (Number.isNaN(data.getTime())) return 'Idade não informada'

  const hoje = new Date()
  let idade = hoje.getFullYear() - data.getFullYear()
  const aniversario = new Date(hoje.getFullYear(), data.getMonth(), data.getDate())
  if (aniversario > hoje) idade -= 1

  if (idade < 0) return 'Idade não informada'
  return idade === 1 ? '1 ano' : `${idade} anos`
}

function resetPageAndFetch() {
  if (page.value === 1) {
    carregarAtendimentos()
  } else {
    page.value = 1
  }
}

async function carregarAtendimentos() {
  const currentRequest = ++requestId
  loading.value = true
  errorMsg.value = ''

  const params = new URLSearchParams()
  params.set('page', String(page.value))
  params.set('pageSize', String(pageSize.value))
  params.set('data', formatarDataISO(new Date()))
  if (selectedStatus.value) params.set('status', selectedStatus.value)
  if (selectedMedico.value) params.set('medico', selectedMedico.value)
  if (busca.value.trim()) params.set('q', busca.value.trim())

  try {
    const response = await $fetch<CheckInResponse>(`/api/check-in?${params.toString()}`)
    if (currentRequest === requestId) dados.value = response
  } catch {
    if (currentRequest === requestId) {
      dados.value = respostaVazia()
      errorMsg.value = 'Erro ao carregar atendimentos'
    }
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

function selecionarMedico(id: string) {
  selectedMedico.value = selectedMedico.value === id ? null : id
  resetPageAndFetch()
}

function limparMedico() {
  selectedMedico.value = null
  resetPageAndFetch()
}

function selecionarStatus(status: AtendimentoStatus | '') {
  selectedStatus.value = status
  resetPageAndFetch()
}

watch(page, () => {
  carregarAtendimentos()
})

watch(busca, () => {
  if (buscaTimer) clearTimeout(buscaTimer)
  buscaTimer = setTimeout(() => {
    resetPageAndFetch()
  }, 350)
})

onMounted(() => {
  carregarAtendimentos()
})

onUnmounted(() => {
  if (buscaTimer) clearTimeout(buscaTimer)
})
</script>

<template>
  <div>
    <UHeader title="Painel da Recepção">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>

    <div class="min-h-screen space-y-4 bg-muted p-4 sm:space-y-6 sm:p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-2xl font-semibold sm:text-3xl">
            {{ getSaudacao(agora) }}, {{ userName }}
          </p>
          <p class="text-base text-muted mt-1">
            {{ formatarData(dados.data) }}. Veja o resumo dos agendamentos da recepção.
          </p>
        </div>
        <div
          class="hidden w-72 lg:block"
          aria-hidden="true"
        />
      </div>

      <UAlert
        v-if="errorMsg"
        :title="errorMsg"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
      />

      <div class="grid grid-cols-1 gap-4  lg:grid-cols-2 lg:gap-6">
        <ChartResumo
          :total="resumoTotal"
          :agendados="dados.resumo.agendados"
          :fila="dados.resumo.emEspera"
          :em-atendimento="dados.resumo.emAtendimento"
          :atendidos="dados.resumo.atendidos"
          :faltas="dados.resumo.faltas"
        />

        <UCard
          class=""
          :ui="{ body: '' }"
        >
          <template #title>
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-lg font-medium">
                Médicos do Dia
              </p>
              <UInputMenu
                v-model="selectedEspecialidade"
                :items="especialidades"
                placeholder="Filtrar por especialidade"
                clearable
                size="sm"
                class="w-full sm:w-56"
              />
            </div>
          </template>

          <div class="overflow-x-auto max-h-55 overflow-y-auto">
            <UTable
              :columns="medicosColunas"
              :data="medicosDoDia"
              class="min-w-90 overflow-auto"
            >
              <template #nome-cell="{ row }">
                <div
                  class="flex min-w-0 cursor-pointer items-center gap-3"
                  @click="selecionarMedico(row.original.id)"
                >
                  <UAvatar
                    :alt="row.original.nome"
                    color="primary"
                    size="sm"
                    class="shrink-0"
                  />
                  <div class="min-w-0">
                    <p
                      class="max-w-48 font-medium text-sm sm:max-w-56"
                      :class="selectedMedico === row.original.id ? 'text-primary' : ''"
                    >
                      {{ row.original.nome }}
                    </p>
                    <p class="max-w-48 truncate text-xs text-muted sm:max-w-56">
                      {{ textoNaoInformado(row.original.especialidade, 'Especialidade não informada') }}
                    </p>
                  </div>
                </div>
              </template>

              <template #pacientesCount-cell="{ row }">
                <UBadge
                  :label="String(row.original.pacientesCount)"
                  color="neutral"
                  variant="soft"
                />
              </template>
            </UTable>
          </div>
        </UCard>
      </div>

      <UCard class="w-full">
        <template #title>
          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-medium">
                  {{ tituloTabela }}
                </p>
                <p class="text-sm text-muted">
                  {{ dados.total }} registro{{ dados.total !== 1 ? 's' : '' }} encontrado{{ dados.total !== 1 ? 's' : '' }}
                </p>
              </div>
              <div class="flex w-full flex-col gap-2 sm:flex-row sm:items-center lg:w-auto">
                <UButton
                  v-if="selectedMedico"
                  icon="i-lucide-x"
                  label="Limpar médico"
                  size="sm"
                  color="neutral"
                  variant="soft"
                  class="w-full sm:w-auto"
                  @click="limparMedico"
                />
                <UInput
                  v-model="busca"
                  icon="i-lucide-search"
                  placeholder="Paciente, CPF, prontuário ou registro"
                  size="sm"
                  class="w-full sm:w-80"
                />
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <UButton
                v-for="status in filtrosStatus"
                :key="status.value || 'todos'"
                :label="status.label"
                :color="status.value ? corStatus(status.value) : 'neutral'"
                :variant="selectedStatus === status.value ? 'solid' : 'soft'"
                size="sm"
                class="flex-1 sm:flex-none"
                @click="selecionarStatus(status.value)"
              />
            </div>
          </div>
        </template>

        <div
          v-if="loading"
          class="space-y-3 py-4"
        >
          <div
            v-for="linha in 6"
            :key="linha"
            class="grid grid-cols-1 gap-3 rounded-lg border border-muted p-3 md:grid-cols-[80px_1.5fr_1fr_1fr_120px]"
          >
            <USkeleton class="h-5 w-16" />
            <div class="space-y-2">
              <USkeleton class="h-5 w-48 max-w-full" />
              <USkeleton class="h-4 w-32 max-w-full" />
            </div>
            <div class="space-y-2">
              <USkeleton class="h-5 w-36 max-w-full" />
              <USkeleton class="h-4 w-44 max-w-full" />
            </div>
            <div class="space-y-2">
              <USkeleton class="h-5 w-40 max-w-full" />
              <USkeleton class="h-4 w-28 max-w-full" />
            </div>
            <USkeleton class="h-6 w-24 rounded-full" />
          </div>
        </div>

        <p
          v-else-if="!dados.items.length"
          class="text-sm text-muted py-4"
        >
          Nenhum atendimento encontrado.
        </p>

        <div
          v-else
          class="overflow-x-auto"
        >
          <UTable
            :columns="atendimentosColunas"
            :data="dados.items"
            class="min-w-[760px]"
          >
            <template #horario-cell="{ row }">
              <span class="font-mono text-sm">{{ row.original.horario || '-' }}</span>
            </template>

            <template #paciente-cell="{ row }">
              <div class="flex min-w-56 items-center gap-3">
                <UAvatar
                  :alt="row.original.paciente"
                  color="primary"
                  size="sm"
                />
                <div>
                  <p class="font-medium">
                    {{ row.original.paciente || 'Paciente não informado' }}
                  </p>
                  <p class="text-xs text-muted">
                    {{ idadePaciente(row.original.dataNascimento) }}
                  </p>
                  <p class="text-xs text-muted">
                    {{ textoNaoInformado(row.original.convenio, 'Convênio não informado') }}
                  </p>
                </div>
              </div>
            </template>

            <template #contato-cell="{ row }">
              <div class="min-w-44 text-sm">
                <p>{{ contatoPrincipal(row.original) }}</p>
                <p class="text-xs text-muted">
                  {{ textoNaoInformado(row.original.email, 'Email não informado') }}
                </p>
              </div>
            </template>

            <template #medico-cell="{ row }">
              <div class="min-w-44 text-sm">
                <p class="font-medium">
                  {{ row.original.medico || '-' }}
                </p>
                <p class="text-xs text-muted">
                  {{ textoNaoInformado(row.original.especialidade, 'Especialidade não informada') }}
                </p>
              </div>
            </template>

            <template #status-cell="{ row }">
              <UBadge
                :label="rotuloStatus(row.original.status)"
                :color="corStatus(row.original.status)"
                variant="subtle"
              />
            </template>
          </UTable>
        </div>

        <div class="flex flex-col gap-3 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-sm text-muted">
            Página {{ page }} · {{ pageSize }} por página
          </p>
          <UPagination
            :page="page"
            :items-per-page="pageSize"
            :total="dados.total"
            @update:page="page = $event"
          />
        </div>
      </UCard>
    </div>
  </div>
</template>
