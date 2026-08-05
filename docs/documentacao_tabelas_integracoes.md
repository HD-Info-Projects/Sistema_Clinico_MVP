# Documentacao De Tabelas E Integracoes

Este documento lista as tabelas externas e locais usadas pelo sistema, separadas por origem: SPDATA/Firebird, BioData/SQL Server e banco local do sistema.

## Visao Geral

| Origem | Banco | Uso principal |
|---|---|---|
| SPDATA | Firebird | Agenda, atendimentos, pacientes, medicos, convenios, especialidades, exames/procedimentos, CID e logos TISS. |
| BioData | SQL Server | Historico antigo de anamneses/prontuario do paciente. |
| Sistema local | Banco da aplicacao | Login, atendimento medico local, evolucoes, prescricoes, solicitacoes de exames, modelos e espelhos do SPDATA. |

## SPDATA / Firebird

| Tabela | O que faz no sistema |
|---|---|
| `REPACAGD` | Agenda do SPDATA. Usada para buscar pacientes agendados, medico, CRM, data/hora, convenio, telefone, CPF, prontuario e status de atendimento. |
| `ATCABECATEND` | Cabecalho/registro de atendimentos reais. Usada para saber quem foi atendido, data/hora de entrada, alta medica, medico, convenio e paciente. |
| `RICADPAC` | Cadastro de pacientes. Traz nome, CPF, prontuario, nascimento, sexo, celular, e-mail e endereco. |
| `TBCBOPRO` | Codigo/CRM de atendimento do profissional. Liga atendimento/agendamento ao profissional correto. |
| `TBPROFIS` | Cadastro de profissionais/medicos. Traz nome, CPF/CNPJ, CRM, e-mail e especialidade principal. |
| `TBESPEC` | Cadastro de especialidades. Usada para especialidade da agenda, atendimento e medicos. |
| `TBMEDESP` | Relacao medico/especialidade. Usada para descobrir especialidades ativas do medico. |
| `TBCONVEN` | Cadastro de convenios. Traz nome, codigo, situacao e registro ANS. |
| `SITABPRO` | Cadastro de exames/procedimentos. Usada para importar exames para o sistema local. |
| `TBTISS` | Logos/imagens TISS dos convenios. Usada para exportar logos dos convenios. |
| `TBCID10` | Cadastro de CID-10. Usada na busca de doencas/CID no prontuario. |
| `RDB$DATABASE` | Usada apenas para testar conexao Firebird. |

## BioData / SQL Server

| Tabela | O que faz no sistema |
|---|---|
| `[BioData].[dbo].[tblAnamnese]` | Historico antigo de anamneses do paciente. Traz data e texto da anamnese. |
| `[Repositorio].[dbo].[tblCliente]` | Cadastro do paciente no BioData/Repositorio. Usada para cruzar paciente por CPF/nome. |
| `[BioData].[dbo].[tblProfissional]` | Profissional/medico que registrou a anamnese antiga. |

## Sistema Local

| Tabela | O que faz no sistema |
|---|---|
| `usuarios` | Usuarios do sistema: medico, recepcao e admin. Guarda login, senha, nome, CPF/CNPJ e perfil. |
| `medicos` | Dados complementares do medico local. Liga `usuarios` ao medico do SPDATA, CRM e especialidade. |
| `atendimentos` | Atendimento criado no sistema local. Guarda vinculo com paciente SPDATA, agenda, medico, status e dados da consulta. |
| `anamneses` | Anamnese registrada no atendimento local. |
| `evolucoes_medicas` | Evolucao medica principal do atendimento. |
| `evolucoes_medicas_versoes` | Historico/versionamento das alteracoes da evolucao medica. |
| `diagnosticos` | Diagnosticos/CIDs vinculados ao atendimento. |
| `prescricoes` | Medicamentos/receitas prescritas no atendimento. |
| `solicitacoes_exames` | Solicitacoes de exames feitas pelo medico no sistema local. Hoje e a base da tela de retencao de exames. |
| `documentos_medicos` | Documentos gerados no atendimento, como atestado, encaminhamento etc. |
| `exames` | Espelho local dos exames/procedimentos importados do SPDATA `SITABPRO`. |
| `MED_SPDATA_AGENDA` | Espelho local da agenda do SPDATA `REPACAGD`. Usada para no-show, check-in e agenda medica. |
| `MED_SPDATA_ATENDIMENTOS` | Espelho local dos atendimentos do SPDATA `ATCABECATEND`. |
| `MED_ATENDIMENTOS` | Controle local do atendimento medico sobre registros vindos do SPDATA, incluindo status local. |
| `MED_SPDATA_CONVENIOS` | Espelho local dos convenios do SPDATA `TBCONVEN`. |
| `MED_SPDATA_ESPECIALIDADES` | Espelho local das especialidades do SPDATA `TBESPEC`. |
| `MODELO_ANAMNESE` | Modelos/padroes de anamnese criados por medico. |
| `MODELO_SOLICITACAO_RECEITA` | Modelos de receita/prescricao. |
| `MEDICAMENTOS_MODELO_RECEITA` | Medicamentos vinculados aos modelos de receita. |
| `MODELO_SOLICITACAO_EXAME` | Modelos de solicitacao de exame. |
| `EXAMES_MODELO_EXAME` | Exames vinculados aos modelos de solicitacao de exame. |
| `auditorias` | Registro de acoes/auditoria do sistema. |
| `logs_integracao` | Logs de integracoes/sincronizacoes. |
| `fila_sincronizacao` | Fila para sincronizacoes pendentes com SPDATA ou outros destinos. |

## Resumo Por Funcao

| Area | Tabelas principais |
|---|---|
| Agenda | `REPACAGD`, `MED_SPDATA_AGENDA` |
| Atendimento SPDATA | `ATCABECATEND`, `RICADPAC`, `TBCBOPRO`, `TBPROFIS`, `TBCONVEN` |
| Atendimento local | `atendimentos`, `MED_ATENDIMENTOS`, `MED_SPDATA_ATENDIMENTOS` |
| Prontuario local | `anamneses`, `evolucoes_medicas`, `diagnosticos`, `prescricoes`, `solicitacoes_exames`, `documentos_medicos` |
| Historico antigo BioData | `[BioData].[dbo].[tblAnamnese]`, `[Repositorio].[dbo].[tblCliente]`, `[BioData].[dbo].[tblProfissional]` |
| Exames | `SITABPRO`, `exames`, `solicitacoes_exames` |
| Convenios | `TBCONVEN`, `MED_SPDATA_CONVENIOS`, `TBTISS` |
| Medicos | `TBPROFIS`, `TBCBOPRO`, `TBMEDESP`, `medicos`, `usuarios` |
| Especialidades | `TBESPEC`, `MED_SPDATA_ESPECIALIDADES` |
| Modelos/padroes | `MODELO_ANAMNESE`, `MODELO_SOLICITACAO_RECEITA`, `MEDICAMENTOS_MODELO_RECEITA`, `MODELO_SOLICITACAO_EXAME`, `EXAMES_MODELO_EXAME` |

## Tela De Retencao De Exames

Hoje a tela de retencao de exames usa principalmente dados locais e espelhos do SPDATA.

| Origem | Tabelas usadas |
|---|---|
| Sistema local | `solicitacoes_exames`, `atendimentos`, `exames`, `medicos` |
| Espelho SPDATA local | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| SPDATA original | Dados vieram indiretamente de `ATCABECATEND`, `REPACAGD`, `RICADPAC`, `TBCONVEN`, `TBPROFIS`, `TBCBOPRO`, `TBESPEC` |

### Dados Que A Retencao Consegue Preencher Hoje

| Dado | Origem atual |
|---|---|
| Paciente | `atendimentos`, `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| CPF | `atendimentos`, `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| Prontuario | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| Telefone/celular | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| Medico | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA`, `medicos` |
| CRM | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA`, `medicos` |
| Especialidade | `MED_SPDATA_AGENDA`, `medicos` |
| Convenio | `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS` |
| Exame solicitado | `solicitacoes_exames`, `exames` |
| Data da solicitacao | `solicitacoes_exames.created_at` |
| Dias em aberto | Calculado a partir de `solicitacoes_exames.created_at` |
| Status inicial | Derivado de `solicitacoes_exames.status` e regra de dias em aberto |

### Dados Que Ainda Nao Temos Fonte Real Mapeada

| Dado | Situacao atual |
|---|---|
| Pedido real de exame no SPDATA | Nao ha tabela/consulta mapeada. |
| Item do pedido de exame | Nao ha tabela/consulta mapeada. |
| Agendamento interno do exame | Nao ha tabela/consulta mapeada. |
| Realizacao interna do exame | Nao ha tabela/consulta mapeada. |
| Realizacao externa do exame | Nao ha fonte automatica; precisaria ser local/manual ou outra integracao. |
| Laudo/resultado | Nao ha tabela/consulta mapeada. |
| Valor estimado real | Hoje fica `0`; nao ha fonte financeira mapeada. |
| Valor realizado/faturado | Hoje fica `null`; nao ha fonte financeira mapeada. |
| Guia/autorizacao | Nao ha tabela/consulta mapeada. |
| Historico de contato | Nao ha fonte real mapeada. |
| Responsavel pela retencao | Nao ha fonte real mapeada. |
| Status `sem-contato` | Nao ha fonte real mapeada. |
| Status `recusou` | Hoje so aparece se a solicitacao local estiver cancelada. |
| Status `agendado-internamente` | Nao ha fonte real mapeada. |
| Status `realizado-internamente` | Nao ha fonte real mapeada. |

## Observacao Importante

Ainda nao usamos uma tabela real do SPDATA para pedido, agendamento, execucao, laudo ou faturamento de exames. Para evoluir a tela de retencao de exames com dados reais completos, precisamos identificar no SPDATA as tabelas responsaveis por:

1. Pedido/solicitacao de exame.
2. Itens do pedido de exame.
3. Agenda de exames/procedimentos.
4. Execucao/realizacao do exame.
5. Laudo/resultado.
6. Guia/autorizacao.
7. Valores/tabela/faturamento por convenio.
8. Historico de contato, se existir no SPDATA.
