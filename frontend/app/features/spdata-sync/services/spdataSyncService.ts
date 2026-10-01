import type {
  SpdataSyncCreateResponse,
  SpdataSyncDetailResponse,
  SpdataSyncListResponse,
  SpdataSyncTarget
} from '../types'

export function iniciarSpdataSync(target: SpdataSyncTarget) {
  return $fetch<SpdataSyncCreateResponse>('/api/admin/spdata-sync', {
    method: 'POST',
    body: { target }
  })
}

export function listarSpdataSync(limit = 20, offset = 0) {
  return $fetch<SpdataSyncListResponse>('/api/admin/spdata-sync', {
    query: { limit, offset }
  })
}

export function buscarSpdataSync(id: number) {
  return $fetch<SpdataSyncDetailResponse>(`/api/admin/spdata-sync/${id}`)
}
