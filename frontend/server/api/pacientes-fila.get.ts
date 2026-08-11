export default defineEventHandler(async (event) => {
  try {
    const clinicaId = getActiveClinicaId(event) ?? 0
    const raw = await flaskFetch<Record<string, unknown>[]>(event, '/dashboard/pacientes')

    return raw.map((item: Record<string, unknown>) => {
      const entrada = item.DATA_HORA_ENTRADA ? new Date(String(item.DATA_HORA_ENTRADA)) : new Date()
      const dataStr = entrada.toISOString().slice(0, 10)
      const horarioStr = entrada.toISOString().slice(11, 16)

      return {
        id: Number(item.COD_ATENDIMENTO) || 0,
        pacienteId: Number(item.ID_PACIENTE) || 0,
        medicoId: Number(item.ID_MEDICO) || 0,
        clinicaId,
        data: dataStr,
        horario: horarioStr,
        prioridade: 'normal',
        status: 'em-espera' as const,
        descricao: '',
        criadoEm: dataStr,
        paciente: {
          id: Number(item.ID_PACIENTE) || null,
          nome: String(item.PACIENTE || ''),
          sexo: String(item.SEXO) === 'F' ? 'feminino' : 'masculino',
          dataNascimento: String(item.DATA_NASCIMENTO || ''),
          tipoSanguineo: '',
          alergias: [],
          medicamentosEmUso: [],
          convenio: String(item.ID_TBCONVEN),
          telefone: String(item.CELULAR || ''),
          email: String(item.EMAIL || 'Não Informado'),
          cpf: String(item.CPF || ''),
          endereco: String(item.ENDERECO || ''),
          historicoRecente: []
        }
      }
    })
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar pacientes no backend Flask')
  }
})
