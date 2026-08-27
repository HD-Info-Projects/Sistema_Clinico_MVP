<script setup lang="ts">
import type { CalendarDate } from '@internationalized/date'
import { calcularDataProvavelParto, calcularIdadeGestacional, formatarDataBR, formatarIdadeGestacional } from '~/utils/obstetricia'

const dum = shallowRef<CalendarDate | null>(null)
const hoje = ref(new Date())
const copiado = ref(false)

function calendarDateToISO(date: CalendarDate): string {
  const month = String(date.month).padStart(2, '0')
  const day = String(date.day).padStart(2, '0')
  return `${date.year}-${month}-${day}`
}

let intervalo: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  intervalo = setInterval(() => {
    hoje.value = new Date()
  }, 60000)
})

onUnmounted(() => {
  if (intervalo) clearInterval(intervalo)
})

const idadeGestacional = computed(() => {
  if (!dum.value) return null
  return calcularIdadeGestacional(calendarDateToISO(dum.value), hoje.value)
})

const dataProvavelParto = computed(() => {
  if (!dum.value) return null
  return calcularDataProvavelParto(calendarDateToISO(dum.value))
})

const idadeGestacionalFormatada = computed(() => {
  if (!idadeGestacional.value) return ''
  return formatarIdadeGestacional(idadeGestacional.value.semanas, idadeGestacional.value.dias)
})

const dataProvavelPartoFormatada = computed(() => {
  if (!dataProvavelParto.value) return ''
  return formatarDataBR(dataProvavelParto.value)
})

const resultadoTexto = computed(() => {
  if (!idadeGestacional.value || !dataProvavelParto.value) return ''
  return `IG: ${idadeGestacionalFormatada.value} | DPP: ${dataProvavelPartoFormatada.value}`
})

function limpar() {
  dum.value = null
}

function copiarResultado() {
  if (resultadoTexto.value) {
    navigator.clipboard.writeText(resultadoTexto.value)
    copiado.value = true
    setTimeout(() => {
      copiado.value = false
    }, 2000)
  }
}
</script>

<template>
  <div class=" p-4 space-y-4">
    <div class="flex items-center gap-2">
      <UIcon
        name="i-lucide-baby"
        class="text-primary text-xl"
      />
      <h3 class="font-semibold text-sm">
        Calculadora DUM
      </h3>
    </div>

    <UFormField label="Data da Última Menstruação">
      <UInputDate
        v-model="dum"
        class="w-full"
      />
    </UFormField>

    <div
      v-if="idadeGestacional"
      class="space-y-3 p-3 bg-primary/5 rounded-lg border border-primary/20"
    >
      <div class="space-y-1">
        <p class="text-xs text-muted uppercase tracking-wide">
          Idade Gestacional
        </p>
        <p class="text-lg font-bold text-primary">
          {{ idadeGestacionalFormatada }}
        </p>
      </div>

      <div class="space-y-1">
        <p class="text-xs text-muted uppercase tracking-wide">
          Data Provável do Parto
        </p>
        <p class="text-lg font-bold text-primary">
          {{ dataProvavelPartoFormatada }}
        </p>
      </div>
    </div>

    <div
      v-else-if="dum"
      class="p-3 bg-warning/10 rounded-lg border border-warning/20"
    >
      <p class="text-sm text-warning">
        Data inválida ou futura
      </p>
    </div>

    <div class="flex gap-2">
      <UButton
        label="Limpar"
        color="neutral"
        variant="ghost"
        size="sm"
        :disabled="!dum"
        @click="limpar"
      />
      <UButton
        v-if="resultadoTexto"
        :label="copiado ? 'Copiado!' : 'Copiar Resultado'"
        :color="copiado ? 'success' : 'primary'"
        :icon="copiado ? 'i-lucide-check' : 'i-lucide-copy'"
        variant="soft"
        size="sm"
        class="flex-1"
        @click="copiarResultado"
      />
    </div>
  </div>
</template>
