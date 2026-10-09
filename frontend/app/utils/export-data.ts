import { getLogoBase64 } from '~/utils/pdf-assets'
import { usePdfMake } from '~/utils/pdf'

// Medidas do PDF em pontos. Margens: esquerda, superior, direita, inferior.
const LARGURA_A4_PAISAGEM = 841.89
const MARGENS_PDF: [number, number, number, number] = [20, 20, 20, 40]
const LARGURA_UTIL_PDF = LARGURA_A4_PAISAGEM - MARGENS_PDF[0] - MARGENS_PDF[2]
const PADDING_HORIZONTAL_TABELA = 2
const PADDING_VERTICAL_TABELA = 1.5

export interface ColunaExport<T> {
  key: string
  header: string
  value: (row: T) => string | number | null | undefined
}

export interface OpcoesPdfExport<T> {
  title: string
  subtitle?: string
  summary?: string[]
  rows: T[]
  columns: ColunaExport<T>[]
  filename: string
  /**
   * Aba aberta com abrirJanelaPdf() no clique do usuário.
   * undefined: abre nova aba agora; null/fechada: baixa o PDF (pop-up bloqueado).
   */
  janela?: Window | null
}

/**
 * Deve ser chamada de forma síncrona no clique, antes de qualquer await,
 * para o navegador não bloquear o pop-up.
 */
export function abrirJanelaPdf() {
  try {
    const janela = window.open('', '_blank')
    if (janela) {
      janela.document.title = 'Gerando PDF...'
      janela.document.body.innerHTML = '<p style="font-family:sans-serif;padding:16px">Gerando PDF...</p>'
    }
    return janela
  } catch {
    return null
  }
}

function baixarArquivo(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function textoCelula(valor: string | number | null | undefined) {
  if (valor === null || valor === undefined) return ''
  if (typeof valor === 'number') return valor.toLocaleString('pt-BR')
  return valor
}

function escaparCsv(valor: string | number | null | undefined) {
  let texto = textoCelula(valor)
  if (typeof valor === 'string' && /^[\t\r\n ]*[=+\-@]/.test(valor)) {
    texto = `'${texto}`
  }
  if (/[";\n\r]/.test(texto)) return `"${texto.replace(/"/g, '""')}"`
  return texto
}

export function exportToCSV<T>(rows: T[], columns: ColunaExport<T>[], filename: string) {
  const linhas = [
    columns.map(c => escaparCsv(c.header)).join(';'),
    ...rows.map(row => columns.map(c => escaparCsv(c.value(row))).join(';'))
  ]
  const blob = new Blob([`\uFEFF${linhas.join('\r\n')}`], { type: 'text/csv;charset=utf-8;' })
  baixarArquivo(blob, filename.endsWith('.csv') ? filename : `${filename}.csv`)
}

export async function exportToExcel<T>(rows: T[], columns: ColunaExport<T>[], filename: string, sheetName = 'Dados') {
  const XLSX = await import('xlsx')
  const dados: (string | number)[][] = [
    columns.map(c => c.header),
    ...rows.map(row => columns.map(c => c.value(row) ?? ''))
  ]
  const ws = XLSX.utils.aoa_to_sheet(dados)
  ws['!cols'] = columns.map((c, i) => {
    const max = dados.reduce((acc, linha) => Math.max(acc, String(linha[i] ?? '').length), c.header.length)
    return { wch: Math.min(Math.max(max + 2, 10), 40) }
  })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  const conteudo = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  baixarArquivo(
    new Blob([conteudo], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
  )
}

function largurasColunas<T>(columns: ColunaExport<T>[], rows: T[]): number[] {
  // pdfmake soma o padding às larguras das células; este layout não tem bordas verticais.
  const larguraConteudo = LARGURA_UTIL_PDF - columns.length * PADDING_HORIZONTAL_TABELA * 2
  const pesos = columns.map((c) => {
    let maxLen = c.header.length
    let maxToken = 0
    const considerar = (texto: string) => {
      if (texto.length > maxLen) maxLen = texto.length
      for (const token of texto.split(' ')) {
        if (token.length > maxToken) maxToken = token.length
      }
    }
    considerar(c.header)
    for (const row of rows) {
      considerar(textoCelula(c.value(row)))
    }
    return Math.max(Math.min(maxLen, 30), maxToken + 2, 6)
  })
  const somaPesos = pesos.reduce((a, b) => a + b, 0)
  return pesos.map(p => (p / somaPesos) * larguraConteudo)
}

const layoutTabelaCompacto = {
  hLineWidth: (i: number, node: { table: { headerRows: number, body: unknown[][] } }) =>
    (i === 0 || i === node.table.body.length ? 0.8 : 0.4),
  vLineWidth: () => 0,
  hLineColor: (i: number, node: { table: { headerRows: number } }) =>
    (i === 0 || i === node.table.headerRows ? '#AAAAAA' : '#DDDDDD'),
  paddingLeft: () => PADDING_HORIZONTAL_TABELA,
  paddingRight: () => PADDING_HORIZONTAL_TABELA,
  paddingTop: () => PADDING_VERTICAL_TABELA,
  paddingBottom: () => PADDING_VERTICAL_TABELA
}

export async function exportTableToPDF<T>(opcoes: OpcoesPdfExport<T>) {
  const pdfMake = await usePdfMake()
  const logo = await getLogoBase64()
  const { title, subtitle, summary, rows, columns, filename } = opcoes

  const corpo = [
    columns.map(c => ({ text: c.header, style: 'tableHeader' })),
    ...rows.map(row => columns.map(c => ({ text: textoCelula(c.value(row)) })))
  ]
  const larguras = largurasColunas(columns, rows)

  const doc = {
    info: { title: filename.endsWith('.pdf') ? filename.slice(0, -4) : filename },
    pageSize: 'A4',
    pageOrientation: 'landscape',
    pageMargins: MARGENS_PDF,
    content: [
      {
        columns: [
          { image: logo, width: 90 },
          {
            stack: [
              { text: 'NATUS LUMINE HOSPITAL E MATERNIDADE', fontSize: 9, bold: true },
              { text: title, fontSize: 13, bold: true }
            ],
            alignment: 'right',
            margin: [0, 4, 0, 0]
          }
        ],
        margin: [0, 0, 0, 4]
      },
      { canvas: [{ type: 'line', x1: 0, y1: 0, x2: LARGURA_UTIL_PDF, y2: 0, lineWidth: 1, lineColor: '#E0E0E0' }], margin: [0, 0, 0, 6] },
      ...(subtitle ? [{ text: subtitle, fontSize: 8, color: '#555555', margin: [0, 0, 0, 3] }] : []),
      ...(summary?.length ? [{ text: summary.join('  •  '), fontSize: 8, color: '#555555', margin: [0, 0, 0, 6] }] : []),
      {
        table: {
          headerRows: 1,
          dontBreakRows: true,
          widths: larguras,
          body: corpo
        },
        layout: layoutTabelaCompacto,
        fontSize: 6
      }
    ],
    footer: (currentPage: number, pageCount: number) => ({
      columns: [
        { text: `Gerado em ${new Date().toLocaleString('pt-BR')}`, fontSize: 7, color: '#999999' },
        { text: `Página ${currentPage} de ${pageCount}`, fontSize: 7, alignment: 'right' as const, color: '#999999' }
      ],
      margin: [MARGENS_PDF[0], 10, MARGENS_PDF[2], 0]
    }),
    styles: {
      tableHeader: { bold: true, fontSize: 6.5, color: '#333333', fillColor: '#F0F0F0' }
    }
  }

  const pdf = pdfMake.createPdf(doc as unknown as Record<string, unknown>)
  const { janela } = opcoes

  if (janela === undefined) {
    await pdf.open()
    return 'aberto' as const
  }

  if (!janela || janela.closed) {
    await pdf.download(filename.endsWith('.pdf') ? filename : `${filename}.pdf`)
    return 'baixado' as const
  }

  await pdf.open(janela)
  return 'aberto' as const
}
