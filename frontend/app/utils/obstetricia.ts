export function calcularIdadeGestacional(dumISO: string, hoje: Date = new Date()): { semanas: number, dias: number, totalDias: number } | null {
  if (!dumISO) return null

  const dum = new Date(dumISO + 'T00:00:00')
  if (isNaN(dum.getTime())) return null

  const diffMs = hoje.getTime() - dum.getTime()
  const totalDias = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (totalDias < 0) return null

  const semanas = Math.floor(totalDias / 7)
  const dias = totalDias % 7

  return { semanas, dias, totalDias }
}

export function calcularDataProvavelParto(dumISO: string): string | null {
  if (!dumISO) return null

  const dum = new Date(dumISO + 'T00:00:00')
  if (isNaN(dum.getTime())) return null

  dum.setDate(dum.getDate() + 280)

  const y = dum.getFullYear()
  const m = String(dum.getMonth() + 1).padStart(2, '0')
  const d = String(dum.getDate()).padStart(2, '0')

  return `${y}-${m}-${d}`
}

export function formatarIdadeGestacional(semanas: number, dias: number): string {
  if (semanas === 0) return `${dias} dia${dias !== 1 ? 's' : ''}`
  if (dias === 0) return `${semanas} semana${semanas !== 1 ? 's' : ''}`
  return `${semanas} semana${semanas !== 1 ? 's' : ''} e ${dias} dia${dias !== 1 ? 's' : ''}`
}

export function formatarDataBR(dataISO: string): string {
  if (!dataISO) return ''
  const d = new Date(dataISO + 'T12:00:00')
  if (isNaN(d.getTime())) return ''

  const dia = String(d.getDate()).padStart(2, '0')
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const ano = d.getFullYear()

  return `${dia}/${mes}/${ano}`
}
