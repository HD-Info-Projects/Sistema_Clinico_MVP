<script setup lang="ts">
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement, LineController } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement, LineController)

const props = defineProps<{
  labels: string[]
  dados: number[]
}>()

const lineColor = ref('#0ea5e9')

onMounted(() => {
  const el = document.documentElement
  lineColor.value = getComputedStyle(el).getPropertyValue('--color-primary-500').trim() || '#0ea5e9'
})

const data = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Faltas',
      data: props.dados,
      borderColor: lineColor.value,
      backgroundColor: lineColor.value,
      pointBackgroundColor: lineColor.value,
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 7,
      borderWidth: 3,
      tension: 0.3,
      fill: false
    }
  ]
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        label: (ctx: any) => ` ${ctx.parsed.y} paciente${ctx.parsed.y !== 1 ? 's' : ''}`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { stepSize: 1, precision: 0 }
    }
  }
}
</script>

<template>
  <ClientOnly>
    <div class="relative h-56 w-full min-w-0 sm:h-64">
      <Line
        :data="data"
        :options="options"
        class="h-full w-full"
        role="img"
        aria-label="Gráfico de faltas por dia da semana"
      />
    </div>
    <template #fallback>
      <div class="flex h-56 items-center justify-center sm:h-64">
        <div class="w-full h-48 bg-neutral-200 dark:bg-neutral-800 rounded animate-pulse" />
      </div>
    </template>
  </ClientOnly>
</template>
