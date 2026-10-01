import type { H3Event } from 'h3'

export function iniciarSincronizacaoSpdata(event: H3Event, target: string) {
  return flaskFetch(event, '/admin/spdata-sync/jobs', {
    method: 'POST',
    body: { target },
    activeClinica: false
  })
}

export function listarSincronizacoesSpdata(event: H3Event, limit: number, offset: number) {
  return flaskFetch(event, `/admin/spdata-sync/jobs?limit=${limit}&offset=${offset}`, {
    activeClinica: false
  })
}

export function buscarSincronizacaoSpdata(event: H3Event, id: number) {
  return flaskFetch(event, `/admin/spdata-sync/jobs/${id}`, {
    activeClinica: false
  })
}
