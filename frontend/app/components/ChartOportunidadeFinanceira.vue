<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, DoughnutController } from 'chart.js'
import type { ChartOptions, TooltipItem } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const props = defineProps<{
  labels: string[]
  dados: number[]
}>()

const cores = ['#22c55e', '#0ea5e9', '#d97706', '#8b5cf6', '#ef4444', '#f97316', '#06b6d4']

const data = computed(() => ({
  labels: props.labels,
  datasets: [{
    data: props.dados,
    backgroundColor: cores.slice(0, props.labels.length),
    borderWidth: 0
  }]
}))

const options: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '50%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: { padding: 16, usePointStyle: true, font: { size: 12 } }
    },
    tooltip: {
      callbacks: {
        label: (ctx: TooltipItem<'doughnut'>) => {
          const valores = ctx.dataset.data.map(valor => Number(valor || 0))
          const total = valores.reduce((acc, valor) => acc + valor, 0)
          const valor = Number(ctx.parsed || 0)
          const pct = total > 0 ? ((valor / total) * 100).toFixed(1) : '0'
          return ` ${ctx.label}: R$ ${valor.toLocaleString('pt-BR')} (${pct}%)`
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
        aria-label="Gráfico de oportunidade financeira por categoria"
      />
      <template #fallback>
        <div class="aspect-square w-48 max-w-full animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-800" />
      </template>
    </ClientOnly>
  </div>
</template>
