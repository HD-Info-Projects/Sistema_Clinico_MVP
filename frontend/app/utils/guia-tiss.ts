import DOMPurify from 'dompurify'
import { getLogoBase64 } from '~/utils/pdf-assets'

export interface ExameTiss {
  nome: string
  codigo_amb?: string | null
  codigo_alfanumerico?: string | null
  orientacao?: string | null
}

const EXAMES_POR_PAGINA = 4
let convenioLogoIndex: Record<string, string> | null = null
let convenioLogoIndexLoaded = false

const TISS_PRINT_CSS = `
        @page {
            size: A4 landscape;
            margin: 0;
        }
        .guia-container {
            width: 287mm !important;
            max-width: none !important;
            min-height: 200mm;
            margin: 5mm auto !important;
            page-break-inside: avoid;
            break-inside: avoid;
        }
        .guia-container:not(:last-child) {
            page-break-after: always;
            break-after: page;
        }
        @media print {
            html, body {
                width: 297mm !important;
                min-width: 297mm !important;
                height: auto !important;
                min-height: 210mm !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        }
        .orientacao-exame-container {
            width: 297mm;
            height: 210mm;
            margin: 0;
            padding: 0;
            background-color: #fff;
            page-break-before: always;
            page-break-after: always;
            break-before: page;
            break-after: page;
            position: relative;
            overflow: hidden;
        }
        .orientacao-exame-container:last-child {
            page-break-after: auto;
            break-after: auto;
        }
        .orientacao-exame-page {
            box-sizing: border-box;
            position: absolute;
            top: 0;
            left: 297mm;
            width: 210mm;
            height: 297mm;
            padding: 12mm 14mm;
            background-color: #fff;
            transform-origin: top left;
            transform: rotate(90deg);
            display: flex;
            flex-direction: column;
            font-size: 12px;
            line-height: 1.5;
        }
        .orientacao-exame-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            border-bottom: 1px solid #d9d9d9;
            padding-bottom: 12px;
            margin-bottom: 24px;
        }
        .orientacao-exame-logo img {
            max-width: 160px;
            max-height: 64px;
            object-fit: contain;
        }
        .orientacao-exame-hospital {
            text-align: right;
            color: #555;
            font-size: 9px;
        }
        .orientacao-exame-hospital strong {
            display: block;
            color: #111;
            font-size: 12px;
            margin-bottom: 4px;
        }
        .orientacao-exame-title {
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .orientacao-exame-info {
            margin-bottom: 20px;
            font-size: 11px;
        }
        .orientacao-exame-info p {
            margin: 0 0 5px 0;
        }
        .orientacao-exame-content {
            flex: 1;
            font-size: 12px;
        }
        .orientacao-exame-content p {
            margin: 0 0 8px 0;
        }
        .orientacao-exame-content ul,
        .orientacao-exame-content ol {
            margin: 0 0 8px 24px;
        }
        .orientacao-exame-content blockquote {
            border-left: 3px solid #d9d9d9;
            margin: 8px 0;
            padding-left: 12px;
            color: #555;
        }
        .orientacao-exame-assinatura {
            margin-top: 48px;
            text-align: center;
            font-size: 10px;
            page-break-inside: avoid;
        }
`

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
  especialidade?: string
  cidPrincipal?: string
  caraterAtendimento?: boolean
}): Promise<string> {
  const template = await $fetch<string>('/guia_tiss_sadt-v2.html', { responseType: 'text' })

  const bodyStart = template.indexOf('<body>') + '<body>'.length
  const bodyEnd = template.indexOf('</body>')
  const beforeBody = adicionarCssTiss(template.slice(0, bodyStart))
  const bodyContent = template.slice(bodyStart, bodyEnd).trim()
  const afterBody = template.slice(bodyEnd)

  const batches = chunk(params.exames, EXAMES_POR_PAGINA)
  const convenioLogo = await convenioLogoHtml(params.convenio, params.idConvenioSpdata)
  const orientacoesPages = await orientacoesExamesHtml(params)

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
      .replaceAll('{{NOME_CONTRATADO}}', 'Natus Lumine Empreendimentos Medicos E Hospitalares LTDA')
      .replaceAll('{{CARATER_ATENDIMENTO}}', params.caraterAtendimento ? 'U' : 'E')
      .replaceAll('{{CID_PRINCIPAL}}', escapeHtml(params.cidPrincipal ?? ''))
      .replaceAll('{{EXAMES_ROWS}}', examesRows + blankRows)
  })

  return beforeBody + '\n' + [...pages, ...orientacoesPages].join('\n') + '\n' + afterBody
}

export function imprimirGuiaTiss(html: string) {
  const w = abrirHtmlParaImpressao(html)
  if (!w) return
  setTimeout(() => {
    imprimirJanela(w)
  }, 250)
}

function abrirHtmlParaImpressao(html: string) {
  const w = window.open('', '_blank')
  if (!w) return null
  w.document.open()
  w.document.write(html)
  w.document.close()
  return w
}

function imprimirJanela(w: Window) {
  w.focus()
  w.print()
  w.close()
}

function exameRowHtml(index: number, e: ExameTiss): string {
  return `            <tr>
                <td>${index} - <input type="text" value="" style="width: 60%; float: right; height:12px;"></td>
                <td><input type="text" value="${escapeHtml(e.codigo_amb ?? '')}"></td>
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

function adicionarCssTiss(html: string) {
  return html.replace('</style>', `${TISS_PRINT_CSS}</style>`)
}

function htmlTemConteudo(valor?: string | null) {
  const texto = (valor || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#160;|&#xA0;/gi, ' ')
    .replace(/[\u00A0\u200B-\u200D\uFEFF]/g, '')
    .trim()

  return Boolean(texto)
}

function sanitizarOrientacao(html: string) {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'blockquote', 'hr', 'a', 'img', 'sub', 'sup'],
    ALLOWED_ATTR: ['href', 'target', 'src', 'alt', 'title', 'class']
  })
}

async function orientacoesExamesHtml(params: {
  paciente: string
  data: string
  exames: ExameTiss[]
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const examesComOrientacao = params.exames.filter(e => htmlTemConteudo(e.orientacao))
  if (!examesComOrientacao.length) return []

  const logo = escapeHtml(await getLogoBase64())

  return examesComOrientacao.map(e => `
<section class="orientacao-exame-container">
  <div class="orientacao-exame-page">
    <div class="orientacao-exame-header">
        <div class="orientacao-exame-logo"><img src="${logo}" alt="Natus Lumine"></div>
        <div class="orientacao-exame-hospital">
            <strong>NATUS LUMINE HOSPITAL E MATERNIDADE</strong>
            <div>Av. dos Holandeses, nº 69, Olho D'Água</div>
            <div>São Luís - MA | CEP: 65065-180</div>
            <div>Telefone: (98) 2107-5252</div>
        </div>
    </div>
    <div class="orientacao-exame-title">ORIENTAÇÃO DE EXAME</div>
    <div class="orientacao-exame-info">
        <p><strong>PACIENTE:</strong> ${escapeHtml(params.paciente.toUpperCase())}</p>
        <p><strong>DATA:</strong> ${escapeHtml(params.data)}</p>
        <p><strong>EXAME:</strong> ${escapeHtml(e.nome)}</p>
    </div>
    <div class="orientacao-exame-content">${sanitizarOrientacao(e.orientacao || '')}</div>
    <div class="orientacao-exame-assinatura">
        <div>__________________________________________</div>
        <strong>${escapeHtml(params.medico || 'Médico Responsável')}</strong>
        ${params.especialidade ? `<div>${escapeHtml(params.especialidade)}</div>` : ''}
        ${params.crm ? `<div>CRM:${escapeHtml(params.crm)}</div>` : ''}
    </div>
  </div>
</section>`)
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
