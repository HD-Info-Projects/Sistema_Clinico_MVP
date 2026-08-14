# Documentacao De Tabelas E Integracoes

Este documento lista as tabelas externas e locais usadas pelo sistema, separadas por origem: SPDATA/Firebird, BioData/SQL Server e banco local do sistema.

Atualizacao: inclui os controles recentes de Seguranca de Dados e LGPD, especialmente senha com hash, auditoria LGPD e a tabela de modelos de orientacao de exame.

## Visao Geral

| Origem | Banco | Uso principal |
|---|---|---|
| SPDATA | Firebird | Agenda, atendimentos, pacientes, medicos, convenios, especialidades, exames/procedimentos, CID e logos TISS. |
| BioData | SQL Server | Historico antigo de anamneses/prontuario do paciente. |
| Sistema local | Banco da aplicacao | Login, atendimento medico local, evolucoes, prescricoes, solicitacoes de exames, documentos, modelos, auditoria e espelhos do SPDATA. |
| Redis | Redis | Cache operacional e storage de rate limit, quando configurado. |

## Observacao LGPD

O sistema trata dados pessoais e dados pessoais sensiveis, especialmente dados de saude. Por isso:

1. Tabelas de prontuario, diagnosticos, prescricoes, exames, documentos medicos e historico BioData devem ser consideradas sensiveis.
2. Logs de auditoria devem guardar metadados do acesso, nao conteudo clinico completo.
3. Logs de integracao e filas nao devem armazenar payloads clinicos completos sem necessidade.
4. Listagens operacionais devem retornar apenas os campos necessarios para a finalidade da tela.
5. Bases de teste/homologacao devem ser anonimizadas ou pseudonimizadas sempre que possivel.

## SPDATA / Firebird

| Tabela | O que faz no sistema | Dados relevantes |
|---|---|---|
| `REPACAGD` | Agenda do SPDATA. Usada para buscar pacientes agendados, medico, CRM, data/hora, convenio, telefone, CPF, prontuario e status de atendimento. | Dados pessoais e operacionais de agenda. |
| `ATCABECATEND` | Cabecalho/registro de atendimentos reais. Usada para saber quem foi atendido, data/hora de entrada, alta medica, medico, convenio e paciente. | Dados de atendimento e possiveis dados sensiveis. |
| `RICADPAC` | Cadastro de pacientes. Traz nome, CPF, prontuario, nascimento, sexo, celular, e-mail e endereco. | Dados pessoais do paciente. |
| `TBCBOPRO` | Codigo/CRM de atendimento do profissional. Liga atendimento/agendamento ao profissional correto. | Dados profissionais do medico. |
| `TBPROFIS` | Cadastro de profissionais/medicos. Traz nome, CPF/CNPJ, CRM, e-mail e especialidade principal. | Dados profissionais e cadastrais. |
| `TBESPEC` | Cadastro de especialidades. Usada para especialidade da agenda, atendimento e medicos. | Dados administrativos. |
| `TBMEDESP` | Relacao medico/especialidade. Usada para descobrir especialidades ativas do medico. | Dados administrativos/profissionais. |
| `TBCONVEN` | Cadastro de convenios. Traz nome, codigo, situacao e registro ANS. | Dados administrativos. |
| `SITABPRO` | Cadastro de exames/procedimentos. Usada para importar exames para o sistema local. | Dados administrativos/assistenciais. |
| `TBTISS` | Logos/imagens TISS dos convenios. Usada para exportar logos dos convenios. | Dados administrativos/imagens. |
| `TBCID10` | Cadastro de CID-10. Usada na busca de doencas/CID no prontuario. | Tabela de referencia clinica. |
| `RDB$DATABASE` | Usada apenas para testar conexao Firebird. | Sem dados pessoais. |

## BioData / SQL Server

| Tabela | O que faz no sistema | Dados relevantes |
|---|---|---|
| `[BioData].[dbo].[tblAnamnese]` | Historico antigo de anamneses do paciente. Traz data e texto da anamnese. | Dado pessoal sensivel, conteudo clinico. |
| `[Repositorio].[dbo].[tblCliente]` | Cadastro do paciente no BioData/Repositorio. Usada para cruzar paciente por CPF/nome. | Dados pessoais do paciente. |
| `[BioData].[dbo].[tblProfissional]` | Profissional/medico que registrou a anamnese antiga. | Dados profissionais. |

## Sistema Local

### Autenticacao, Usuarios E Medicos

| Tabela | O que faz no sistema | Observacao LGPD/seguranca |
|---|---|---|
| `usuarios` | Usuarios do sistema: medico, recepcao, admin e perfis administrativos como DPO/TI quando usados. Guarda login, hash de senha, nome, CPF/CNPJ e perfil. | A coluna `senha` deve armazenar hash, nunca senha em texto puro. CPF/CNPJ e e-mail sao dados pessoais. |
| `medicos` | Dados complementares do medico local. Liga `usuarios` ao medico do SPDATA, CRM, CRM de atendimento e especialidade. | Dados profissionais usados para vincular medico ao SPDATA e filtrar agenda/prontuario. |

### Atendimento E Prontuario Local

| Tabela | O que faz no sistema | Observacao LGPD/seguranca |
|---|---|---|
| `atendimentos` | Atendimento criado no sistema local. Guarda vinculo com paciente SPDATA, agenda, medico, status e dados da consulta. | Contem nome/CPF do paciente e vinculos assistenciais. Deve ser tratado como sensivel. |
| `anamneses` | Anamnese registrada no atendimento local. | Conteudo clinico sensivel. Acesso deve ser auditado. |
| `evolucoes_medicas` | Evolucao medica principal do atendimento. | Conteudo clinico sensivel. |
| `evolucoes_medicas_versoes` | Historico/versionamento das alteracoes da evolucao medica. | Conteudo clinico sensivel e trilha de alteracao. |
| `diagnosticos` | Diagnosticos/CIDs vinculados ao atendimento. | Dado de saude sensivel. |
| `prescricoes` | Medicamentos/receitas prescritas no atendimento. | Dado de saude sensivel. |
| `solicitacoes_exames` | Solicitacoes de exames feitas pelo medico no sistema local. Hoje e a base da tela de retencao/conversao de exames. | Dado assistencial sensivel. |
| `documentos_medicos` | Documentos gerados no atendimento, como atestado, declaracao, encaminhamento, relatorio e receita. | Conteudo clinico/documental sensivel. Acesso e alteracao devem ser auditados. |

### Espelhos E Caches Locais Do SPDATA

| Tabela | O que faz no sistema | Observacao LGPD/seguranca |
|---|---|---|
| `exames` | Espelho local dos exames/procedimentos importados do SPDATA `SITABPRO`. | Catalogo de exames/procedimentos. Normalmente administrativo, mas pode indicar contexto assistencial quando vinculado a solicitacoes. |
| `MED_SPDATA_AGENDA` | Espelho local da agenda do SPDATA `REPACAGD`. Usada para no-show, check-in e agenda medica. | Contem paciente, CPF, prontuario, telefone, e-mail e agenda. Dado pessoal e operacional. |
| `MED_SPDATA_ATENDIMENTOS` | Espelho local dos atendimentos do SPDATA `ATCABECATEND`. | Contem paciente, CPF, prontuario, contato, endereco e dados de atendimento. Sensivel. |
| `MED_ATENDIMENTOS` | Controle local do atendimento medico sobre registros vindos do SPDATA, incluindo status local. | Controle operacional do atendimento vinculado a paciente e medico. |
| `MED_SPDATA_CONVENIOS` | Espelho local dos convenios do SPDATA `TBCONVEN`. | Dado administrativo, podendo ser dado pessoal quando associado a paciente. |
| `MED_SPDATA_ESPECIALIDADES` | Espelho local das especialidades do SPDATA `TBESPEC`. | Dado administrativo/profissional. |

### Modelos E Padroes Medicos

| Tabela | O que faz no sistema | Observacao LGPD/seguranca |
|---|---|---|
| `MODELO_ANAMNESE` | Modelos/padroes de anamnese criados por medico. | Deve evitar dados reais de pacientes em modelos. |
| `MODELO_SOLICITACAO_RECEITA` | Modelos de receita/prescricao. | Deve evitar dados reais de pacientes em modelos. |
| `MEDICAMENTOS_MODELO_RECEITA` | Medicamentos vinculados aos modelos de receita. | Catalogo operacional de modelos. |
| `MODELO_SOLICITACAO_EXAME` | Modelos de solicitacao de exame. | Deve evitar dados reais de pacientes em modelos. |
| `EXAMES_MODELO_EXAME` | Exames vinculados aos modelos de solicitacao de exame. | Catalogo operacional de modelos. |
| `MODELO_ORIENTACAO_EXAME` | Modelos de orientacao/preparo de exames criados por medico. | Deve conter orientacoes padrao, nao dados identificaveis de pacientes. |

### Seguranca, Auditoria E Integracoes

| Tabela | O que faz no sistema | Observacao LGPD/seguranca |
|---|---|---|
| `auditorias` | Registro de eventos relevantes do sistema e trilha LGPD. Guarda usuario, acao, entidade, entidade_id, descricao, IP, user-agent e data/hora. | Deve registrar metadados de acesso, sem conteudo clinico completo. |
| `logs_integracao` | Logs de integracoes/sincronizacoes com sistemas externos. | Evitar payloads com dados pessoais/sensiveis quando nao forem indispensaveis. |
| `fila_sincronizacao` | Fila para sincronizacoes pendentes com SPDATA ou outros destinos. Guarda tipo de evento, referencia, payload, status, tentativas e erro. | Payload pode conter dado sensivel. Deve ser minimizado e protegido. |

## Auditoria LGPD

A tabela `auditorias` passou a ser usada como trilha LGPD para responder quem acessou, quando acessou, de onde acessou e qual entidade foi acessada.

### Eventos registrados atualmente

| Acao | Quando ocorre |
|---|---|
| `LOGIN_SUCESSO` | Login realizado com sucesso. |
| `LOGIN_FALHA` | Tentativa de login com credenciais invalidas. |
| `LOGOUT` | Encerramento de sessao. |
| `ACESSO_NEGADO` | Usuario autenticado tenta acessar rota sem perfil permitido. |
| `VISUALIZOU_AGENDA` | Medico consulta agenda medica. |
| `VISUALIZOU_CHECK_IN` | Recepcao consulta check-in. |
| `VISUALIZOU_NO_SHOW` | Recepcao consulta no-show. |
| `VISUALIZOU_RETENCAO_EXAMES` | Recepcao consulta retencao/conversao de exames. |
| `VISUALIZOU_PRONTUARIO` | Medico consulta historico/prontuario local. |
| `VISUALIZOU_HISTORICO_BIODATA` | Medico consulta historico antigo do BioData. |
| `VISUALIZOU_DOCUMENTOS_MEDICOS` | Medico lista documentos medicos. |
| `SALVOU_DOCUMENTO_MEDICO` | Medico salva documento medico. |
| `EXPORTOU_DADOS` | Reservado para controle de exportacao de dados. |

### Campos principais da auditoria

| Campo | Uso |
|---|---|
| `usuario_id` | Usuario que executou a acao. |
| `medico_id` | Medico relacionado, quando aplicavel. |
| `acao` | Tipo de evento LGPD/operacional. |
| `entidade` | Tipo da entidade acessada, como `paciente`, `check_in`, `no_show`. |
| `entidade_id` | Identificador da entidade, quando aplicavel. |
| `descricao` | Resumo curto do evento, sem conteudo clinico completo. |
| `ip` | IP de origem ou `X-Forwarded-For`. |
| `user_agent` | Navegador/cliente usado no acesso. |
| `created_at` | Data/hora do evento. |

## Classificacao LGPD Dos Dados

| Dado | Classificacao | Tabelas principais |
|---|---|---|
| Nome do paciente | Pessoal | `atendimentos`, `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS`, BioData |
| CPF do paciente | Pessoal | `atendimentos`, `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS`, BioData |
| Telefone, celular, e-mail e endereco | Pessoal | `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS`, `RICADPAC` |
| Prontuario | Sensivel/assistencial | `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS` |
| Anamnese | Sensivel | `anamneses`, `[BioData].[dbo].[tblAnamnese]` |
| Evolucao medica | Sensivel | `evolucoes_medicas`, `evolucoes_medicas_versoes` |
| Diagnostico/CID | Sensivel | `diagnosticos`, `TBCID10` |
| Prescricao | Sensivel | `prescricoes`, `documentos_medicos` |
| Solicitacao de exame | Sensivel | `solicitacoes_exames`, `exames` |
| Documento medico | Sensivel | `documentos_medicos` |
| Convenio | Administrativo/pessoal quando vinculado ao paciente | `TBCONVEN`, `MED_SPDATA_CONVENIOS`, `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS` |
| Dados de usuario | Pessoal/credencial | `usuarios`, `auditorias` |
| Logs de auditoria | Metadado de seguranca | `auditorias` |
| Payloads de integracao | Variavel, pode ser sensivel | `logs_integracao`, `fila_sincronizacao` |

## Resumo Por Funcao

| Area | Tabelas principais |
|---|---|
| Autenticacao e usuarios | `usuarios`, `medicos` |
| Auditoria e LGPD | `auditorias` |
| Agenda | `REPACAGD`, `MED_SPDATA_AGENDA` |
| Atendimento SPDATA | `ATCABECATEND`, `RICADPAC`, `TBCBOPRO`, `TBPROFIS`, `TBCONVEN` |
| Atendimento local | `atendimentos`, `MED_ATENDIMENTOS`, `MED_SPDATA_ATENDIMENTOS` |
| Prontuario local | `anamneses`, `evolucoes_medicas`, `diagnosticos`, `prescricoes`, `solicitacoes_exames`, `documentos_medicos` |
| Historico antigo BioData | `[BioData].[dbo].[tblAnamnese]`, `[Repositorio].[dbo].[tblCliente]`, `[BioData].[dbo].[tblProfissional]` |
| Exames | `SITABPRO`, `exames`, `solicitacoes_exames` |
| Convenios | `TBCONVEN`, `MED_SPDATA_CONVENIOS`, `TBTISS` |
| Medicos | `TBPROFIS`, `TBCBOPRO`, `TBMEDESP`, `medicos`, `usuarios` |
| Especialidades | `TBESPEC`, `MED_SPDATA_ESPECIALIDADES` |
| Modelos/padroes | `MODELO_ANAMNESE`, `MODELO_SOLICITACAO_RECEITA`, `MEDICAMENTOS_MODELO_RECEITA`, `MODELO_SOLICITACAO_EXAME`, `EXAMES_MODELO_EXAME`, `MODELO_ORIENTACAO_EXAME` |
| Integracoes e sincronizacao | `logs_integracao`, `fila_sincronizacao` |

## Tela De Retencao/Conversao De Exames

Hoje a tela de retencao/conversao de exames usa principalmente dados locais e espelhos do SPDATA.

| Origem | Tabelas usadas |
|---|---|
| Sistema local | `solicitacoes_exames`, `atendimentos`, `exames`, `medicos` |
| Espelho SPDATA local | `MED_SPDATA_ATENDIMENTOS`, `MED_SPDATA_AGENDA` |
| SPDATA original | Dados vieram indiretamente de `ATCABECATEND`, `REPACAGD`, `RICADPAC`, `TBCONVEN`, `TBPROFIS`, `TBCBOPRO`, `TBESPEC` |
| Auditoria | `auditorias`, quando a tela e consultada. |

### Dados Que A Retencao/Conversao Consegue Preencher Hoje

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

Ainda nao usamos uma tabela real do SPDATA para pedido, agendamento, execucao, laudo ou faturamento de exames. Para evoluir a tela de retencao/conversao de exames com dados reais completos, precisamos identificar no SPDATA as tabelas responsaveis por:

1. Pedido/solicitacao de exame.
2. Itens do pedido de exame.
3. Agenda de exames/procedimentos.
4. Execucao/realizacao do exame.
5. Laudo/resultado.
6. Guia/autorizacao.
7. Valores/tabela/faturamento por convenio.
8. Historico de contato, se existir no SPDATA.
