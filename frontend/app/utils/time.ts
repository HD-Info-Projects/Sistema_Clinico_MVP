export function calcularMinutosDesde(horarioOriginal: string, agora: Date = new Date()) {
  const horario = normalizarHorario(horarioOriginal)
  if (!/^\d{2}:\d{2}$/.test(horario)) return 0

  const [h, m] = horario.split(':').map(Number) as [number, number]
  const date = new Date(agora)
  date.setHours(h, m, 0, 0)
  return Math.max(0, Math.round((agora.getTime() - date.getTime()) / 60000))
}

export function minutosDoHorario(valor: unknown): number {
  const horario = normalizarHorario(valor)
  if (!/^\d{2}:\d{2}$/.test(horario)) return Number.MAX_SAFE_INTEGER
  const [hora, minuto] = horario.split(':').map(Number) as [number, number]
  return hora * 60 + minuto
}

/** Converte horários vindos como HHmm, HH:mm ou HH:mm:ss para HH:mm. */
export function normalizarHorario(valor: unknown): string {
  if (valor === null || valor === undefined) return ''

  const texto = String(valor).trim()
  if (!texto) return ''

  const comSeparador = texto.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/)
  if (comSeparador) {
    const hora = Number(comSeparador[1])
    const minuto = Number(comSeparador[2])
    if (hora < 24 && minuto < 60) {
      return `${String(hora).padStart(2, '0')}:${String(minuto).padStart(2, '0')}`
    }
    return ''
  }

  if (/^\d{1,4}$/.test(texto)) {
    const preenchido = texto.padStart(4, '0')
    const hora = Number(preenchido.slice(0, 2))
    const minuto = Number(preenchido.slice(2))
    if (hora < 24 && minuto < 60) {
      return `${String(hora).padStart(2, '0')}:${String(minuto).padStart(2, '0')}`
    }
  }

  return texto
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

function obterDataNascimento(dataNascimento: string | null | undefined, hoje: Date): Date | null {
  if (!dataNascimento) return null
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(dataNascimento)
  if (!match) return null

  const ano = Number(match[1])
  const mesNascimento = Number(match[2])
  const dia = Number(match[3])
  const nasc = new Date(ano, mesNascimento - 1, dia)
  if (
    nasc.getFullYear() !== ano
    || nasc.getMonth() !== mesNascimento - 1
    || nasc.getDate() !== dia
    || (ano === 1899 && mesNascimento === 12 && dia === 30)
    || nasc.getTime() > hoje.getTime()
  ) return null

  return nasc
}

export function calcularIdade(dataNascimento: string | null | undefined, hoje: Date = new Date()): number | null {
  const nasc = obterDataNascimento(dataNascimento, hoje)
  if (!nasc) return null

  let idade = hoje.getFullYear() - nasc.getFullYear()
  const mes = hoje.getMonth() - nasc.getMonth()
  if (mes < 0 || (mes === 0 && hoje.getDate() < nasc.getDate())) idade -= 1
  return idade < 0 ? null : idade
}

export function calcularIdadeDetalhada(
  dataNascimento: string | null | undefined,
  hoje: Date = new Date()
): { anos: number, meses: number, dias: number } | null {
  const nasc = obterDataNascimento(dataNascimento, hoje)
  if (!nasc) return null

  const anos = calcularIdade(dataNascimento, hoje)
  if (anos === null) return null

  const aniversario = new Date(nasc.getFullYear() + anos, nasc.getMonth(), nasc.getDate())
  let meses = Math.min(
    (hoje.getFullYear() - aniversario.getFullYear()) * 12 + hoje.getMonth() - aniversario.getMonth(),
    11
  )

  const inicioMes = new Date(
    aniversario.getFullYear(),
    aniversario.getMonth() + meses,
    Math.min(aniversario.getDate(), new Date(aniversario.getFullYear(), aniversario.getMonth() + meses + 1, 0).getDate())
  )

  if (inicioMes.getTime() > hoje.getTime()) meses -= 1

  const inicioPeriodo = new Date(
    aniversario.getFullYear(),
    aniversario.getMonth() + meses,
    Math.min(aniversario.getDate(), new Date(aniversario.getFullYear(), aniversario.getMonth() + meses + 1, 0).getDate())
  )
  const inicioUtc = Date.UTC(inicioPeriodo.getFullYear(), inicioPeriodo.getMonth(), inicioPeriodo.getDate())
  const hojeUtc = Date.UTC(hoje.getFullYear(), hoje.getMonth(), hoje.getDate())
  const dias = Math.floor((hojeUtc - inicioUtc) / 86_400_000)

  return { anos, meses, dias }
}

export function formatarIdade(
  dataNascimento: string | null | undefined,
  { semAnos = false, semDados = false }: { semAnos?: boolean, semDados?: boolean } = {}
): string {
  const idade = calcularIdadeDetalhada(dataNascimento)
  if (idade === null) return semDados ? 'Idade não informada' : ''
  if (idade.anos <= 3) return `${idade.anos}a ${idade.meses}m ${idade.dias}d`
  return semAnos ? String(idade.anos) : `${idade.anos} ${idade.anos === 1 ? 'ano' : 'anos'}`
}
