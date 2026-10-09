import type { PeriodoPagamento } from '../types'

export interface IntervaloPagamento {
  dataIni: string
  dataFim: string
}

function dataISO(data: Date) {
  return data.toISOString().slice(0, 10)
}

// Use calendar dates, not elapsed hours: DST must not change a selected day.
export function dataCalendario(referencia = new Date()) {
  return new Date(Date.UTC(referencia.getFullYear(), referencia.getMonth(), referencia.getDate()))
}

export function dataPagamentoValida(valor: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(valor)) return false
  const data = new Date(`${valor}T00:00:00Z`)
  return !Number.isNaN(data.getTime()) && dataISO(data) === valor
}

export function validarIntervaloPagamento(dataIni: string, dataFim: string): string | null {
  if (!dataIni || !dataFim) return 'Informe a data inicial e a data final.'
  if (!dataPagamentoValida(dataIni) || !dataPagamentoValida(dataFim)) return 'Informe datas válidas.'
  if (dataIni > dataFim) return 'A data final deve ser igual ou posterior à data inicial.'
  return null
}

export function resolverPeriodoPagamento(
  periodo: PeriodoPagamento,
  personalizado: IntervaloPagamento,
  referencia = new Date()
): IntervaloPagamento {
  if (periodo === 'personalizado') {
    const error = validarIntervaloPagamento(personalizado.dataIni, personalizado.dataFim)
    if (error) throw new Error(error)
    return { ...personalizado }
  }

  const inicio = dataCalendario(referencia)
  const fim = new Date(inicio)

  switch (periodo) {
    case 'hoje': break
    case 'ontem':
      inicio.setUTCDate(inicio.getUTCDate() - 1)
      fim.setUTCDate(fim.getUTCDate() - 1)
      break
    case 'ultimos-7-dias':
      inicio.setUTCDate(inicio.getUTCDate() - 6)
      break
    case 'este-mes':
      inicio.setUTCDate(1)
      fim.setUTCMonth(fim.getUTCMonth() + 1, 0)
      break
    case 'mes-anterior':
      inicio.setUTCMonth(inicio.getUTCMonth() - 1, 1)
      fim.setUTCDate(0)
      break
  }

  return { dataIni: dataISO(inicio), dataFim: dataISO(fim) }
}
