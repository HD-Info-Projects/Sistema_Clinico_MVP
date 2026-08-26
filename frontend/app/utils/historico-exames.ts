import type { ExameHistoricoItem, ExamePacs, HistoricoExame, HistoricoLocalRecord } from '~/types'

const MS_DIA = 24 * 60 * 60 * 1000
const JANELA_CODIGO_DIAS = 60
const JANELA_NOME_DIAS = 30

type PacsEntry = {
  exame: ExamePacs
  chave: string
}

export type GrupoExamesRealizados = {
  id: string
  data: string | null
  sortKey: string
  exames: ExameHistoricoItem[]
}

export type ExamesHistoricoUnificados = {
  examesPorRegistroLocal: ExameHistoricoItem[][]
  examesRealizados: GrupoExamesRealizados[]
}

function texto(valor: unknown): string {
  return String(valor || '').trim()
}

function normalizarCodigo(valor: unknown): string {
  return texto(valor).toUpperCase()
}

export function normalizarNomeExame(valor: unknown): string {
  return texto(valor)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

export function extrairDataIso(valor?: string | null): string {
  const textoData = texto(valor)
  const match = textoData.match(/^(\d{4}-\d{2}-\d{2})/)
  if (match) return match[1]!

  const data = new Date(textoData)
  if (Number.isNaN(data.getTime())) return ''

  return data.toISOString().slice(0, 10)
}

function timestampDia(valor?: string | null): number | null {
  const iso = extrairDataIso(valor)
  if (!iso) return null
  const timestamp = new Date(`${iso}T00:00:00`).getTime()
  return Number.isNaN(timestamp) ? null : timestamp
}

function distanciaDias(dataA?: string | null, dataB?: string | null): number | null {
  const a = timestampDia(dataA)
  const b = timestampDia(dataB)
  if (a === null || b === null) return null
  return Math.abs(Math.round((a - b) / MS_DIA))
}

function dataRealizacaoPacs(exame: ExamePacs): string | null {
  return exame.dataResultado || exame.dataLancamento || null
}

function idPacs(exame: ExamePacs): number | null {
  const id = Number(exame.idTokenLancamentoExame)
  return Number.isFinite(id) && id > 0 ? id : null
}

function chavePacs(exame: ExamePacs, index: number): string {
  const id = idPacs(exame)
  return id ? `id:${id}` : `idx:${index}`
}

function nomeLocal(exame: HistoricoExame | string): string {
  return typeof exame === 'string'
    ? texto(exame)
    : texto(exame.nome || exame.descricao || exame.tipo_exame)
}

function codigoLocal(exame: HistoricoExame | string): string {
  return typeof exame === 'string' ? '' : normalizarCodigo(exame.codigo_alfanumerico)
}

function tokenLocal(exame: HistoricoExame | string): number | null {
  if (typeof exame === 'string') return null
  const id = Number(exame.idTokenLancamentoExame)
  return Number.isFinite(id) && id > 0 ? id : null
}

function orientacaoLocal(exame: HistoricoExame | string): string | null {
  return typeof exame === 'string' ? null : (exame.orientacao || null)
}

function scoreMatch(exameLocal: HistoricoExame | string, dataAtendimento: string | null, pacs: ExamePacs): number {
  const token = tokenLocal(exameLocal)
  const tokenPacs = idPacs(pacs)
  if (token && tokenPacs && token === tokenPacs) return 10000

  const dias = distanciaDias(dataAtendimento, dataRealizacaoPacs(pacs))
  const codigo = codigoLocal(exameLocal)
  const codigoPacs = normalizarCodigo(pacs.codigoExame)
  if (codigo && codigoPacs && codigo === codigoPacs && dias !== null && dias <= JANELA_CODIGO_DIAS) {
    return 800 - dias
  }

  const nome = normalizarNomeExame(nomeLocal(exameLocal))
  const nomePacs = normalizarNomeExame(pacs.nomeExame)
  if (nome && nomePacs && nome === nomePacs && dias !== null && dias <= JANELA_NOME_DIAS) {
    return 500 - dias
  }

  return 0
}

function encontrarPacsCompativel(
  exameLocal: HistoricoExame | string,
  dataAtendimento: string | null,
  pacs: PacsEntry[],
  usados: Set<string>
): PacsEntry | null {
  const candidatos = pacs
    .filter(entry => !usados.has(entry.chave))
    .map(entry => ({ entry, score: scoreMatch(exameLocal, dataAtendimento, entry.exame) }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)

  if (!candidatos.length) return null
  if (candidatos[1] && candidatos[0]!.score === candidatos[1].score) return null

  return candidatos[0]!.entry
}

function itemLocal(exame: HistoricoExame | string, dataAtendimento: string | null, pacs?: ExamePacs): ExameHistoricoItem | null {
  const nome = nomeLocal(exame)
  if (!nome) return null

  return {
    nome,
    orientacao: orientacaoLocal(exame),
    temImagem: pacs?.temImagem ?? false,
    temLaudo: pacs?.temLaudo ?? false,
    idTokenLancamentoExame: pacs?.idTokenLancamentoExame ?? tokenLocal(exame),
    situacao: pacs ? 'Solicitado · Realizado' : 'Solicitado',
    origemLocal: true,
    origemPacs: Boolean(pacs),
    dataSolicitacao: dataAtendimento,
    dataRealizacao: pacs ? dataRealizacaoPacs(pacs) : null,
    codigoExame: pacs?.codigoExame || (typeof exame === 'string' ? null : exame.codigo_alfanumerico)
  }
}

function itemPacs(exame: ExamePacs): ExameHistoricoItem | null {
  const nome = texto(exame.nomeExame)
  if (!nome) return null

  return {
    nome,
    orientacao: null,
    temImagem: exame.temImagem,
    temLaudo: exame.temLaudo,
    idTokenLancamentoExame: exame.idTokenLancamentoExame,
    situacao: 'Realizado',
    origemLocal: false,
    origemPacs: true,
    dataSolicitacao: null,
    dataRealizacao: dataRealizacaoPacs(exame),
    codigoExame: exame.codigoExame || null
  }
}

function agruparPacsSemSolicitacao(pacs: PacsEntry[], usados: Set<string>): GrupoExamesRealizados[] {
  const grupos = new Map<string, GrupoExamesRealizados>()

  for (const entry of pacs) {
    if (usados.has(entry.chave)) continue

    const item = itemPacs(entry.exame)
    if (!item) continue

    const data = dataRealizacaoPacs(entry.exame)
    const dataIso = extrairDataIso(data)
    const chaveGrupo = dataIso || entry.chave
    const grupo = grupos.get(chaveGrupo) || {
      id: `exames-realizados-${chaveGrupo}`,
      data,
      sortKey: data || '',
      exames: []
    }

    grupo.exames.push(item)
    grupos.set(chaveGrupo, grupo)
  }

  return [...grupos.values()].sort((a, b) => {
    const dataA = new Date(a.sortKey).getTime()
    const dataB = new Date(b.sortKey).getTime()
    return (Number.isNaN(dataB) ? 0 : dataB) - (Number.isNaN(dataA) ? 0 : dataA)
  })
}

export function montarExamesHistoricoUnificados(
  localHistorico: HistoricoLocalRecord[],
  examesPacs: ExamePacs[]
): ExamesHistoricoUnificados {
  const pacs = examesPacs.map((exame, index) => ({ exame, chave: chavePacs(exame, index) }))
  const usados = new Set<string>()
  const examesPorRegistroLocal = localHistorico.map((registro) => {
    const examesLocais = registro.exames || []
    const itens: ExameHistoricoItem[] = []

    for (const exame of examesLocais) {
      const pacsCompativel = encontrarPacsCompativel(exame, registro.data_consulta, pacs, usados)
      if (pacsCompativel) usados.add(pacsCompativel.chave)

      const item = itemLocal(exame, registro.data_consulta, pacsCompativel?.exame)
      if (item) itens.push(item)
    }

    return itens
  })

  return {
    examesPorRegistroLocal,
    examesRealizados: agruparPacsSemSolicitacao(pacs, usados)
  }
}

export function abrirExamePacs(idTokenLancamentoExame: number | null | undefined, tipo: 'imagem' | 'laudo') {
  if (!import.meta.client || !idTokenLancamentoExame) return
  const id = Number(idTokenLancamentoExame)
  if (!Number.isFinite(id) || id <= 0) return

  const url = tipo === 'imagem'
    ? `/api/exames-pacs/${id}/viewer`
    : `/api/exames-pacs/${id}/laudo/pdf`
  window.open(url, '_blank', 'noopener,noreferrer')
}
