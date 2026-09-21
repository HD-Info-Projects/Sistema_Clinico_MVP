"""Pacientes module.

O domínio de pacientes não possui blueprint próprio: a identidade do
paciente é agregada a partir dos espelhos SPDATA (MedSpdataAtendimento,
MedSpdataAgenda) e do Atendimento local. Este módulo concentra as
leituras de paciente (busca SPDATA, convênios locais e CRM do usuário)
e reexporta os modelos do domínio para os demais módulos.
"""