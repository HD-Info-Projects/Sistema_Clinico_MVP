import type { H3Event } from 'h3'
import { createError, sendRedirect, setResponseHeader } from 'h3'
import { useRuntimeConfig } from '#imports'
import { flaskFetch } from '../../utils/flask'

type LaudoExamePacs = {
  contentType?: string
  filename?: string
  base64: string
}

const VIEWER_URL_KEYS = ['message', 'url', 'viewerUrl', 'viewer_url', 'link', 'href']

export function validarIdPacs(id: number, mensagem: string) {
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: mensagem })
  }

  return id
}

export function listarExamesPacsPaciente(event: H3Event, pacienteId: number) {
  return flaskFetch(event, `/exames-pacs/paciente/${validarIdPacs(pacienteId, 'Paciente inválido')}`)
}

export function abrirViewerExamePacs(event: H3Event, exameId: number) {
  return flaskFetch<Record<string, unknown>>(event, `/exames-pacs/${validarIdPacs(exameId, 'Exame inválido')}`, { method: 'POST' })
}

export function buscarLaudoExamePacs(event: H3Event, exameId: number) {
  setNoStoreHeaders(event)
  setResponseHeader(event, 'X-Content-Type-Options', 'nosniff')
  return flaskFetch(event, `/exames-pacs/${validarIdPacs(exameId, 'Exame inválido')}/laudo`)
}

export function extrairViewerUrl(payload: Record<string, unknown>): string | null {
  for (const chave of VIEWER_URL_KEYS) {
    const valor = payload[chave]
    if (typeof valor === 'string' && /^https?:\/\//i.test(valor.trim())) return valor.trim()
  }

  const data = payload.data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return extrairViewerUrl(data as Record<string, unknown>)
  }

  return null
}

export function hostsPermitidosViewer(): string[] {
  const config = useRuntimeConfig()
  return String(config.pacsViewerAllowedHosts || '')
    .split(',')
    .map(host => host.trim().toLowerCase())
    .filter(Boolean)
}

export function viewerUrlPermitida(viewerUrl: string): boolean {
  const hostsPermitidos = hostsPermitidosViewer()
  if (!hostsPermitidos.length) return false

  try {
    const url = new URL(viewerUrl)
    const host = url.host.toLowerCase()
    const hostname = url.hostname.toLowerCase()
    return hostsPermitidos.includes(host) || hostsPermitidos.includes(hostname)
  } catch {
    return false
  }
}

export function setNoStoreHeaders(event: H3Event) {
  setResponseHeader(event, 'Cache-Control', 'no-store, private')
  setResponseHeader(event, 'Pragma', 'no-cache')
}

export async function redirecionarViewerExamePacs(event: H3Event, exameId: number) {
  const payload = await abrirViewerExamePacs(event, exameId)
  const viewerUrl = extrairViewerUrl(payload)
  if (!viewerUrl) {
    throw createError({ statusCode: 502, message: 'O PACS não retornou URL de visualização' })
  }
  if (!viewerUrlPermitida(viewerUrl)) {
    throw createError({ statusCode: 502, message: 'URL de visualização PACS fora da allowlist' })
  }

  setNoStoreHeaders(event)
  return sendRedirect(event, viewerUrl, 302)
}

function nomeArquivoSeguro(filename: string | undefined, id: number) {
  const nome = String(filename || `laudo-exame-${id}.pdf`).replace(/[\\/\r\n"]/g, '')
  return nome || `laudo-exame-${id}.pdf`
}

export async function enviarPdfLaudoPacs(event: H3Event, exameId: number) {
  const id = validarIdPacs(exameId, 'Exame inválido')
  const laudo = await flaskFetch<LaudoExamePacs>(event, `/exames-pacs/${id}/laudo`)
  const pdf = Buffer.from(laudo.base64, 'base64')
  const contentType = laudo.contentType || 'application/pdf'
  const filename = nomeArquivoSeguro(laudo.filename, id)

  setResponseHeader(event, 'Content-Type', contentType)
  setResponseHeader(event, 'Content-Disposition', `inline; filename="${filename}"`)
  setResponseHeader(event, 'Content-Length', pdf.length)
  setNoStoreHeaders(event)
  setResponseHeader(event, 'X-Content-Type-Options', 'nosniff')

  return pdf
}
