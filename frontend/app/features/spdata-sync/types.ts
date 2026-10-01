export type SpdataSyncTarget = 'TODOS' | 'EXAMES' | 'PROCEDIMENTOS'
export type SpdataSyncStatus = 'QUEUED' | 'RUNNING' | 'RETRYING' | 'SUCCEEDED' | 'SUCCEEDED_WITH_ERRORS' | 'FAILED'

export type SpdataSyncCounters = {
  lidos: number
  criados: number
  atualizados: number
  erros: number
  completed?: boolean
}

export type SpdataSyncJob = {
  id: number
  target: SpdataSyncTarget
  origin: 'ADMIN_API' | 'CLI'
  status: SpdataSyncStatus
  current_stage: 'EXAMES' | 'PROCEDIMENTOS' | null
  attempts: number
  max_attempts: number
  batch_size: number
  progress: Partial<Record<'exames' | 'procedimentos', SpdataSyncCounters>>
  result: Partial<Record<'exames' | 'procedimentos', SpdataSyncCounters>> | null
  error_code: string | null
  error_message: string | null
  requested_by: { id: number, nome_completo: string } | null
  queued_at: string
  started_at: string | null
  heartbeat_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

export type SpdataSyncListResponse = {
  items: SpdataSyncJob[]
  limit: number
  offset: number
  has_more: boolean
  active_job: SpdataSyncJob | null
}

export type SpdataSyncCreateResponse = {
  message: string
  job: SpdataSyncJob
}

export type SpdataSyncDetailResponse = {
  job: SpdataSyncJob
}
