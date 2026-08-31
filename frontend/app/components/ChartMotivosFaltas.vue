<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, DoughnutController } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const props = defineProps<{
  total: number
  items: Array<{ label: string, total: number, color?: string }>
}>()

const colors = ref<string[]>(['#0ea5e9', '#d97706', '#5f7198', '#737373'])

onMounted(() => {
  const el = document.documentElement
  colors.value = [
    getComputedStyle(el).getPropertyValue('--color-info-500').trim() || '#0ea5e9',
    getComputedStyle(el).getPropertyValue('--color-warning-500').trim() || '#d97706',
    getComputedStyle(el).getPropertyValue('--color-secondary-500').trim() || '#5f7198',
    getComputedStyle(el).getPropertyValue('--color-neutral-500').trim() || '#737373'
  ]
})

const data = computed(() => ({
  labels: props.items.map(item => item.label),
  datasets: [
    {
      data: props.items.map(item => item.total),
      backgroundColor: props.items.map((item, index) => item.color || colors.value[index % colors.value.length]),
      borderWidth: 0
    }
  ]
}))

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
  <div class="flex h-56 w-full min-w-0 justify-center sm:h-64">
    <div class="relative h-full w-full max-w-sm">
      <ClientOnly>
        <Doughnut
          :data="data"
          :options="options"
          class="mx-auto h-full max-w-full"
          role="img"
          aria-label="Gráfico dos motivos de faltas"
        />
        <template #fallback>
          <div class="flex h-full items-center justify-center gap-4 sm:gap-8">
            <div class="size-40 rounded-full bg-neutral-200 animate-pulse sm:size-48 dark:bg-neutral-800" />
            <div class="space-y-3">
              <div
                v-for="i in 3"
                :key="i"
                class="h-4 w-16 rounded bg-neutral-200 animate-pulse sm:w-24 dark:bg-neutral-800"
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
  </div>
</template>
