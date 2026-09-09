function extrairViewerUrl(payload: Record<string, unknown>): string | null {
  const chaves = ['message', 'url', 'viewerUrl', 'viewer_url', 'link', 'href']
  for (const chave of chaves) {
    const valor = payload[chave]
    if (typeof valor === 'string' && /^https?:\/\//i.test(valor.trim())) return valor.trim()
  }

  const data = payload.data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return extrairViewerUrl(data as Record<string, unknown>)
  }

  return null
}

function hostsPermitidosViewer(): string[] {
  const config = useRuntimeConfig()
  return String(config.pacsViewerAllowedHosts || '')
    .split(',')
    .map(host => host.trim().toLowerCase())
    .filter(Boolean)
}

function viewerUrlPermitida(viewerUrl: string): boolean {
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

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: 'Exame inválido' })
  }

  try {
    const payload = await flaskFetch<Record<string, unknown>>(event, `/exames-pacs/${id}`, { method: 'POST' })
    const viewerUrl = extrairViewerUrl(payload)
    if (!viewerUrl) {
      throw createError({ statusCode: 502, message: 'O PACS não retornou URL de visualização' })
    }
    if (!viewerUrlPermitida(viewerUrl)) {
      throw createError({ statusCode: 502, message: 'URL de visualização PACS fora da allowlist' })
    }

    setResponseHeader(event, 'Cache-Control', 'no-store, private')
    setResponseHeader(event, 'Pragma', 'no-cache')
    return sendRedirect(event, viewerUrl, 302)
  } catch (error) {
    throwProxyError(error, 'Falha ao abrir viewer de imagem no backend Flask')
  }
})
