<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import type { ChartOptions, TooltipItem } from 'chart.js'

ChartJS.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps<{
  medicos: string[]
  taxas: number[]
}>()

const barColor = ref<string>('#22c55e')

onMounted(() => {
  const el = document.documentElement
  barColor.value = getComputedStyle(el).getPropertyValue('--color-success-500').trim() || '#22c55e'
})

const data = computed(() => ({
  labels: props.medicos,
  datasets: [
    {
      label: 'Conversão (%)',
      data: props.taxas,
      backgroundColor: barColor.value,
      borderRadius: 4,
      borderSkipped: false
    }
  ]
}))

const options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: TooltipItem<'bar'>) => ` ${ctx.parsed.x || 0}% de conversão`
      }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      ticks: { callback: value => `${value}%` }
    }
  }
}
</script>

<template>
  <ClientOnly>
    <div class="relative h-56 w-full min-w-0 sm:h-64">
      <Bar
        :data="data"
        :options="options"
        class="h-full w-full"
        role="img"
        aria-label="Gráfico da taxa de conversão por médico"
      />
    </div>
    <template #fallback>
      <div class="flex h-56 items-center justify-center sm:h-64">
        <div class="w-full h-48 bg-neutral-200 dark:bg-neutral-800 rounded animate-pulse" />
      </div>
    </template>
  </ClientOnly>
</template>
