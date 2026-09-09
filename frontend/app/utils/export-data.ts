import { getLogoBase64 } from '~/utils/pdf-assets'
import { usePdfMake } from '~/utils/pdf'

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

function escaparCsv(valor: string) {
  if (/[";\n\r]/.test(valor)) return `"${valor.replace(/"/g, '""')}"`
  return valor
}

export function exportToCSV<T>(rows: T[], columns: ColunaExport<T>[], filename: string) {
  const linhas = [
    columns.map(c => escaparCsv(c.header)).join(';'),
    ...rows.map(row => columns.map(c => escaparCsv(textoCelula(c.value(row)))).join(';'))
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
  const LARGURA_PAGINA = 802
  const INFLACAO_RENDER = 8
  const OFFSETS_POR_COLUNA = 3.5
  const MARGEM_SEGURANCA = 3
  const larguraConteudo = LARGURA_PAGINA - columns.length * (INFLACAO_RENDER + OFFSETS_POR_COLUNA) - MARGEM_SEGURANCA
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
  return pesos.map(p => Math.floor((p / somaPesos) * larguraConteudo * 100) / 100)
}

const layoutTabelaCompacto = {
  hLineWidth: (i: number, node: { table: { headerRows: number, body: unknown[][] } }) =>
    (i === 0 || i === node.table.body.length ? 0.8 : 0.4),
  vLineWidth: () => 0,
  hLineColor: (i: number, node: { table: { headerRows: number } }) =>
    (i === 0 || i === node.table.headerRows ? '#AAAAAA' : '#DDDDDD'),
  padding: () => [2, 1.5, 2, 1.5] as [number, number, number, number]
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
    pageSize: 'A4',
    pageOrientation: 'landscape',
    pageMargins: [20, 20, 20, 40],
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
      { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 802, y2: 0, lineWidth: 1, lineColor: '#E0E0E0' }], margin: [0, 0, 0, 6] },
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
      margin: [20, 10, 20, 0]
    }),
    styles: {
      tableHeader: { bold: true, fontSize: 6.5, color: '#333333', fillColor: '#F0F0F0' }
    }
  }

  pdfMake.createPdf(doc as unknown as Record<string, unknown>).download(filename.endsWith('.pdf') ? filename : `${filename}.pdf`)
}
