<script setup lang="ts">
import type { PagamentosFiltrosForm, PagamentoStatus, PeriodoPagamento } from '../types'
import { validarIntervaloPagamento } from '../utils/periodos'
import { formatarCpf } from '~/utils/masks'

const filtros = defineModel<PagamentosFiltrosForm>({ required: true })
const props = defineProps<{ loading: boolean }>()
const emit = defineEmits<{ aplicar: [] }>()
const tentouAplicar = ref(false)

const periodos: { label: string, value: PeriodoPagamento }[] = [
  { label: 'Hoje', value: 'hoje' },
  { label: 'Ontem', value: 'ontem' },
  { label: 'Últimos 7 dias', value: 'ultimos-7-dias' },
  { label: 'Este mês', value: 'este-mes' },
  { label: 'Mês anterior', value: 'mes-anterior' },
  { label: 'Período personalizado', value: 'personalizado' }
]

const status: { label: string, value: PagamentoStatus | 'todos' }[] = [
  { label: 'Todos', value: 'todos' },
  { label: 'Conciliado', value: 'conciliado' },
  { label: 'Pendente', value: 'pendente' },
  { label: 'Divergente', value: 'divergente' }
]

const erroPeriodo = computed(() => filtros.value.periodo === 'personalizado'
  ? validarIntervaloPagamento(filtros.value.dataIni, filtros.value.dataFim)
  : null)

function aplicar() {
  tentouAplicar.value = true
  if (!erroPeriodo.value) emit('aplicar')
}
</script>

<template>
  <UCard class="w-full">
    <template #title>
      <p class="text-lg font-medium">
        Filtros de pagamentos
      </p>
    </template>

    <form
      class="space-y-4"
      @submit.prevent="aplicar"
    >
      <div class="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 xl:grid-cols-[1.2fr_1.5fr_1fr_1fr_auto]">
        <UFormField
          label="Período"
          name="periodo"
          class="w-full"
        >
          <USelect
            v-model="filtros.periodo"
            :items="periodos"
            value-key="value"
            size="sm"
            class="w-full"
          />
        </UFormField>
        <UFormField
          label="Paciente"
          name="paciente"
          class="w-full"
        >
          <UInput
            v-model="filtros.paciente"
            icon="i-lucide-search"
            placeholder="Buscar paciente..."
            size="sm"
            class="w-full"
          />
        </UFormField>
        <UFormField
          label="CPF"
          name="cpf"
          class="w-full"
        >
          <UInput
            :model-value="filtros.cpf"
            placeholder="Digite o CPF"
            inputmode="numeric"
            maxlength="14"
            size="sm"
            class="w-full"
            @update:model-value="filtros.cpf = formatarCpf(String($event ?? ''))"
          />
        </UFormField>
        <UFormField
          label="Status"
          name="status"
          class="w-full"
        >
          <USelect
            v-model="filtros.status"
            :items="status"
            value-key="value"
            size="sm"
            class="w-full"
          />
        </UFormField>
        <UButton
          type="submit"
          label="Aplicar filtros"
          icon="i-lucide-filter"
          size="sm"
          color="primary"
          class="min-h-10 w-full justify-center sm:col-span-2 xl:col-span-1 xl:w-auto"
          :loading="props.loading"
          :disabled="props.loading"
        />
      </div>

      <div
        v-if="filtros.periodo === 'personalizado'"
        class="grid grid-cols-1 items-start gap-3 sm:grid-cols-2 xl:max-w-xl"
      >
        <UFormField
          label="Data inicial"
          name="dataIni"
          required
          :error="tentouAplicar && !filtros.dataIni ? 'Informe a data inicial.' : undefined"
        >
          <UInput
            v-model="filtros.dataIni"
            type="date"
            size="sm"
            class="w-full"
            :max="filtros.dataFim || undefined"
          />
        </UFormField>
        <UFormField
          label="Data final"
          name="dataFim"
          required
          :error="tentouAplicar ? erroPeriodo || undefined : undefined"
        >
          <UInput
            v-model="filtros.dataFim"
            type="date"
            size="sm"
            class="w-full"
            :min="filtros.dataIni || undefined"
          />
        </UFormField>
      </div>
    </form>
  </UCard>
</template>
