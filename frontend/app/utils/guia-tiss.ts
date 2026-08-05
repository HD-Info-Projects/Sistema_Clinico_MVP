export interface ExameTiss {
  nome: string
  codigo_amb?: string | null
  codigo_alfanumerico?: string | null
}

const EXAMES_POR_PAGINA = 4
let convenioLogoIndex: Record<string, string> | null = null
let convenioLogoIndexLoaded = false

export async function gerarHtmlGuiaTiss(params: {
  paciente: string
  nomeSocial?: string | null
  cpf?: string
  convenio: string
  idConvenioSpdata?: number | null
  data: string
  exames: ExameTiss[]
  medico?: string
  crm?: string
}): Promise<string> {
  const template = await $fetch<string>('/guia_tiss_sadt-v2.html', { responseType: 'text' })

  const bodyStart = template.indexOf('<body>') + '<body>'.length
  const bodyEnd = template.indexOf('</body>')
  const beforeBody = template.slice(0, bodyStart)
  const bodyContent = template.slice(bodyStart, bodyEnd).trim()
  const afterBody = template.slice(bodyEnd)

  const batches = chunk(params.exames, EXAMES_POR_PAGINA)
  const convenioLogo = await convenioLogoHtml(params.convenio, params.idConvenioSpdata)

  const pages = batches.map((batch, batchIdx) => {
    const startNum = batchIdx * EXAMES_POR_PAGINA
    const examesRows = batch.map((e, i) =>
      exameRowHtml(startNum + i + 1, e)
    ).join('')
    const blankRows = Array.from({ length: EXAMES_POR_PAGINA - batch.length }, (_, i) =>
      exameRowHtml(startNum + batch.length + i + 1, { nome: '' })
    ).join('')

    return bodyContent
      .replaceAll('{{CONVENIO}}', escapeHtml(params.convenio))
      .replaceAll('{{CONVENIO_LOGO}}', convenioLogo)
      .replaceAll('{{PACIENTE}}', escapeHtml(params.paciente))
      .replaceAll('{{PACIENTE_NOME_SOCIAL}}', escapeHtml(params.nomeSocial ?? ''))
      .replaceAll('{{CPF}}', escapeHtml(params.cpf ?? ''))
      .replaceAll('{{MEDICO}}', escapeHtml(params.medico ?? ''))
      .replaceAll('{{CRM_NUMERO}}', extractCrmNumero(params.crm))
      .replaceAll('{{DATA_SOLICITACAO}}', escapeHtml(params.data))
      .replaceAll('{{EXAMES_ROWS}}', examesRows + blankRows)
  })

  return beforeBody + '\n' + pages.join('\n') + '\n' + afterBody
}

export function imprimirGuiaTiss(html: string) {
  const w = window.open('', '_blank')
  if (!w) return
  w.document.open()
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => {
    w.print()
    w.close()
  }, 250)
}

function exameRowHtml(index: number, e: ExameTiss): string {
  return `            <tr>
                <td>${index} - <input type="text" value="" style="width: 60%; float: right; height:12px;"></td>
                <td><input type="text" value=""></td>
                <td><input type="text" value="${escapeHtml(e.nome)}"></td>
                <td><input type="text" value="1"></td>
                <td><input type="text" value=""></td>
            </tr>`
}

function chunk<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = []
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size))
  }
  return chunks
}

function escapeHtml(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

async function convenioLogoHtml(convenio: string, idConvenioSpdata?: number | null) {
  const fallback = ''
  const alt = escapeHtml(convenio)
  if (!idConvenioSpdata) return fallback

  try {
    const index = await getConvenioLogoIndex()
    const logoPath = index[String(idConvenioSpdata)]
    if (!logoPath) return fallback

    const response = await fetch(logoPath)
    if (!response.ok) return fallback

    const dataUrl = await blobToDataUrl(await response.blob())
    return `<img src="${escapeHtml(dataUrl)}" alt="${alt}">`
  } catch {
    return fallback
  }
}

async function getConvenioLogoIndex() {
  if (convenioLogoIndexLoaded) return convenioLogoIndex ?? {}

  convenioLogoIndexLoaded = true

  try {
    const response = await fetch('/img/convenios/index.json')
    if (!response.ok) {
      convenioLogoIndex = {}
      return convenioLogoIndex
    }

    const data = await response.json() as unknown
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      convenioLogoIndex = {}
      return convenioLogoIndex
    }

    convenioLogoIndex = Object.fromEntries(
      Object.entries(data as Record<string, unknown>)
        .filter((entry): entry is [string, string] => typeof entry[1] === 'string')
    )
  } catch {
    convenioLogoIndex = {}
  }

  return convenioLogoIndex
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Falha ao carregar logo do convênio'))
    reader.readAsDataURL(blob)
  })
}

function extractCrmNumero(crm?: string): string {
  if (!crm) return ''
  const match = crm.match(/\d+/)
  return match ? escapeHtml(match[0]) : ''
}
