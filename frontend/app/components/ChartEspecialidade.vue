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

const itens = computed(() => props.labels.map((label, index) => ({
  label,
  total: props.dados[index] ?? 0,
  color: cores[index % cores.length]
})))

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
      display: false
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
  <div class="flex w-full min-w-0 items-center justify-center gap-3 sm:gap-4">
    <div class="h-40 w-40 shrink-0 sm:h-48 sm:w-48">
      <ClientOnly>
        <Doughnut
          :data="data"
          :options="options"
          class="h-full w-full"
          role="img"
          aria-label="Gráfico de pacientes por especialidade"
        />
        <template #fallback>
          <div class="flex h-full items-center justify-center">
            <div class="aspect-square w-full max-w-full animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-800" />
          </div>
        </template>
      </ClientOnly>
    </div>

    <ul
      class="max-h-56 min-w-0 flex-1 overflow-y-auto sm:max-h-64"
      aria-label="Especialidades com pacientes em no-show"
    >
      <li
        v-for="item in itens"
        :key="item.label"
        class="flex items-center gap-2 py-1"
      >
        <span
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: item.color }"
        />
        <span
          class="min-w-0 truncate text-sm text-foreground"
          :title="item.label"
        >
          {{ item.label }}
        </span>
        <span class="ml-auto shrink-0 text-sm text-muted tabular-nums">
          {{ item.total }}
        </span>
      </li>
    </ul>
  </div>
</template>
