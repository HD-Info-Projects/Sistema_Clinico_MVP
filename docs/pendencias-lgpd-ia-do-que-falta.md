# Pendências LGPD e IA - O Que Falta Implementar ou Formalizar

Data de referência: 2026-07-30

Este documento lista o que falta fazer para que o projeto `Sistema_Clinico_MVP` atenda de forma mais completa às exigências indicadas: Inventário de Dados, ROPA, RIPD, Política de Inteligência Artificial, Compartilhamento de Bases, Anonimização e Pseudonimização, Controle de Acesso, Retenção e Descarte de Dados de Desenvolvimento e Resposta a Incidentes envolvendo IA.

As pendências abaixo combinam lacunas técnicas observadas no código com lacunas documentais, jurídicas e operacionais. A priorização considera o fato de o sistema tratar dados pessoais sensíveis de saúde.

## 1. Resumo Prioritário

| Prioridade | Pendência | Motivo |
|---|---|---|
| Crítica | Implementar hash de senha e rotação de credenciais | Senha está armazenada/comparada em texto claro no código atual. |
| Crítica | Formalizar e restringir acesso a dados sensíveis por política e auditoria | Há dados clínicos sensíveis e modelo de auditoria não usado efetivamente. |
| Crítica | Criar plano formal de retenção/descarte para MySQL, backups, logs e desenvolvimento | Retenção atual é majoritariamente indefinida. |
| Alta | Criar procedimento real de anonimização/pseudonimização para dev/teste | Não há rotina de mascaramento para dados reais. |
| Alta | Formalizar compartilhamento com SPData, BioData e TTS | Integrações existem, mas falta base documental/contratual e matriz de responsáveis. |
| Alta | Revisar painel público e TTS para minimização de dados | Nome do paciente é exibido/anunciado publicamente e enviado ao TTS. |
| Alta | Configurar CORS e headers de segurança de forma restritiva | CORS está inicializado sem política visível por origem. |
| Média | Completar ROPA/RIPD com bases legais aprovadas | Bases legais não estão formalizadas no projeto. |
| Média | Definir plano de resposta a incidentes envolvendo IA/TTS | Não há procedimento formal. |

## 2. Inventário de Dados - Pendências

| Item exigido | O que falta | Ação recomendada | Prioridade |
|---|---|---|---|
| Dono do dado/processo | Não há responsável formal por cada conjunto de dados. | Nomear responsável de negócio e responsável técnico por módulo: agenda, prontuário, recepção, exames, painel de chamada, integrações. | Alta |
| Base legal por dado | Não está documentada oficialmente. | Validar bases legais com jurídico/DPO, especialmente dados de saúde, painel público e TTS. | Alta |
| Finalidade por campo | Há finalidade por módulo, mas não por campo. | Criar matriz campo a campo para tabelas sensíveis: `usuarios`, `atendimentos`, `anamneses`, `evolucoes_medicas`, `diagnosticos`, `prescricoes`, `solicitacoes_exames`, `documentos_medicos`, `MED_*`. | Média |
| Classificação de sensibilidade | Não há classificação formal no banco ou documentação oficial. | Classificar campos como comum, sensível, credencial, operacional, auditoria, log. | Média |
| Localização física/lógica | Há Compose e conexões, mas falta inventário de ambientes. | Registrar onde rodam VPS, MySQL, Redis, SPData, BioData, backups e logs. | Alta |
| Fluxo de dados com terceiros | TTS e bases externas precisam documentação contratual. | Mapear operadores/controladores, canais de conexão, criptografia e responsáveis. | Alta |

## 3. ROPA - Pendências

| Item exigido no ROPA | Lacuna atual | Ação recomendada | Prioridade |
|---|---|---|---|
| Base legal aprovada | Documento técnico apenas sugere validação. | Aprovar juridicamente bases legais por operação. | Alta |
| Categorias de titulares | Mapeadas parcialmente. | Formalizar titulares: pacientes, médicos, recepção, admins, acompanhantes/responsáveis se coletados. | Média |
| Retenção por operação | Não definida. | Associar prazo de retenção a cada operação do ROPA. | Alta |
| Medidas técnicas e organizacionais | Mapeadas parcialmente no código. | Complementar com controles organizacionais: treinamento, termo de confidencialidade, gestão de acessos, revisão periódica. | Média |
| Transferência internacional | Não avaliada para `edge-tts`/serviços externos. | Verificar se o provedor TTS processa dados fora do Brasil e registrar no ROPA. | Alta |
| Operadores e suboperadores | Não formalizados. | Registrar fornecedores: hospedagem/VPS, SPData, BioData, TTS/Microsoft ou serviço usado pelo `edge-tts`, provedores de backup. | Alta |

## 4. RIPD - Pendências

| Risco | Falta fazer | Ação recomendada | Prioridade |
|---|---|---|---|
| Senha em texto claro | Corrigir autenticação. | Usar `werkzeug.security.generate_password_hash` e `check_password_hash`, migrar senhas atuais, forçar redefinição/rotação. | Crítica |
| Acesso indevido | Fortalecer autorização. | Revisar todas as rotas com `@jwt_required()` sem `roles_required`, adicionar testes de autorização e validação por vínculo assistencial. | Alta |
| Ausência de auditoria efetiva | Modelo existe, mas não é usado. | Registrar login, falha de login, visualização de prontuário, consulta BioData, geração de documentos, exportações, alterações clínicas, chamadas públicas e uso de TTS. | Crítica |
| Retenção indefinida | Criar expurgo controlado. | Implementar políticas e jobs de retenção por tabela, logs, Redis, backups e ambientes de dev/teste. | Crítica |
| TTS com dado pessoal | Avaliar e minimizar. | Reduzir texto enviado, avaliar uso local/offline, criar aviso ao paciente, registrar fornecedor e base legal. | Alta |
| Painel público com nome de paciente | Minimização incompleta. | Avaliar chamada por senha, iniciais, primeiro nome ou código; restringir tela à área física adequada. | Alta |
| CORS amplo | Configuração não restritiva visível. | Definir origens permitidas por ambiente e bloquear origens desconhecidas. | Alta |
| Logs e payloads sensíveis | Política ausente. | Sanitizar logs, evitar imprimir payloads clínicos, configurar retenção e acesso restrito a logs. | Alta |
| Dados reais em desenvolvimento | Sem anonimização. | Proibir cópia direta de produção para dev sem anonimização; criar script de mascaramento. | Crítica |

## 5. Política de Inteligência Artificial - Pendências

| Tema | O que falta | Ação recomendada | Prioridade |
|---|---|---|---|
| Política formal de IA | Não há documento corporativo aprovado. | Aprovar política proibindo IA para decisão clínica sem validação, consentimento/base legal, DPIA e governança. | Alta |
| Registro de sistemas de IA | Apenas TTS foi identificado. | Criar inventário de IA com fornecedor, finalidade, dados enviados, retenção do fornecedor e riscos. | Alta |
| Governança do `edge-tts` | Falta avaliação de fornecedor. | Verificar termos, local de processamento, retenção de dados, segurança e possibilidade de DPA/contrato. | Alta |
| Aviso de transparência | Pacientes não são informados no projeto. | Incluir aviso físico/digital sobre chamada por painel e eventual síntese de voz. | Média |
| Minimização de dados no prompt/texto | Nome completo pode ser enviado. | Usar menor identificador possível: primeiro nome, senha de atendimento, iniciais ou número de chamada. | Alta |
| Bloqueio de dados clínicos no TTS | Não há filtro semântico, apenas limite de tamanho. | Validar texto de TTS para impedir CID, diagnóstico, exame, medicamento, CPF e termos clínicos. | Alta |
| Monitoramento de uso | Não há auditoria do TTS. | Registrar data, IP, usuário quando aplicável, texto minimizado/hash, status e erro sem armazenar conteúdo sensível desnecessário. | Média |

## 6. Procedimento para Compartilhamento de Bases de Dados - Pendências

| Compartilhamento | Lacuna | Ação recomendada | Prioridade |
|---|---|---|---|
| SPData/Firebird | Falta documento de autorização, finalidade e responsabilidades. | Formalizar acordo interno/contrato, escopo de tabelas, usuários técnicos, rede permitida e logs. | Alta |
| BioData/SQL Server | Histórico sensível é consultado sob demanda. | Formalizar base legal, escopo, perfil de acesso, trilha de auditoria e retenção de logs. | Alta |
| TTS externo | Texto de chamada pode sair do ambiente local. | Validar fornecedor, contrato, DPA, transferência internacional e alternativa local. | Alta |
| Redis | Persistente e usado para rate limit/cache. | Definir quais dados podem ir para cache, TTL obrigatório e limpeza. | Média |
| Backups | Procedimento existe, mas sem proteção/retencao. | Criptografar backup, restringir acesso, definir prazo, local e teste de restauração. | Crítica |
| Exportação de logos TISS | Pode gerar arquivos no frontend/public. | Confirmar que não contém dados pessoais e registrar no procedimento. | Baixa |
| Compartilhamento por painel público | Nome do paciente é exibido. | Formalizar regra de minimização e posicionamento do painel para evitar exposição indevida. | Alta |

## 7. Procedimento de Anonimização e Pseudonimização - Pendências

| Necessidade | Lacuna | Ação recomendada | Prioridade |
|---|---|---|---|
| Dados de desenvolvimento | Sem script de anonimização. | Criar pipeline para gerar base dev mascarada ou sintética. | Crítica |
| CPF | CPF real trafega e persiste. | Mascarar CPF em telas onde não for estritamente necessário; em dev substituir por CPF sintético válido. | Alta |
| Nome de paciente | Nome real usado em painel e TTS. | Usar código/senha de chamada ou primeiro nome quando possível. | Alta |
| Prontuário | Identificador real persistido. | Pseudonimizar em dev/teste com tabela de correspondência separada e protegida, ou gerar identificadores sintéticos. | Alta |
| E-mail/telefone/endereço | Dados reais em espelhos SPData. | Mascarar em dev/teste e ocultar parcialmente nas telas administrativas quando possível. | Alta |
| Dados clínicos livres | Anamnese/evolução podem reidentificar paciente. | Em dev/teste substituir textos por amostras sintéticas; não usar LLM externo com dados reais sem base legal/contrato. | Crítica |
| Logs | Podem conter dados em exceções. | Sanitizar mensagens e remover payloads sensíveis. | Alta |
| Backups | Dump completo identificável. | Criptografar e controlar acesso; para dev gerar dump anonimizado. | Crítica |

### 7.1 Regras mínimas sugeridas para anonimização em dev/teste

| Campo | Regra sugerida |
|---|---|
| Nome | Substituir por `Paciente 000001`, mantendo consistência por ID. |
| CPF | Gerar CPF sintético válido sem relação com o real. |
| E-mail | Usar domínio reservado, como `paciente000001@example.test`. |
| Telefone | Substituir por número fictício padronizado. |
| Endereço | Substituir por cidade/UF genérica ou valor nulo quando possível. |
| Prontuário | Gerar identificador aleatório ou sequencial sintético. |
| Texto clínico livre | Substituir por texto clínico sintético sem referência real. |
| Datas | Deslocar datas por offset consistente por paciente, quando análise temporal for necessária. |

## 8. Procedimento de Controle de Acesso - Pendências

| Controle | Lacuna | Ação recomendada | Prioridade |
|---|---|---|---|
| Hash de senha | Senhas em texto claro. | Implementar hash, política de senha e rotação. | Crítica |
| MFA | Não existe. | Avaliar MFA para admin e perfis com acesso a dados sensíveis. | Alta |
| Bloqueio/expiração de conta | Não existe política visível. | Implementar status de usuário, bloqueio por tentativas, desativação e revisão periódica. | Alta |
| Perfis granulares | Roles são simples. | Criar matriz de permissões por módulo, ação e dado. | Média |
| Auditoria de acesso | Modelo existe, mas sem uso. | Registrar visualização e alteração de dados sensíveis. | Crítica |
| Rotas sem role | Algumas rotas têm JWT, mas não role específico. | Revisar `/exames`, documentos e demais endpoints, aplicando menor privilégio. | Alta |
| Sessão longa | JWT padrão de 7 dias. | Avaliar redução de expiração, refresh token seguro ou renovação controlada. | Média |
| Revogação de sessão | Logout remove cookie, mas JWT continua válido até expirar. | Implementar lista de revogação ou sessão server-side para casos críticos. | Média |
| CORS | Sem origem restrita visível. | Configurar CORS por `APP_DOMAIN`/ambiente. | Alta |
| Headers de segurança | Caddy só faz proxy/encoding. | Adicionar CSP, HSTS explícito, X-Frame-Options/Frame-Ancestors, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. | Média |

## 9. Plano de Retenção e Descarte de Dados de Desenvolvimento - Pendências

| Item | Lacuna | Ação recomendada | Prioridade |
|---|---|---|---|
| Política de ambiente | Não há separação documental clara entre produção, homologação e dev. | Definir ambientes, responsáveis, dados permitidos e restrições. | Alta |
| Uso de dados reais em dev | Não há proibição técnica/documental. | Proibir dados reais fora de produção sem autorização formal e anonimização. | Crítica |
| Retenção do banco dev | Indefinida. | Definir prazo máximo, por exemplo 30/60/90 dias, e expurgo automático. | Alta |
| Retenção de backups | Sem prazo. | Definir ciclo de backup, criptografia, armazenamento, retenção e descarte seguro. | Crítica |
| Retenção de logs | Sem prazo. | Configurar rotação de logs Docker/host e limpeza. | Alta |
| Retenção Redis | Parcialmente por TTL. | Exigir TTL para todo cache com dado pessoal e limpar volumes de dev periodicamente. | Média |
| Rascunhos no navegador | Limpam no logout apenas. | Adicionar expiração por tempo e limpeza ao iniciar sessão. | Média |
| Descarte seguro | Não há procedimento. | Documentar eliminação segura de dumps, volumes, arquivos temporários e mídias. | Alta |

### 9.1 Prazos iniciais a validar

| Tipo de dado | Prazo sugerido para desenvolvimento/teste |
|---|---|
| Base anonimizada de dev | Até 90 dias, renovável mediante necessidade. |
| Dump temporário para migração | Até 7 dias. |
| Logs de desenvolvimento | Até 30 dias. |
| Backups de homologação | Até 30 dias, se criptografados. |
| Rascunhos locais de navegador | Até 24 horas ou até logout, o que ocorrer primeiro. |
| Cache Redis com dado pessoal | Evitar; se inevitável, TTL menor possível. |

## 10. Plano de Resposta a Incidentes envolvendo IA - Pendências

| Etapa | O que falta | Ação recomendada | Prioridade |
|---|---|---|---|
| Detecção | Sem alerta específico para TTS/IA. | Registrar eventos de TTS e monitorar volume/anomalias. | Média |
| Classificação | Não há critérios de severidade. | Criar matriz de incidente: exposição pública, envio a terceiro, falha do provedor, abuso de endpoint. | Alta |
| Contenção | Não há toggle operacional. | Criar variável para desabilitar TTS sem deploy complexo, por exemplo `ENABLE_TTS=false`. | Alta |
| Evidências | Logs podem ser insuficientes ou sensíveis. | Definir coleta segura de logs, sem armazenar texto completo se não necessário. | Média |
| Comunicação | Não há fluxo com DPO/ANPD/titulares. | Definir responsáveis, prazos internos e critérios de comunicação. | Alta |
| Pós-incidente | Não há procedimento. | Criar análise de causa raiz, plano de correção, registro e teste de regressão. | Média |
| Fornecedor TTS | Não há contato/contrato mapeado. | Registrar canal de suporte/privacidade do fornecedor e cláusulas de incidente. | Alta |

## 11. Ações Técnicas Recomendadas por Ordem

1. Implementar hash de senha, migrar credenciais e forçar redefinição das senhas atuais.
2. Remover qualquer credencial real do repositório e rotacionar segredos já compartilhados, especialmente os relacionados a `VPS - Acesso.md`.
3. Configurar CORS restrito, headers de segurança e política de cookies por ambiente.
4. Ativar auditoria efetiva para acessos e alterações de dados sensíveis.
5. Revisar todas as rotas e aplicar `roles_required` e validação de vínculo assistencial onde faltar.
6. Criar job/rotina de retenção e descarte para MySQL, Redis, logs e backups.
7. Criar script de anonimização/pseudonimização para bases de desenvolvimento e homologação.
8. Reduzir exposição no painel público e no TTS usando senha/código de chamada ou dado minimizado.
9. Formalizar fornecedores e integrações com SPData, BioData/SQL Server, hospedagem/VPS, backup e TTS.
10. Completar ROPA e RIPD com aprovação jurídica, DPO, segurança e direção clínica.

## 12. Checklist de Aceite para Considerar a Exigência Atendida

| Exigência | Critério de aceite |
|---|---|
| Inventário de Dados | Matriz aprovada com campos, titulares, finalidade, origem, armazenamento, acesso, retenção e compartilhamento. |
| ROPA | Registro aprovado por operação com base legal, operadores, transferência, segurança e retenção. |
| RIPD | Relatório aprovado com riscos, medidas, risco residual, responsáveis e plano de ação. |
| Política de IA | Documento aprovado com escopo, proibições, permissões, governança, transparência e revisão periódica. |
| Compartilhamento de Bases | Procedimento aprovado e contratos/DPA registrados para integrações e terceiros. |
| Anonimização/Pseudonimização | Script/processo testado, documentado e obrigatório para dev/teste. |
| Controle de Acesso | Hash de senha, MFA avaliado, roles revisados, auditoria ativa e revisão periódica de usuários. |
| Retenção/Descarte Dev | Prazos definidos, automação criada, evidência de descarte e backup criptografado. |
| Resposta a Incidentes IA | Playbook aprovado, contatos definidos, toggle de TTS, logging seguro e teste de simulação. |
