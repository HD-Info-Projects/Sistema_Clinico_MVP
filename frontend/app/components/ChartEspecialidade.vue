<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, DoughnutController } from 'chart.js'
import type { ChartOptions, TooltipItem } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const props = defineProps<{
  labels: string[]
  dados: number[]
}>()

const cores = ['#0ea5e9', '#d97706', '#22c55e', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4']

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
      position: 'right' as const,
      labels: { padding: 16, usePointStyle: true, font: { size: 12 } }
    },
    tooltip: {
      callbacks: {
        label: (ctx: TooltipItem<'doughnut'>) => {
          const total = Number(ctx.parsed || 0)
          return ` ${total} paciente${total !== 1 ? 's' : ''}`
        }
      }
    }
  }
}
</script>

<template>
  <div class="relative h-64">
    <ClientOnly>
      <Doughnut
        :data="data"
        :options="options"
        class="h-full w-full"
      />
      <template #fallback>
        <div class="flex h-full items-center justify-center">
          <div class="size-48 rounded-full bg-neutral-200 dark:bg-neutral-800 animate-pulse" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>
