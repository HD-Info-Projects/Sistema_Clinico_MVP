export function calcularMinutosDesde(horarioOriginal: string, agora: Date = new Date()) {
  const [h, m] = horarioOriginal.split(':').map(Number) as [number, number]
  const date = new Date(agora)
  date.setHours(h, m, 0, 0)
  return Math.max(0, Math.round((agora.getTime() - date.getTime()) / 60000))
}

export function formatarTempoEspera(minutos: number) {
  if (minutos < 1) return '0 min'
  if (minutos < 60) return `${minutos} min`
  const horas = Math.floor(minutos / 60)
  const resto = minutos % 60
  return resto ? `${horas}h ${resto}min` : `${horas}h`
}

const DIAS = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado']
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

export function formatarDiaDaSemana(d: Date) {
  return DIAS[d.getDay()]
}

export function formatarDataCompleta(d: Date) {
  return `${DIAS[d.getDay()]}, ${d.getDate()} de ${MESES[d.getMonth()]}`
}

export function formatarHora(d: Date) {
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export function formatarDataISO(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function formatarDataHistorico(dataStr: string): string {
  if (!dataStr) return ''
  const d = new Date(dataStr)
  if (isNaN(d.getTime())) return ''
  const dia = String(d.getDate()).padStart(2, '0')
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const ano = d.getFullYear()
  return `${dia}/${mes}/${ano}`
}

export function getSaudacao(d: Date = new Date()) {
  const hour = d.getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 18) return 'Boa tarde'
  return 'Boa noite'
}

export function calcularIdade(dataNascimento: string | null | undefined, hoje: Date = new Date()): number | null {
  if (!dataNascimento) return null
  const nasc = new Date(dataNascimento)
  if (Number.isNaN(nasc.getTime())) return null

  let idade = hoje.getFullYear() - nasc.getFullYear()
  const mes = hoje.getMonth() - nasc.getMonth()
  if (mes < 0 || (mes === 0 && hoje.getDate() < nasc.getDate())) idade -= 1
  return idade < 0 ? null : idade
}

export function formatarIdade(
  dataNascimento: string | null | undefined,
  { semAnos = false, semDados = false }: { semAnos?: boolean, semDados?: boolean } = {}
): string {
  const idade = calcularIdade(dataNascimento)
  if (idade === null) return semDados ? 'Idade não informada' : ''
  return semAnos ? String(idade) : `${idade} ${idade === 1 ? 'ano' : 'anos'}`
}
