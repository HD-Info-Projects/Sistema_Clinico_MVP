# Documentação LGPD e IA - Situação Atual do Projeto

Data de referência: 2026-07-30

Este documento consolida, em um único arquivo, a documentação existente ou inferida a partir do código do projeto `Sistema_Clinico_MVP` para os seguintes temas: Inventário de Dados, ROPA, RIPD, Política de Inteligência Artificial, Compartilhamento de Bases, Anonimização e Pseudonimização, Controle de Acesso, Retenção e Descarte de Dados de Desenvolvimento e Resposta a Incidentes envolvendo IA.

Este é um documento técnico-operacional inicial. Ele deve ser validado pela área jurídica, pelo Encarregado/DPO, pela segurança da informação e pelos responsáveis assistenciais antes de ser usado como política corporativa definitiva.

## 1. Escopo Avaliado

O projeto é um sistema clínico MVP composto por:

| Componente | Tecnologia | Função observada |
|---|---|---|
| Backend | Flask, SQLAlchemy, JWT, Flask-Limiter | API clínica, autenticação, integração com bancos externos, persistência local. |
| Frontend | Nuxt, Vue, Pinia, Nuxt server routes | Interface médica, recepção, painel de chamadas, proxy seguro para backend. |
| Banco local | MySQL 8.4 | Dados locais do sistema, usuários, atendimentos, prontuário local, espelhos do SPData. |
| Cache/rate limit | Redis | Cache técnico e armazenamento de rate limit. |
| Proxy | Caddy | HTTPS público e proxy reverso para o frontend. |
| Integração SPData | Firebird externo | Agenda, atendimentos, pacientes, médicos, convênios, especialidades, exames e CID. |
| Integração BioData | SQL Server externo | Histórico antigo de anamnese/prontuário. |
| IA/TTS | `edge-tts` | Síntese de voz para chamada de paciente no painel público. |

Arquivos e áreas usados como referência:

| Área | Referências no projeto |
|---|---|
| Modelos locais | `backend/src/models/**/*.py` |
| Rotas backend | `backend/src/routes/**/*.py` |
| Serviços de integração | `backend/src/services/**/*.py` |
| Autenticação e autorização | `backend/src/routes/login_route.py`, `backend/src/controllers/login_controller.py`, `backend/src/security/decorators.py`, `frontend/server/utils/auth.ts` |
| Frontend e painel público | `frontend/app/pages/**/*.vue`, `frontend/server/api/**/*.ts` |
| Deploy e infraestrutura | `docker-compose.yml`, `Caddyfile`, `.env.example`, `DEPLOY_DOCKER_VPS.md` |
| Tabelas e integrações | `documentacao_tabelas_integracoes.md` |

## 2. Inventário de Dados Utilizados no Projeto

### 2.1 Dados de usuários internos

| Categoria | Dados tratados | Origem | Armazenamento | Observação |
|---|---|---|---|---|
| Identificação de usuário | Nome completo, CPF/CNPJ, e-mail, perfil/role | Cadastro admin, comandos CLI, SPData para médicos | `usuarios` | Perfil observado: `medico`, `recepcao`, `admin`. |
| Credencial | Senha | Cadastro admin, comandos CLI | `usuarios.senha` | A senha é usada na autenticação. O código atual compara diretamente `usuario.senha != senha`. |
| Dados profissionais médicos | CRM, CRM de atendimento SPData, UF do CRM, RQE, especialidade, vínculo com SPData | SPData e cadastro local | `medicos` | Usado para filtrar agenda e prontuário por médico autenticado. |
| Sessão/autenticação | JWT, claims de usuário, cookie `auth_token`, cookie `active_clinica_id` | Login | Cookie HTTP-only no Nuxt e JWT no backend | JWT expira por configuração, padrão observado de 7 dias. |

### 2.2 Dados de pacientes e agenda

| Categoria | Dados tratados | Origem | Armazenamento/uso | Sensibilidade |
|---|---|---|---|---|
| Identificação de paciente | Nome, CPF, prontuário, ID SPData | SPData Firebird | `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS`, `MED_ATENDIMENTOS`, `atendimentos` | Dado pessoal comum e identificador de saúde. |
| Contato | Telefone, celular, e-mail, endereço | SPData Firebird | Espelhos locais e respostas de API | Dado pessoal comum. |
| Dados demográficos | Data de nascimento, sexo | SPData Firebird | Espelhos locais e frontend | Dado pessoal comum, associado ao contexto de saúde. |
| Agenda e comparecimento | Data, hora, status, falta/no-show, check-in, médico, convênio, unidade, observações | SPData e sistema local | `MED_SPDATA_AGENDA`, `MED_ATENDIMENTOS` | Dado de saúde operacional. |
| Painel de chamada | Nome do paciente, local de atendimento, horário da chamada | Frontend/Nuxt server memory | Memória do servidor Nuxt, histórico limitado a 100 chamadas | Exposto publicamente no painel de chamada. |

### 2.3 Dados clínicos e prontuário local

| Categoria | Dados tratados | Origem | Armazenamento | Sensibilidade |
|---|---|---|---|---|
| Atendimento | Paciente, CPF, IDs SPData, médico, status, data, hora inicial/final | Médico e SPData | `atendimentos` | Dado pessoal sensível por contexto assistencial. |
| Anamnese | Queixa principal, história da doença atual, antecedentes pessoais/familiares, alergias, medicamentos em uso, hábitos de vida, observações | Médico | `anamneses` | Dado pessoal sensível de saúde. |
| Evolução médica | Texto da evolução, versão, status, médico responsável | Médico | `evolucoes_medicas`, `evolucoes_medicas_versoes` | Dado pessoal sensível de saúde. |
| Diagnóstico | CID, descrição, diagnóstico descritivo, principal/secundário | Médico e base CID do SPData | `diagnosticos` | Dado pessoal sensível de saúde. |
| Prescrição | Medicamento, dosagem, frequência, duração, orientações | Médico | `prescricoes` | Dado pessoal sensível de saúde. |
| Solicitação de exame | Tipo, exame, descrição, justificativa, orientação, status | Médico e catálogo SPData | `solicitacoes_exames`, `exames` | Dado pessoal sensível de saúde. |
| Documentos médicos | Atestado, encaminhamento, solicitação de procedimento, dados em JSON | Médico | `documentos_medicos` | Dado pessoal sensível de saúde. |
| Histórico antigo | Anamnese antiga, paciente, CPF, médico, data | BioData/SQL Server | Consultado sob demanda, retornado pela API | Dado pessoal sensível de saúde. |

### 2.4 Modelos e padrões médicos

| Categoria | Dados tratados | Armazenamento | Observação |
|---|---|---|---|
| Modelo de anamnese | Nome do modelo, conteúdo, médico | `MODELO_ANAMNESE` | Pode conter texto clínico livre se o médico inserir dados reais. |
| Modelo de receita | Nome do modelo, medicamentos, dosagem, detalhes | `MODELO_SOLICITACAO_RECEITA`, `MEDICAMENTOS_MODELO_RECEITA` | Deve ser tratado como dado clínico se contiver referência a paciente. |
| Modelo de exame | Nome do modelo, exames vinculados | `MODELO_SOLICITACAO_EXAME`, `EXAMES_MODELO_EXAME` | Em regra é padrão clínico, mas pode conter texto livre. |
| Modelo de orientação | Nome do modelo, conteúdo HTML/texto | `MODELO_ORIENTACAO_EXAME` | Sanitização é aplicada no frontend ao exibir orientação. |

### 2.5 Dados de integração, auditoria e logs

| Categoria | Dados tratados | Armazenamento | Situação observada |
|---|---|---|---|
| Logs de integração | Ação, método, endpoint, payload enviado, resposta recebida, status, erro | `logs_integracao` | Modelo existe. Não foi encontrado uso efetivo criando registros. |
| Fila de sincronização | Tipo de evento, referência, payload, status, tentativas, erro | `fila_sincronizacao` | Modelo existe. Não foi encontrado uso efetivo criando registros. |
| Auditoria | Usuário, médico, ação, entidade, IP, user agent, descrição | `auditorias` | Modelo existe. Não foi encontrado uso efetivo criando registros. |
| Logs de aplicação | Exceções, requisições e mensagens no logger | stdout/container logs | Logging centralizado com `X-Request-ID`, formato configurável, cores apenas em texto/local e sanitização de credenciais e identificadores sensíveis. |

### 2.6 Dados de IA/TTS

| Categoria | Dados tratados | Origem | Destino | Observação |
|---|---|---|---|---|
| Texto para fala | Nome do paciente e local de atendimento | Painel de chamada | Backend Flask e biblioteca `edge-tts` | Texto limitado a 240 caracteres. |
| Áudio gerado | Áudio MP3 da chamada | Serviço TTS | Browser do painel | Resposta com `Cache-Control: no-store`. |
| Rate limit TTS | IP e contagem de requisições em memória | Nuxt server | Memória do processo | Limite observado: 30 requisições por minuto por IP. |

## 3. Registro das Operações de Tratamento (ROPA)

As bases legais abaixo não estão formalizadas no código. Onde indicado, a base deve ser validada pela área jurídica e pelo Encarregado/DPO.

| Operação | Finalidade | Titulares | Dados tratados | Fonte | Sistema/tabelas | Acesso observado | Compartilhamento | Base legal a validar |
|---|---|---|---|---|---|---|---|---|
| Autenticação de usuários | Permitir acesso ao sistema por usuário interno | Médicos, recepção, admins | E-mail, senha, nome, CPF/CNPJ, role, JWT | Cadastro local/SPData | `usuarios`, `medicos` | Login público, `/login/me` autenticado | Backend e frontend | Execução de contrato/trabalho, legítimo interesse e segurança. |
| Cadastro de médico a partir do SPData | Criar usuário médico local vinculado ao cadastro SPData | Médicos | Nome, CPF/CNPJ, e-mail, CRM, especialidade | SPData `TBPROFIS`, `TBCBOPRO`, `TBESPEC`, `TBMEDESP` | `usuarios`, `medicos` | Admin e CLI | SPData para banco local | Obrigação regulatória/execução de contrato assistencial. |
| Consulta de agenda médica | Exibir pacientes atribuídos ao médico | Pacientes, médicos | Nome, CPF, prontuário, agenda, contato, convênio, médico, observação | SPData | `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS` | Role `medico` | SPData para sistema local e frontend | Tutela da saúde/execução assistencial. |
| Check-in/recepção | Organizar atendimento do dia | Pacientes, médicos | Agenda, status, paciente, CPF, telefone, convênio, especialidade | SPData e local | `MED_SPDATA_AGENDA`, `MED_ATENDIMENTOS` | Role `recepcao` | Backend para frontend recepção | Tutela da saúde/execução assistencial. |
| No-show | Identificar faltas e não confirmações | Pacientes | Nome, telefone, CPF, prontuário, médico, convênio, data da falta | SPData e local | `MED_SPDATA_AGENDA`, `MED_ATENDIMENTOS` | Role `recepcao` | Backend para frontend recepção | Gestão assistencial e administrativa. |
| Retenção/conversão de exames | Acompanhar exames solicitados e realizados | Pacientes, médicos | Exame, CPF, prontuário, médico, convênio, valores estimados, datas | Sistema local e SPData | `solicitacoes_exames`, `atendimentos`, `exames`, `SILANEXA`, `SICADATE`, `SITABPRO` | Role `recepcao` | SPData para sistema local e frontend | Gestão assistencial/administrativa. |
| Registro de atendimento clínico | Documentar consulta e conduta médica | Pacientes, médicos | Anamnese, evolução, CID, prescrição, exames, documentos | Médico | `atendimentos`, `anamneses`, `evolucoes_medicas`, `diagnosticos`, `prescricoes`, `solicitacoes_exames`, `documentos_medicos` | Role `medico`, filtrado por CRM | Banco local e frontend médico | Tutela da saúde e obrigação regulatória de prontuário. |
| Consulta de histórico local | Apoiar decisão médica com registros anteriores | Pacientes | Histórico de atendimento, anamnese, CIDs, medicamentos, exames | Banco local | Tabelas clínicas locais | Role `medico`, com validação de vínculo com paciente | Backend para frontend médico | Tutela da saúde. |
| Consulta de histórico BioData | Consultar anamneses antigas | Pacientes | Nome, CPF, anamnese antiga, médico, data | BioData/SQL Server | `[BioData].[dbo].[tblAnamnese]`, `[Repositorio].[dbo].[tblCliente]` | Role `medico`, com validação de vínculo | SQL Server para backend e frontend | Tutela da saúde/continuidade assistencial. |
| Busca de CID | Apoiar preenchimento de diagnóstico | Pacientes indiretamente | Código e nome de doença CID | SPData `TBCID10` | Cache Redis por termo | Role `medico` | SPData para Redis/backend/frontend | Apoio assistencial, sem dado identificável direto na busca. |
| Modelos médicos | Reutilizar textos e conjuntos padrão | Médicos; eventualmente pacientes se dados reais forem inseridos | Conteúdo de anamnese, receita, exames, orientação | Médico | Tabelas de modelos | Role `medico`, por `medico_id` | Banco local e frontend médico | Produtividade assistencial. |
| Painel de chamada | Chamar paciente para local de atendimento | Pacientes | Nome do paciente e local | Usuário autenticado que cria chamada | Memória do Nuxt server | Endpoint público de painel | Exibição pública em tela e SSE público | Interesse legítimo/execução do atendimento, com minimização a revisar. |
| Síntese de voz TTS | Reproduzir chamada do paciente por áudio | Pacientes | Nome do paciente e local | Painel de chamada | Backend Flask/TTS | Endpoint TTS sem JWT, com rate limit no Nuxt | Serviço externo usado por `edge-tts` | Deve ser validada, pois envolve terceiro/provedor de TTS. |
| Backup operacional | Recuperar banco local | Pacientes, usuários internos | Dump MySQL completo | Banco local | Arquivo de backup manual | Operador de infraestrutura | Ambiente de backup | Segurança/continuidade do serviço. |

## 4. Relatório de Impacto à Proteção de Dados (RIPD) - Versão Técnica Inicial

### 4.1 Contexto e necessidade

O sistema processa dados pessoais e dados pessoais sensíveis de saúde em contexto clínico, incluindo prontuário, anamnese, diagnóstico, prescrição e solicitações de exames. O tratamento é necessário para execução de atendimento médico, continuidade assistencial, gestão de agenda, apoio à recepção e acompanhamento de exames/no-show.

### 4.2 Fluxo resumido dos dados

| Etapa | Fluxo |
|---|---|
| 1 | Usuário interno autentica no frontend Nuxt. |
| 2 | Nuxt envia credenciais para Flask e recebe JWT. |
| 3 | JWT é armazenado no cookie `auth_token` com `httpOnly`, `sameSite=strict` e `secure` configurável. |
| 4 | Backend consulta SPData/Firebird para agenda, atendimentos, pacientes, médicos, convênios, especialidades, exames e CID. |
| 5 | Backend grava espelhos locais e registros clínicos no MySQL. |
| 6 | Médico registra atendimento, anamnese/evolução, diagnósticos, prescrições, exames e documentos médicos. |
| 7 | Backend pode consultar histórico antigo no BioData/SQL Server mediante validação de vínculo do médico com o paciente. |
| 8 | Recepção consulta check-in, no-show e retenção/conversão de exames. |
| 9 | Painel público exibe e pode anunciar nome do paciente e local via TTS. |

### 4.3 Riscos identificados e medidas existentes

| Risco | Impacto | Medidas existentes observadas | Risco residual |
|---|---|---|---|
| Acesso indevido por usuário sem perfil adequado | Alto | JWT, decorators `roles_required`, middleware frontend por role | Médio, pois nem todas as rotas têm role específico e não há política formal de permissões por dado. |
| Médico acessar paciente de outro médico | Alto | Validação por CRM em agenda e histórico (`get_crm_medico_usuario`, `_referencia_autorizada_paciente`) | Médio, depende da consistência do CRM e das regras implementadas. |
| Vazamento por credenciais fracas ou senha em texto claro | Alto | Login com rate limit por IP/e-mail | Alto, pois senha não está hasheada no modelo atual. |
| Exposição de dados em painel público | Médio/Alto | Painel público remove `pacienteId` e médico responsável, mas mantém nome do paciente | Médio/Alto, pois nome do paciente é exibido e anunciado. |
| Envio de texto com dado pessoal para TTS externo | Médio/Alto | Limite de 240 caracteres, cache `no-store`, rate limit | Médio/Alto, falta contrato/avaliação do fornecedor TTS. |
| Retenção excessiva no MySQL | Alto | Timestamps em tabelas e exclusões técnicas por cascata em alguns relacionamentos | Alto, não há rotina formal de expurgo por prazo. |
| Logs com dados pessoais | Médio | Logging centralizado, `X-Request-ID`, mensagens genéricas em exceções e sanitização de credenciais/identificadores sensíveis | Médio, ainda exige disciplina para não registrar payloads clínicos completos em novos logs. |
| Uso de dados reais em desenvolvimento | Alto | `.env` ignorado, alerta para remover credenciais locais | Alto, não há plano formal de dados de desenvolvimento. |
| Exposição por CORS amplo | Médio | CORS inicializado no Flask | Médio, não há configuração restritiva visível por domínio. |
| Dados sensíveis em modelos médicos | Médio | Modelos vinculados ao médico por `medico_id` | Médio, falta alerta/validação para impedir dados reais de paciente em modelos. |

### 4.4 Medidas de segurança já observadas

| Medida | Evidência no projeto |
|---|---|
| HTTPS público via Caddy | `Caddyfile`, `docker-compose.yml`, `DEPLOY_DOCKER_VPS.md` |
| Backend não exposto publicamente no Compose | `docker-compose.yml`, backend com `expose: 5000` |
| MySQL e Redis em rede Docker | `docker-compose.yml` |
| JWT para rotas autenticadas | `flask_jwt_extended`, `@jwt_required()` |
| Controle por perfil | `roles_required("medico")`, `roles_required("recepcao")`, `roles_required("admin")` |
| Cookie de autenticação HTTP-only | `frontend/server/utils/auth.ts` |
| Rate limit de login | `Flask-Limiter`, `LOGIN_RATE_LIMIT_IP`, `LOGIN_RATE_LIMIT_EMAIL` |
| Rate limit de TTS | `frontend/server/api/tts/speak.post.ts` |
| Sanitização de HTML clínico no frontend | `DOMPurify` em `useSanitize.ts` e `guia-tiss.ts` |
| Cache com TTL para CID | Redis TTL de 3600 segundos em busca CID |
| Limpeza de rascunhos locais no logout | `limparRascunhosClinicosLocais()` remove chaves `medsystem:atendimento-draft:*` |

### 4.5 Conclusão preliminar do RIPD

O projeto possui controles iniciais relevantes para autenticação, autorização por perfil, isolamento parcial por médico, HTTPS, rate limit e sanitização de HTML. Porém, por tratar dados sensíveis de saúde e envolver integrações externas, o risco residual permanece alto até que sejam implementados hash de senha, retenção/descarte formal, auditoria efetiva, revisão de CORS/headers, anonimização para desenvolvimento e governança do uso de TTS/IA.

## 5. Política de Inteligência Artificial - Situação Atual

### 5.1 Uso de IA identificado

O único uso de IA/serviço inteligente identificado no código é a síntese de voz com `edge-tts`, usada no painel de chamada de pacientes.

| Item | Situação atual |
|---|---|
| Finalidade | Converter texto de chamada em áudio para o painel público. |
| Texto enviado | Nome do paciente e local de atendimento, no formato observado: `Nome, por favor dirija-se à Local`. |
| Limite técnico | 240 caracteres no frontend server e backend Flask. |
| Endpoint frontend | `POST /api/tts/speak` |
| Endpoint backend | `POST /tts/speak` |
| Vozes | `pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural` |
| Cache | Resposta com `Cache-Control: no-store`. |
| Decisão automatizada | Não identificada. O TTS não decide conduta clínica, triagem, diagnóstico ou prioridade. |

### 5.2 Princípios aplicáveis ao uso atual

| Princípio | Aplicação atual |
|---|---|
| Finalidade limitada | Uso restrito a chamada de paciente. |
| Minimização | Texto limitado, mas ainda contém nome do paciente. |
| Transparência | Não há aviso formal no código/documentação para pacientes sobre uso de TTS. |
| Supervisão humana | Chamada é iniciada por usuário autenticado ou fluxo do painel. |
| Não substituição clínica | Não há IA para decisão clínica. |
| Segurança | Rate limit, limite de tamanho e resposta sem cache. |

### 5.3 Regras operacionais atuais inferidas

| Regra | Situação |
|---|---|
| Não usar IA para diagnóstico ou prescrição | Não há código de IA para esse fim. |
| Não enviar anamnese, diagnóstico ou prontuário para IA | Não foi encontrado envio desses dados para LLM/IA. |
| Não usar IA generativa para preencher prontuário | Não foi encontrado uso de LLM. |
| Usar TTS apenas para chamadas curtas | Implementado por limite de 240 caracteres. |
| Evitar armazenamento do áudio | Resposta TTS usa `no-store`; o browser cria URL temporária e revoga após uso. |

## 6. Procedimento para Compartilhamento de Bases de Dados - Situação Atual

### 6.1 Bases compartilhadas ou integradas

| Origem/Destino | Tipo | Dados compartilhados | Mecanismo | Direção |
|---|---|---|---|---|
| SPData/Firebird | Banco externo | Agenda, atendimentos, pacientes, médicos, convênios, especialidades, exames, CID | Conexão por variáveis `FIREBIRD_*` | SPData para sistema local/backend. |
| BioData/SQL Server | Banco externo | Histórico antigo de anamnese/prontuário | Conexão por variáveis `SQLSERVER_*` | BioData para backend/frontend. |
| MySQL local | Banco da aplicação | Usuários, atendimentos, espelhos, registros clínicos | SQLAlchemy | Backend para persistência local. |
| Redis | Cache/rate limit | Cache CID e rate limit | Redis | Backend/Nuxt para Redis. |
| Frontend Nuxt | Aplicação web | Dados necessários para telas médicas/recepção | APIs internas Nuxt e Flask | Backend para usuário autenticado. |
| Painel público | Tela pública | Nome do paciente, local, horário | SSE público e endpoint público de chamadas | Nuxt server para tela pública. |
| TTS externo via `edge-tts` | Serviço de síntese de voz | Texto da chamada | Biblioteca `edge-tts` | Backend para serviço TTS e retorno de áudio. |

### 6.2 Procedimento técnico atualmente observado

| Etapa | Situação atual |
|---|---|
| Configuração de credenciais | Via variáveis de ambiente no `.env`, com `.env` ignorado no Git. |
| Execução de integrações | Backend abre conexões server-to-server com Firebird e SQL Server. |
| Persistência de espelhos | Dados do SPData são normalizados e gravados em tabelas locais `MED_*` e `exames`. |
| Acesso ao histórico BioData | Consulta sob demanda com validação de referência autorizada do paciente. |
| Exposição ao frontend | Via Nuxt server routes e APIs Flask autenticadas com JWT, exceto painel público/TTS. |
| Registro de compartilhamento | Modelos `logs_integracao` e `auditorias` existem, mas não foi encontrado registro efetivo. |

### 6.3 Tabelas externas principais mapeadas

| Sistema | Tabelas |
|---|---|
| SPData/Firebird | `REPACAGD`, `ATCABECATEND`, `RICADPAC`, `TBCBOPRO`, `TBPROFIS`, `TBESPEC`, `TBMEDESP`, `TBCONVEN`, `SITABPRO`, `TBTISS`, `TBCID10`, `SILANEXA`, `SICADATE`, `SIREFCON`, `PRSITEXAME`, `TBVLRTHM` |
| BioData/SQL Server | `[BioData].[dbo].[tblAnamnese]`, `[Repositorio].[dbo].[tblCliente]`, `[BioData].[dbo].[tblProfissional]` |
| Sistema local | `usuarios`, `medicos`, `atendimentos`, `anamneses`, `evolucoes_medicas`, `evolucoes_medicas_versoes`, `diagnosticos`, `prescricoes`, `solicitacoes_exames`, `documentos_medicos`, `exames`, `MED_SPDATA_AGENDA`, `MED_SPDATA_ATENDIMENTOS`, `MED_ATENDIMENTOS`, `MED_SPDATA_CONVENIOS`, `MED_SPDATA_ESPECIALIDADES`, modelos médicos, `auditorias`, `logs_integracao`, `fila_sincronizacao` |

## 7. Procedimento de Anonimização e Pseudonimização - Situação Atual

Não foi encontrada rotina formal de anonimização ou pseudonimização de dados pessoais/sensíveis no backend, banco local, scripts ou documentação.

### 7.1 Medidas parciais observadas

| Medida | Situação | Limitação |
|---|---|---|
| Painel público remove `pacienteId` e médico responsável | `chamadoPublico()` retorna `pacienteId: 0` e `medicoResponsavel: ''` | O nome do paciente continua exposto. |
| Normalização de CPF | `normalizar_cpf()` padroniza CPF | Não é anonimização nem pseudonimização. |
| Sanitização HTML | DOMPurify remove conteúdo perigoso no frontend | Protege contra XSS, não anonimiza dados. |
| Limpeza de rascunhos no logout | Remove chaves locais de draft clínico | Não cobre todos os cenários de navegador/queda de sessão. |
| Histórico público de chamadas limitado | Memória mantém até 100 chamadas | Não anonimiza; apenas limita quantidade. |

### 7.2 Dados que permanecem identificáveis

| Local | Dados identificáveis |
|---|---|
| MySQL local | Nome, CPF, prontuário, contato, dados clínicos. |
| Espelhos SPData | Nome, CPF, prontuário, contato, nascimento, sexo, endereço, convênio. |
| Frontend autenticado | Dados do paciente e prontuário conforme perfil. |
| Painel público | Nome do paciente e local de atendimento. |
| Logs de erro | Possibilidade de conter dados se exceções incluírem payloads. |
| Backups | Dump completo do banco local. |

## 8. Procedimento de Controle de Acesso - Situação Atual

### 8.1 Autenticação

| Controle | Situação atual |
|---|---|
| Login | `POST /login/auth` no Flask, chamado por `/api/auth/login` no Nuxt. |
| Token | JWT gerado por `flask_jwt_extended.create_access_token`. |
| Expiração | `JWT_ACCESS_TOKEN_EXPIRES_SECONDS`, padrão 604800 segundos. |
| Cookie | `auth_token` com `httpOnly`, `sameSite: strict`, `secure` quando `NUXT_AUTH_COOKIE_SECURE=true`. |
| Rate limit de login | Por IP e e-mail via Flask-Limiter. |
| Logout | Remove cookie no Nuxt e limpa rascunhos clínicos locais. |

### 8.2 Autorização por perfil

| Perfil | Acessos observados |
|---|---|
| `medico` | Agenda médica, prontuário, histórico local/BioData, CID, modelos médicos, documentos médicos, atualização de status de atendimento. |
| `recepcao` | Check-in, no-show, retenção de exames. |
| `admin` | Registro de médico pela rota `/login/register`. |

### 8.3 Controles por vínculo assistencial

| Controle | Situação atual |
|---|---|
| Filtro por CRM | Agenda e atualização de status verificam CRM do médico autenticado. |
| Histórico por paciente | `_referencia_autorizada_paciente()` valida vínculo por atendimento, agenda, CPF ou atendimento local do médico. |
| Modelos por médico | Rotas de padrões filtram por `medico_id` autenticado. |

### 8.4 Exceções e áreas públicas

| Área | Situação |
|---|---|
| `/painel-chamada` | Página pública sem autenticação. |
| SSE público de TV | Endpoint público para painel de chamada. |
| TTS | Endpoint Nuxt `/api/tts/speak` não exige usuário autenticado e usa rate limit por IP. Backend Flask `/tts/speak` também não exige JWT. |
| Endpoint raiz | Público para healthcheck. |

## 9. Plano de Retenção e Descarte de Dados de Desenvolvimento - Situação Atual

Não foi encontrado plano formal implementado para retenção e descarte de dados em desenvolvimento.

### 9.1 Retenção observada por componente

| Componente | Retenção atual observada |
|---|---|
| MySQL local | Dados persistem indefinidamente em volume Docker `mysql_data`, salvo exclusão manual/aplicação. |
| Redis | Algumas chaves usam TTL, como CID por 3600 segundos e cache técnico; Redis também tem volume persistente. |
| Chamada de pacientes | Armazenada em memória do Nuxt server, limitada a 100 registros. Perde-se ao reiniciar o processo. |
| Rascunhos clínicos no navegador | Chaves `medsystem:atendimento-draft:*` em `localStorage`/`sessionStorage` são removidas no logout. |
| Backups MySQL | Há comando de backup manual em `DEPLOY_DOCKER_VPS.md`, sem prazo de retenção definido. |
| Logs de container | Dependem da configuração Docker/host; sem prazo definido no projeto. |
| Dados de desenvolvimento | Não há script de anonimização, geração sintética ou expurgo automático. |

### 9.2 Exclusões técnicas existentes

| Exclusão | Situação |
|---|---|
| Cascata de atendimento | Relacionamentos de atendimento usam `cascade="all, delete-orphan"` para dados clínicos dependentes. |
| Edição de atendimento | Ao salvar novos diagnósticos, prescrições ou exames, registros antigos relacionados podem ser apagados e recriados. |
| Exclusão de modelos | Rotas permitem deletar modelos e itens de modelos médicos. |
| Chamada pública | Histórico em memória remove registros antigos acima de 100. |

## 10. Plano de Resposta a Incidentes envolvendo IA - Situação Atual

Não foi encontrado plano formal de resposta a incidentes envolvendo IA. A resposta técnica possível, com base no sistema atual, se concentra no TTS.

### 10.1 Incidentes de IA/TTS considerados

| Incidente | Exemplo |
|---|---|
| Exposição indevida de dado pessoal | Nome de paciente ou local sensível anunciado em ambiente inadequado. |
| Envio excessivo de dados ao TTS | Texto contendo informação clínica além do nome/local. |
| Abuso do endpoint TTS | Terceiro gerando áudio em massa. |
| Falha do fornecedor TTS | Serviço externo indisponível ou retornando áudio incorreto. |
| Incidente de confidencialidade no provedor | Texto enviado ao TTS sendo retido ou acessado por terceiro. |

### 10.2 Controles técnicos atuais para resposta

| Controle | Situação |
|---|---|
| Limite de texto | 240 caracteres. |
| Rate limit | 30 requisições por minuto por IP no Nuxt server. |
| Cache | `Cache-Control: no-store` no áudio. |
| Desativação operacional | É possível remover/desabilitar a rota TTS ou o botão de áudio por alteração de código/configuração. |
| Logs técnicos | Falhas de TTS são registradas no logger do Flask/Nuxt. |

### 10.3 Papéis sugeridos para resposta

| Papel | Responsabilidade operacional esperada |
|---|---|
| Equipe técnica | Isolar endpoint, coletar logs, aplicar correção, confirmar escopo. |
| Encarregado/DPO | Avaliar impacto LGPD e necessidade de comunicação à ANPD/titulares. |
| Direção/gestão clínica | Avaliar impacto assistencial e orientar equipe. |
| Segurança da informação | Analisar abuso, credenciais, logs e perímetro. |

## 11. Resumo Executivo do Que Existe

| Documento exigido | Situação atual consolidada |
|---|---|
| Inventário de Dados | Mapeado neste documento com categorias, origens e armazenamentos. |
| ROPA | Estruturado neste documento com operações principais. Bases legais ainda precisam validação formal. |
| RIPD | Avaliação técnica inicial realizada com riscos e medidas existentes. |
| Política de IA | Uso atual limitado a TTS; sem IA para decisão clínica. |
| Compartilhamento de Bases | Integrações SPData, BioData, MySQL, Redis, frontend, painel público e TTS mapeadas. |
| Anonimização/Pseudonimização | Não há rotina formal; apenas medidas parciais. |
| Controle de Acesso | JWT, roles, cookies HTTP-only, rate limit e filtros por CRM existem. |
| Retenção/Descarte de Desenvolvimento | Não há plano formal; retenção atual é majoritariamente indefinida. |
| Resposta a Incidentes envolvendo IA | Não há plano formal; riscos e controles atuais de TTS foram mapeados. |
