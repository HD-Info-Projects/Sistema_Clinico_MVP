<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, DoughnutController } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const props = defineProps<{
  total: number
  agendados?: number
  fila: number
  emAtendimento: number
  atendidos: number
  faltas: number
}>()

const colors = ref({
  warning: '#f59e0b',
  primary: '#737373',
  secondary: '#5f7198',
  success: '#22c55e',
  error: '#ef4444'
})

onMounted(() => {
  const el = document.documentElement
  colors.value = {
    warning: getComputedStyle(el).getPropertyValue('--color-warning-500').trim() || '#f59e0b',
    primary: getComputedStyle(el).getPropertyValue('--color-primary-500').trim() || '#737373',
    secondary: getComputedStyle(el).getPropertyValue('--color-secondary-500').trim() || '#5f7198',
    success: getComputedStyle(el).getPropertyValue('--color-success-500').trim() || '#22c55e',
    error: getComputedStyle(el).getPropertyValue('--color-error-500').trim() || '#ef4444'
  }
})

const data = computed(() => {
  const hasAgendados = typeof props.agendados === 'number'
  const labels = ['Em espera', 'Em Atendimento', 'Atendidos', 'Faltas']
  const values = [props.fila, props.emAtendimento, props.atendidos, props.faltas]
  const backgroundColor = [colors.value.primary, colors.value.warning, colors.value.success, colors.value.error]

  if (hasAgendados) {
    labels.unshift('Agendados')
    values.unshift(props.agendados ?? 0)
    backgroundColor.unshift(colors.value.secondary)
  }

  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor,
        borderWidth: 0
      }
    ]
  }
})

const options = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        padding: 16,
        usePointStyle: true,
        font: { size: 12 }
      }
    },
    tooltip: {
      callbacks: {
        label: (ctx: { parsed: number, dataIndex: number }) => {
          return ` ${ctx.parsed} paciente${ctx.parsed !== 1 ? 's' : ''}`
        }
      }
    }
  }
}
</script>

<template>
  <div class="relative flex min-h-56 w-full min-w-0 items-center justify-center sm:min-h-64">
    <ClientOnly>
      <Doughnut
        :data="data"
        :options="options"
        class="aspect-square h-auto max-h-64 w-full max-w-full"
        role="img"
        aria-label="Gráfico de resumo dos atendimentos"
      />
      <template #fallback>
        <div class="flex max-w-full items-center gap-4 sm:gap-8">
          <div class="aspect-square w-48 max-w-full animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-800" />
          <div class="space-y-3">
            <div
              v-for="i in 4"
              :key="i"
              class="h-4 w-24 bg-neutral-200 dark:bg-neutral-800 rounded animate-pulse"
            />
          </div>
        </div>
      </template>
    </ClientOnly>
    <div class="pointer-events-none absolute inset-0 mb-8 flex items-center justify-center">
      <div class="text-center">
        <p class="text-3xl font-bold sm:text-4xl">
          {{ props.total }}
        </p>
        <p class="text-xs text-muted">
          Total
        </p>
      </div>
    </div>
  </div>
</template>
