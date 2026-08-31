<script setup lang="ts">
type AuditoriaUsuario = {
  id: number
  nome_completo: string
  email: string
  role: string
}

type AuditoriaEvento = {
  id: number
  usuario_id: number | null
  medico_id: number | null
  acao: string
  entidade: string | null
  entidade_id: number | null
  descricao: string | null
  ip: string | null
  user_agent: string | null
  created_at: string | null
  usuario: AuditoriaUsuario | null
}

type AuditoriaResponse = {
  items: AuditoriaEvento[]
  limit: number
  offset: number
  has_more: boolean
}

const openNav = inject<() => void>('openNav', () => {})
const eventos = ref<AuditoriaEvento[]>([])
const loading = ref(false)
const erro = ref<string | null>(null)
const dataIni = ref('')
const dataFim = ref('')
const acao = ref('')
const entidade = ref('')
const limit = ref(50)
const offset = ref(0)
const hasMore = ref(false)

const acoesCriticas = new Set([
  'LOGIN_FALHA',
  'ACESSO_NEGADO',
  'EXPORTOU_DADOS',
  'VISUALIZOU_HISTORICO_BIODATA',
  'VISUALIZOU_DOCUMENTOS_MEDICOS'
])

function formatarData(valor: string | null) {
  if (!valor) return '-'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'medium'
  }).format(new Date(valor))
}

function usuarioLabel(evento: AuditoriaEvento) {
  if (evento.usuario?.nome_completo) return evento.usuario.nome_completo
  if (evento.usuario_id) return `Usuário #${evento.usuario_id}`
  return 'Não identificado'
}

function entidadeLabel(evento: AuditoriaEvento) {
  const nome = evento.entidade || '-'
  return evento.entidade_id ? `${nome} #${evento.entidade_id}` : nome
}

async function carregarAuditoria(novoOffset = 0) {
  loading.value = true
  erro.value = null

  const params = new URLSearchParams()
  if (dataIni.value) params.set('dataIni', dataIni.value)
  if (dataFim.value) params.set('dataFim', dataFim.value)
  if (acao.value.trim()) params.set('acao', acao.value.trim())
  if (entidade.value.trim()) params.set('entidade', entidade.value.trim())
  params.set('limit', String(limit.value))
  params.set('offset', String(novoOffset))

  try {
    const response = await $fetch<AuditoriaResponse>(`/api/auditorias?${params.toString()}`)
    eventos.value = response.items
    offset.value = response.offset
    hasMore.value = response.has_more
  } catch (error: unknown) {
    const fetchError = error as { data?: { statusMessage?: string }, statusMessage?: string }
    erro.value = fetchError.data?.statusMessage || fetchError.statusMessage || 'Falha ao carregar auditoria LGPD'
  } finally {
    loading.value = false
  }
}

function aplicarFiltros() {
  carregarAuditoria(0)
}

function proximaPagina() {
  carregarAuditoria(offset.value + limit.value)
}

function paginaAnterior() {
  carregarAuditoria(Math.max(offset.value - limit.value, 0))
}

onMounted(() => {
  carregarAuditoria()
})
</script>

<template>
  <div class="min-h-screen space-y-6 bg-slate-50 p-4 dark:bg-slate-950 sm:p-6">
    <UButton
      icon="i-lucide-panel-left"
      label="Abrir menu"
      color="neutral"
      variant="ghost"
      class="min-h-11 lg:hidden"
      @click="openNav()"
    />
    <header class="flex flex-col gap-2">
      <UBadge
        label="LGPD"
        color="info"
        variant="soft"
        class="w-fit"
      />
      <h1 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 sm:text-3xl">
        Auditoria LGPD
      </h1>
      <p class="max-w-3xl text-sm text-slate-600 dark:text-slate-300 sm:text-base">
        Acompanhe metadados de acessos sensíveis, autenticação, tentativas negadas e operações relevantes sem expor conteúdo clínico nos logs.
      </p>
    </header>

    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon
            name="i-lucide-filter"
            class="size-5 text-slate-500 dark:text-slate-400"
          />
          <span class="font-medium">Filtros</span>
        </div>
      </template>

      <form
        class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5"
        @submit.prevent="aplicarFiltros"
      >
        <UFormField label="Data inicial">
          <UInput
            v-model="dataIni"
            type="date"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Data final">
          <UInput
            v-model="dataFim"
            type="date"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Ação">
          <UInput
            v-model="acao"
            placeholder="LOGIN_SUCESSO"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Entidade">
          <UInput
            v-model="entidade"
            placeholder="paciente"
            class="w-full"
          />
        </UFormField>
        <div class="flex items-end">
          <UButton
            label="Aplicar"
            icon="i-lucide-search"
            type="submit"
            :loading="loading"
            class="w-full justify-center"
          />
        </div>
      </form>
    </UCard>

    <UAlert
      v-if="erro"
      color="error"
      variant="soft"
      icon="i-lucide-alert-triangle"
      :title="erro"
    />

    <UCard>
      <template #header>
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <div class="min-w-0">
            <h2 class="font-semibold text-slate-900 dark:text-slate-100">
              Eventos registrados
            </h2>
            <p class="text-sm text-slate-600 dark:text-slate-400">
              Exibindo {{ eventos.length }} evento(s), a partir do offset {{ offset }}.
            </p>
          </div>
          <UButton
            icon="i-lucide-refresh-cw"
            label="Atualizar"
            color="neutral"
            variant="soft"
            :loading="loading"
            class="w-full justify-center sm:w-auto"
            @click="carregarAuditoria(offset)"
          />
        </div>
      </template>

      <div
        class="max-w-full overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700"
        role="region"
        aria-label="Eventos de auditoria"
        tabindex="0"
      >
        <table class="min-w-[64rem] divide-y divide-slate-200 text-sm dark:divide-slate-700">
          <caption class="sr-only">
            Eventos de auditoria LGPD, com data, ação, usuário, entidade, IP e descrição.
          </caption>
          <thead class="bg-slate-100 text-left text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <tr>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                Data/Hora
              </th>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                Ação
              </th>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                Usuário
              </th>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                Entidade
              </th>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                IP
              </th>
              <th
                scope="col"
                class="px-4 py-3 font-medium"
              >
                Descrição
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white dark:divide-slate-800 dark:bg-slate-900">
            <tr v-if="loading">
              <td
                colspan="6"
                class="px-4 py-8 text-center text-slate-600 dark:text-slate-400"
              >
                Carregando auditoria...
              </td>
            </tr>
            <tr v-else-if="!eventos.length">
              <td
                colspan="6"
                class="px-4 py-8 text-center text-slate-600 dark:text-slate-400"
              >
                Nenhum evento encontrado.
              </td>
            </tr>
            <template v-else>
              <tr
                v-for="evento in eventos"
                :key="evento.id"
                class="hover:bg-slate-50 dark:hover:bg-slate-800/70"
              >
                <td class="whitespace-nowrap px-4 py-3 text-slate-700 dark:text-slate-300">
                  {{ formatarData(evento.created_at) }}
                </td>
                <td class="whitespace-nowrap px-4 py-3">
                  <UBadge
                    :label="evento.acao"
                    :color="acoesCriticas.has(evento.acao) ? 'warning' : 'neutral'"
                    variant="soft"
                  />
                </td>
                <td class="px-4 py-3 text-slate-700 dark:text-slate-300">
                  {{ usuarioLabel(evento) }}
                </td>
                <td class="px-4 py-3 text-slate-700 dark:text-slate-300">
                  {{ entidadeLabel(evento) }}
                </td>
                <td class="px-4 py-3 text-slate-700 dark:text-slate-300">
                  {{ evento.ip || '-' }}
                </td>
                <td class="max-w-xl px-4 py-3 text-slate-600 dark:text-slate-300">
                  {{ evento.descricao || '-' }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <template #footer>
        <div class="flex flex-col justify-between gap-3 sm:flex-row">
          <UButton
            label="Anterior"
            icon="i-lucide-chevron-left"
            color="neutral"
            variant="soft"
            :disabled="offset === 0 || loading"
            class="w-full justify-center sm:w-auto"
            @click="paginaAnterior"
          />
          <UButton
            label="Próxima"
            trailing-icon="i-lucide-chevron-right"
            color="neutral"
            variant="soft"
            :disabled="!hasMore || loading"
            class="w-full justify-center sm:w-auto"
            @click="proximaPagina"
          />
        </div>
      </template>
    </UCard>
  </div>
</template>
