<script setup lang="ts">
import PagamentosFiltros from '~/features/financeiro/components/PagamentosFiltros.vue'
import { listarPagamentos } from '~/features/financeiro/services/financeiroService'
import { resolverPeriodoPagamento } from '~/features/financeiro/utils/periodos'
import type { FormaPagamento, PagamentosFiltrosForm, PagamentosResponse, PagamentoStatus } from '~/features/financeiro/types'
import { formatarCpf } from '~/utils/masks'

definePageMeta({ layout: 'financeiro' })

const openNav = inject<() => void>('openNav', () => {})
const auth = useAuthStore()
const userName = computed(() => auth.user?.nome || 'Usuário')
const loading = ref(true)
const errorMsg = ref('')
const page = ref(1)
const pageSize = 20
const filtros = ref<PagamentosFiltrosForm>({
  periodo: 'hoje', paciente: '', cpf: '', status: 'todos', dataIni: '', dataFim: ''
})
const filtrosAplicados = ref<PagamentosFiltrosForm>({ ...filtros.value })

function respostaVazia(): PagamentosResponse {
  return {
    items: [], total: 0, page: 1, pageSize,
    resumo: { conciliados: 0, pendentes: 0, divergentes: 0, totalBrutoCentavos: 0 }
  }
}

const dados = ref<PagamentosResponse>(respostaVazia())
let requestId = 0
let montado = false

const formasPagamento: Record<FormaPagamento, { label: string, icon: string }> = {
  'cartao-credito': { label: 'Cartão de crédito', icon: 'i-lucide-credit-card' },
  'pix': { label: 'Pix', icon: 'i-lucide-qr-code' },
  'dinheiro': { label: 'Dinheiro', icon: 'i-lucide-banknote' },
  'cartao-debito': { label: 'Cartão de débito', icon: 'i-lucide-wallet-cards' }
}

const statusPagamento: Record<PagamentoStatus, { label: string, color: 'success' | 'warning' | 'error' }> = {
  conciliado: { label: 'Conciliado', color: 'success' },
  pendente: { label: 'Pendente', color: 'warning' },
  divergente: { label: 'Divergente', color: 'error' }
}

const formatoMoeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
function formatarValor(centavos: number) {
  return formatoMoeda.format(centavos / 100)
}

function formatarData(data: string) {
  return data.split('-').reverse().join('/')
}

async function carregarPagamentos() {
  const currentRequest = ++requestId
  const unidadeId = auth.activeClinicaId
  loading.value = true
  errorMsg.value = ''

  if (!unidadeId) {
    dados.value = respostaVazia()
    errorMsg.value = 'Selecione uma unidade para carregar os pagamentos.'
    loading.value = false
    return
  }

  try {
    const intervalo = resolverPeriodoPagamento(filtrosAplicados.value.periodo, filtrosAplicados.value)
    const response = await listarPagamentos({
      ...intervalo,
      unidadeId,
      paciente: filtrosAplicados.value.paciente,
      cpf: filtrosAplicados.value.cpf,
      status: filtrosAplicados.value.status === 'todos' ? undefined : filtrosAplicados.value.status,
      page: page.value,
      pageSize
    })
    if (currentRequest !== requestId || unidadeId !== auth.activeClinicaId) return
    dados.value = response
    page.value = response.page
  } catch (error) {
    if (currentRequest !== requestId || unidadeId !== auth.activeClinicaId) return
    dados.value = respostaVazia()
    errorMsg.value = error instanceof Error ? error.message : 'Erro ao carregar os pagamentos.'
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

function aplicarFiltros() {
  filtrosAplicados.value = { ...filtros.value }
  page.value = 1
  void carregarPagamentos()
}

function mudarPagina(novaPagina: number) {
  if (novaPagina === page.value || loading.value) return
  page.value = novaPagina
  void carregarPagamentos()
}

watch(() => auth.activeClinicaId, () => {
  if (!montado) return
  dados.value = respostaVazia()
  page.value = 1
  void carregarPagamentos()
})

onMounted(() => {
  montado = true
  void carregarPagamentos()
})

onBeforeUnmount(() => {
  montado = false
  requestId++
})
</script>

<template>
  <div>
    <UHeader
      title="Gerenciamento de pagamentos"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-menu"
          color="neutral"
          variant="ghost"
          class="lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
            class="hidden lg:inline-flex"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>

    <div class="min-h-screen min-w-0 space-y-6 bg-muted p-3 sm:space-y-8 sm:p-6">
      <PagamentosFiltros
        v-model="filtros"
        :loading="loading"
        @aplicar="aplicarFiltros"
      />

      <UAlert
        v-if="errorMsg"
        :title="errorMsg"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
      />

      <div class="grid w-full grid-cols-2 items-stretch gap-4 xl:grid-cols-4">
        <CardInformativo
          class="h-full"
          titulo="Pagamentos conciliados"
          :valor="dados.resumo.conciliados"
          cor="success"
          icone="i-lucide-circle-check"
          :loading="loading"
        />
        <CardInformativo
          class="h-full"
          titulo="Pagamentos pendentes"
          :valor="dados.resumo.pendentes"
          cor="warning"
          icone="i-lucide-clock"
          :loading="loading"
        />
        <CardInformativo
          class="h-full"
          titulo="Pagamentos divergentes"
          :valor="dados.resumo.divergentes"
          cor="error"
          icone="i-lucide-triangle-alert"
          :loading="loading"
        />
        <CardInformativo
          class="h-full"
          titulo="Total financeiro filtrado"
          :valor="formatarValor(dados.resumo.totalBrutoCentavos)"
          cor="primary"
          icone="i-lucide-coins"
          :loading="loading"
        />
      </div>

      <UCard class="w-full">
        <template #title>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="min-w-0">
              <p class="text-lg font-medium">
                Pagamentos
              </p>
              <p class="text-sm text-muted">
                {{ dados.total }} registro{{ dados.total !== 1 ? 's' : '' }} encontrado{{ dados.total !== 1 ? 's' : '' }}
              </p>
            </div>
          </div>
        </template>

        <div
          v-if="loading"
          role="status"
          aria-label="Carregando pagamentos"
          class="space-y-3 py-4"
        >
          <div
            v-for="linha in 6"
            :key="linha"
            class="grid grid-cols-1 gap-3 rounded-lg border border-muted p-3 sm:grid-cols-2 md:grid-cols-[max-content_2fr_1.5fr_1.5fr_max-content_max-content]"
          >
            <USkeleton class="h-5 w-20" />
            <div class="flex min-w-0 items-center gap-3">
              <USkeleton class="size-8 shrink-0 rounded-full" />
              <div class="min-w-0 space-y-2">
                <USkeleton class="h-5 w-40 max-w-full" />
                <USkeleton class="h-4 w-28 max-w-full" />
              </div>
            </div>
            <USkeleton class="h-5 w-28 max-w-full" />
            <USkeleton class="h-5 w-28 max-w-full" />
            <USkeleton class="h-5 w-24" />
            <USkeleton class="h-6 w-24 rounded-full" />
          </div>
        </div>

        <p
          v-else-if="!dados.items.length"
          class="py-4 text-sm text-muted"
        >
          Nenhum pagamento encontrado para os filtros selecionados.
        </p>

        <div
          v-else
          class="flex flex-col gap-2"
        >
          <UPageCard
            v-for="item in dados.items"
            :key="item.id"
            :to="`/financeiro/pacientes/${item.paciente.id}`"
            :aria-label="`Abrir gerenciamento de ${item.paciente.nome}, pagamento de ${formatarValor(item.valorBrutoCentavos)}`"
            variant="ghost"
            class="cursor-pointer rounded-none border-b border-muted"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 md:grid-cols-[max-content_minmax(0,2fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_max-content_max-content]">
              <div class="hidden w-min pr-3 md:block">
                <p class="text-sm font-bold text-muted">
                  Data
                </p>
                <p class="whitespace-nowrap pt-2 font-mono text-sm">
                  {{ formatarData(item.data) }}
                </p>
              </div>

              <div class="sm:col-span-2 md:col-span-1">
                <div class="flex min-w-0 items-center gap-3">
                  <UAvatar
                    :alt="item.paciente.nome"
                    color="primary"
                    size="sm"
                    class="shrink-0"
                  />
                  <div class="min-w-0">
                    <p class="wrap-break-word font-medium">
                      {{ item.paciente.nome }}
                    </p>
                    <p class="text-xs text-muted">
                      CPF: {{ formatarCpf(item.paciente.cpf) }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="md:hidden">
                <p class="text-sm font-bold text-muted">
                  Data
                </p>
                <p class="whitespace-nowrap font-mono text-sm">
                  {{ formatarData(item.data) }}
                </p>
              </div>

              <div class="min-w-0">
                <p class="text-sm font-bold text-muted">
                  Atendimento
                </p>
                <p class="wrap-break-word text-sm">
                  {{ item.atendimento.descricao }}
                </p>
                <p class="wrap-break-word text-xs text-muted">
                  {{ item.atendimento.id }}
                </p>
              </div>

              <div class="min-w-0">
                <p class="text-sm font-bold text-muted">
                  Forma de pagamento
                </p>
                <div class="flex items-center gap-2 text-sm">
                  <UIcon
                    :name="formasPagamento[item.formaPagamento].icon"
                    class="size-4 shrink-0 text-primary"
                  />
                  <span class="wrap-break-word">{{ formasPagamento[item.formaPagamento].label }}</span>
                </div>
              </div>

              <div>
                <p class="text-sm font-bold text-muted">
                  Valor bruto
                </p>
                <p class="whitespace-nowrap text-sm font-semibold tabular-nums">
                  {{ formatarValor(item.valorBrutoCentavos) }}
                </p>
              </div>

              <div>
                <p class="text-sm font-bold text-muted">
                  Status
                </p>
                <UBadge
                  :label="statusPagamento[item.status].label"
                  :color="statusPagamento[item.status].color"
                  variant="subtle"
                />
              </div>
            </div>
          </UPageCard>
        </div>

        <div class="flex flex-col gap-3 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-sm text-muted">
            Página {{ page }} · {{ pageSize }} por página
          </p>
          <UPagination
            :page="page"
            :items-per-page="pageSize"
            :total="dados.total"
            :sibling-count="1"
            :disabled="loading"
            :ui="{ list: 'flex flex-wrap items-center gap-1 justify-center' }"
            @update:page="mudarPagina"
          />
        </div>
      </UCard>
    </div>
  </div>
</template>
