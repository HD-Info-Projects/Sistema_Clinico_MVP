# Plano de Implementação LGPD e Segurança

**Sistema:** Sistema Clínico MVP  
**Data de referência:** 17 de agosto de 2026  
**Status:** Plano técnico-operacional para execução  
**Classificação:** Uso interno  

> Este plano não substitui validação jurídica, regulatória, assistencial ou do Encarregado/DPO. Ele organiza as ações técnicas necessárias para reduzir risco, gerar evidências e sustentar a validação de conformidade LGPD.

## 1. Objetivo

Implementar os controles técnicos e operacionais que ainda faltam para reduzir o risco no tratamento de dados pessoais sensíveis de saúde, especialmente em autenticação, autorização, auditoria, retenção, anonimização, painel público, TTS, logs e governança documental.

## 2. Escopo

Este plano cobre:

| Área | Incluído |
|---|---|
| Backend Flask | Autenticação, autorização, auditoria, retenção, rotas sensíveis, integrações, logs. |
| Frontend Nuxt | Cookies, proxy server-side, painel público, TTS, rascunhos clínicos, rotas por perfil. |
| Banco MySQL | Usuários, dados clínicos, auditoria, logs de integração, fila de sincronização, espelhos SPData. |
| Redis | Rate limit, blocklist JWT, cache técnico, TTL. |
| Infra Docker/Caddy | HTTPS, headers, logs Docker, backup criptografado, restore, hardening. |
| Operação LGPD | Evidências, aprovações, playbooks, ROPA, RIPD, política de IA/TTS. |

Fora do escopo deste plano:

| Área | Observação |
|---|---|
| Parecer jurídico definitivo | Deve ser emitido pelo jurídico/DPO. |
| Descarte automático de prontuário | Não deve ser implementado sem validação jurídica, regulatória e assistencial específica. |
| Contratos com fornecedores | Este plano indica necessidade, mas a formalização é institucional. |

## 3. Situação Técnica Atual Resumida

| Controle | Situação atual | Referência |
|---|---|---|
| Hash de senha nova | Implementado. | `backend/src/models/usuario_model.py`, `backend/src/security/passwords.py` |
| Senha legada | Ainda aceita temporariamente no login para migrar. | `backend/src/security/passwords.py`, `backend/src/controllers/login_controller.py` |
| Rate limit login | Implementado por IP e e-mail. | `backend/src/routes/login_route.py` |
| Revogação JWT no logout | Implementada via blocklist Redis/memória. | `backend/src/security/jwt_blocklist.py` |
| Usuário ativo/bloqueado | Validado no `roles_required`, mas não em toda rota com apenas `jwt_required`. | `backend/src/security/decorators.py` |
| Auditoria | Existe e cobre parte dos eventos. | `backend/src/services/auditoria_service.py` |
| Retenção LGPD | Comando com dry-run, hash de plano e lista fechada. | `backend/src/services/lgpd_retencao_service.py` |
| Backup criptografado | Scripts com `age`, checksum e restore controlado. | `scripts/backup_mysql_encrypted.sh`, `scripts/restore_mysql_encrypted.sh` |
| Painel público | Minimiza para primeiro nome e remove `pacienteId`, mas segue público por unidade. | `frontend/server/utils/chamadas.ts` |
| TTS | Desabilitado por padrão e filtra CPF/CID/termos clínicos. | `backend/src/routes/tts_route.py` |
| Anonimização dev/teste | Não encontrada rotina formal. | Lacuna técnica |

## 4. Priorização Executiva

| Prioridade | Frente | Resultado esperado |
|---|---|---|
| P0 | Senhas legadas, sessão e bloqueio | Eliminar senha em texto puro e impedir acesso de conta bloqueada em qualquer endpoint. |
| P0 | Autorização e menor privilégio | Toda rota autenticada valida usuário ativo, role e unidade/vínculo quando aplicável. |
| P0 | Auditoria de dados sensíveis | Toda visualização/alteração sensível deixa trilha auditável sem conteúdo clínico indevido. |
| P1 | Anonimização dev/teste | Nenhum ambiente não produtivo usa dados reais sem mascaramento aprovado. |
| P1 | Painel público e TTS | Reduzir exposição pública e registrar governança do fornecedor/uso. |
| P1 | Backup/retenção operacional | Backup, restore e dry-run executados com evidência e aprovação. |
| P2 | Hardening adicional | Logs sanitizados, CSRF avaliado, CSP melhorado, TLS de integrações validado. |
| P2 | Documentação formal | ROPA, RIPD, política IA/TTS e resposta a incidentes aprovados. |

## 5. Fase 0 - Preparação e Linha de Base

### Tarefas

| ID | Tarefa | Arquivos/Comandos | Responsável sugerido |
|---|---|---|---|
| F0.1 | Criar branch ou janela de mudança para LGPD/security. | Git/repositório | TI |
| F0.2 | Rodar testes atuais e registrar resultado. | `pytest`, `pnpm lint`, `pnpm typecheck` | TI |
| F0.3 | Gerar inventário de rotas Flask e endpoints Nuxt. | `backend/src/routes/**/*.py`, `frontend/server/api/**/*.ts` | TI |
| F0.4 | Confirmar que `.env` real não está versionado. | `git ls-files -- .env backend/.env` | TI |
| F0.5 | Validar variáveis de produção obrigatórias. | `.env.example`, `docker-compose.yml` | TI |

### Critérios de aceite

| Critério | Evidência |
|---|---|
| Linha de base conhecida | Resultado dos testes e lista de rotas anexados à mudança. |
| Nenhum segredo real versionado | Saída do Git demonstrando `.env` ignorado/não rastreado. |
| Escopo validado | Plano aprovado por TI e revisado por DPO/jurídico para priorização. |

## 6. Fase 1 - Autenticação, Senhas e Sessão

### Objetivo

Eliminar senha legada em texto puro, endurecer login e garantir que bloqueio/desativação de conta invalide acesso efetivamente.

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F1.1 | Criar comando para listar usuários com senha legada não-hasheada. | `backend/src/commands/usuarios_commands.py`, `backend/src/security/passwords.py` | P0 |
| F1.2 | Criar comando para forçar troca de senha ou reset controlado. | `backend/src/commands/usuarios_commands.py` | P0 |
| F1.3 | Adicionar campos de segurança de conta. | Nova migration, `backend/src/models/usuario_model.py` | P0 |
| F1.4 | Registrar tentativas de login falhas por usuário/e-mail. | `backend/src/routes/login_route.py`, `backend/src/controllers/login_controller.py` | P0 |
| F1.5 | Bloquear conta após limite configurável de falhas. | `backend/src/controllers/login_controller.py`, `backend/src/settings/config.py` | P0 |
| F1.6 | Remover fallback que aceita senha em texto puro após migração. | `backend/src/security/passwords.py`, testes | P0 |
| F1.7 | Aumentar política mínima de senha para produção. | `.env.example`, `backend/src/settings/config.py` | P1 |
| F1.8 | Avaliar MFA para `admin`, `dpo`, `ti`. | Nova decisão técnica | P2 |

### Campos sugeridos

| Campo | Tipo | Finalidade |
|---|---|---|
| `senha_alterada_em` | DateTime | Evidenciar rotação/troca. |
| `forcar_troca_senha` | Boolean | Obrigar reset no próximo login. |
| `tentativas_login_falhas` | Integer | Controle de bloqueio. |
| `ultimo_login_falho_em` | DateTime | Auditoria e desbloqueio. |
| `bloqueio_motivo` | String | Evidência operacional. |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Nenhuma senha em texto puro permanece | Comando administrativo retorna zero senhas legadas. |
| Login não aceita senha legada | Teste automatizado falha quando `stored_password` não é hash. |
| Conta bloqueada não acessa endpoints | Testes em rotas com role e rotas só autenticadas. |
| Falha de login é auditada sem vazar senha | Tabela `auditorias` contém evento sem payload sensível. |

## 7. Fase 2 - Autorização, Usuário Ativo e Unidade

### Objetivo

Aplicar menor privilégio em todas as rotas e impedir acesso com JWT válido quando usuário estiver inativo, bloqueado ou sem unidade/vínculo assistencial.

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F2.1 | Criar decorator base para rota autenticada com usuário ativo. | `backend/src/security/decorators.py` | P0 |
| F2.2 | Revisar rotas com `@jwt_required()` sem `roles_required`. | `backend/src/routes/**/*.py` | P0 |
| F2.3 | Aplicar role apropriada a catálogos e unidades. | `procedimentos_route.py`, `unidades_route.py` | P0 |
| F2.4 | Garantir validação de unidade nas rotas de dados de pacientes. | `agenda_medica_route.py`, `check_in_route.py`, `no_show_route.py`, `documentos_medicos_route.py`, `prontuario_route.py` | P0 |
| F2.5 | Formalizar matriz de permissões por perfil. | Novo doc ou seção neste plano | P1 |
| F2.6 | Criar testes para acesso negado por role, usuário bloqueado e unidade errada. | `backend/tests` ou `backend/src/security/test_lgpd_security.py` | P0 |

### Matriz inicial de permissões

| Perfil | Pode acessar | Não deve acessar |
|---|---|---|
| `medico` | Agenda própria, prontuário com vínculo, histórico autorizado, modelos próprios, documentos do atendimento próprio. | Check-in geral, no-show geral, auditoria LGPD global, usuários administrativos. |
| `recepcao` | Check-in, no-show, retenção de exames, chamada de paciente. | Prontuário clínico, histórico BioData, modelos médicos privados. |
| `admin` | Administração de usuários médicos, auditoria conforme regra local. | Prontuário sem necessidade formal. |
| `dpo` | Auditoria e evidências LGPD. | Alteração clínica/assistencial. |
| `ti` | Auditoria técnica e operação LGPD conforme necessidade. | Alteração clínica/assistencial. |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Nenhuma rota autenticada ignora usuário bloqueado | Teste automatizado por rota crítica ou decorator comum. |
| Role incorreta recebe 403 | Testes por perfil. |
| Unidade incorreta recebe 403 | Testes em agenda/check-in/no-show/documentos/prontuário. |
| Médico só vê paciente com vínculo | Testes de histórico local e BioData. |

## 8. Fase 3 - Auditoria LGPD Efetiva

### Objetivo

Registrar os eventos relevantes de tratamento de dados pessoais/sensíveis sem armazenar conteúdo clínico completo, credenciais ou payloads desnecessários.

### Eventos mínimos

| Evento | Ação sugerida | Observação |
|---|---|---|
| Login sucesso/falha/logout | Já existe parcialmente | Manter sem senha. |
| Visualização de agenda | Já existe parcialmente | Registrar filtros agregados. |
| Visualização de check-in/no-show/retenção | Já existe parcialmente | Registrar período e quantidade. |
| Início de atendimento | `INICIOU_ATENDIMENTO` | Ao mudar para `em-atendimento`. |
| Finalização de atendimento | `FINALIZOU_ATENDIMENTO` | Ao salvar conteúdo clínico. |
| Edição de evolução/anamnese | `EDITOU_EVOLUCAO` | Sem texto clínico na descrição. |
| Visualização de prontuário/histórico | Já existe parcialmente | Manter com paciente/entidade e contagem. |
| Consulta BioData | Já existe | Manter sem anamnese no log. |
| Documento médico salvo/listado | Já existe parcialmente | Registrar tipo, não conteúdo. |
| No-show motivo alterado | Criar evento | Registrar motivo categórico. |
| Modelo médico criado/editado/deletado | Criar evento | Pode conter conteúdo clínico livre, não gravar conteúdo. |
| Chamada pública criada/concluída | Criar evento | Registrar unidade e chamado, sem nome completo. |
| TTS solicitado | Criar evento | Registrar `chamadoId`, unidade, IP, status, não texto. |
| Retenção executada | Já existe | Manter evidência agregada. |

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F3.1 | Expandir enum de auditoria para eventos faltantes. | `backend/src/models/auditoria_model.py` | P0 |
| F3.2 | Adicionar auditoria em alteração de status/atendimento. | `backend/src/routes/agenda_medica_route.py`, `backend/src/services/spdata_atendimentos_service.py` | P0 |
| F3.3 | Adicionar auditoria em modelos médicos. | `modelo_solicitacao_*_route.py`, `modelo_orientacao_exame_route.py` | P1 |
| F3.4 | Adicionar auditoria em no-show motivo. | `backend/src/routes/no_show_route.py` | P1 |
| F3.5 | Adicionar auditoria para painel/TTS. | `frontend/server/api/chamadas/*.ts`, `frontend/server/api/tts/speak.post.ts`, `backend/src/routes/tts_route.py` | P1 |
| F3.6 | Criar sanitizador de descrição de auditoria. | `backend/src/services/auditoria_service.py` | P1 |
| F3.7 | Criar testes de auditoria sem dados sensíveis. | Testes backend/frontend server | P1 |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Evento sensível gera auditoria | Testes verificam inserção de `Auditoria`. |
| Auditoria não contém CPF/senha/token/texto clínico | Testes de sanitização. |
| Consulta de auditoria é restrita | Apenas `admin`, `dpo`, `ti`. |

## 9. Fase 4 - Anonimização e Pseudonimização Dev/Teste

### Objetivo

Impedir o uso de dados reais em desenvolvimento/homologação sem anonimização, reduzindo risco de exposição indevida.

### Estratégia recomendada

Criar processo de geração de base dev mascarada a partir de um dump restaurado em ambiente isolado, nunca diretamente em produção.

Fluxo sugerido:

| Etapa | Ação |
|---|---|
| 1 | Restaurar backup criptografado em ambiente isolado sem integrações externas. |
| 2 | Executar script de anonimização no banco restaurado. |
| 3 | Validar ausência de CPF/nome/e-mail/telefone reais por amostragem e consultas. |
| 4 | Gerar novo dump anonimizado para dev/teste. |
| 5 | Destruir ambiente temporário e registrar evidência sem dados pessoais. |

### Regras mínimas de mascaramento

| Campo | Regra |
|---|---|
| Nome paciente | `Paciente 000001`, consistente por paciente. |
| Nome social | `Nome Social 000001` ou nulo. |
| CPF | CPF sintético válido, sem relação com o real. |
| E-mail | `paciente000001@example.test`. |
| Telefone/celular | Número fictício padronizado. |
| Endereço | Valor genérico ou nulo. |
| Prontuário | Identificador sintético. |
| Texto clínico livre | Texto clínico sintético sem referência real. |
| Datas | Deslocamento consistente por paciente, se necessário. |
| Usuários internos | Manter apenas usuários técnicos fictícios; resetar senhas. |

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F4.1 | Criar script de anonimização. | `scripts/anonymize_dev_database.py` ou comando Flask | P1 |
| F4.2 | Definir mapeamento de tabelas/campos. | Modelos em `backend/src/models/**/*.py` | P1 |
| F4.3 | Criar validações automáticas pós-anonimização. | Script/testes | P1 |
| F4.4 | Documentar procedimento operacional. | `docs/` | P1 |
| F4.5 | Atualizar `.env.example`/docs para proibir dados reais em dev. | `.env.example`, `docs/` | P1 |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Dev não contém dados reais | Script de validação e amostragem formal. |
| Dados sintéticos são consistentes | Mesmo paciente mantém mesmo ID sintético. |
| Processo é repetível | Comando documentado e testado. |

## 10. Fase 5 - Retenção, Descarte e Backup Operacional

### Objetivo

Ativar controles existentes de backup/restore/retenção com governança, aprovação e evidência operacional.

### Tarefas Técnicas e Operacionais

| ID | Tarefa | Arquivos/Comandos | Prioridade |
|---|---|---|---|
| F5.1 | Validar política com Controlador, DPO, jurídico/regulatório e TI. | `docs/politica-retencao-descarte-backup.md` | P1 |
| F5.2 | Configurar destinatário público `age` em produção. | `.env` operacional | P1 |
| F5.3 | Agendar backup diário via cron. | `scripts/backup_mysql_encrypted.sh` | P1 |
| F5.4 | Executar teste de restore em ambiente isolado. | `scripts/restore_mysql_encrypted.sh` | P1 |
| F5.5 | Rodar dry-run de retenção e registrar contagens. | `flask lgpd-retencao --dry-run` | P1 |
| F5.6 | Executar descarte somente com hash, backup, aprovação e legal hold checado. | `flask lgpd-retencao --execute ...` | P1 |
| F5.7 | Criar rotina mensal/trimestral de revisão. | Procedimento operacional | P2 |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Backup diário existe e é criptografado | Arquivo `.sql.gz.age` e `.sha256`. |
| Restore é testado | Evidência trimestral sem dados pessoais. |
| Retenção não apaga tabela clínica | Dry-run e teste de segurança. |
| Execute exige aprovação | Comando aborta sem parâmetros obrigatórios. |

## 11. Fase 6 - Painel Público e TTS

### Objetivo

Reduzir exposição pública de dados pessoais no painel e controlar o uso de TTS/fornecedor externo.

### Decisões necessárias

| Decisão | Opção recomendada |
|---|---|
| Identificador no painel | Usar senha/código de chamada em vez de nome, quando operacionalmente viável. |
| Acesso ao painel | Usar token/pareamento por unidade, não apenas ID público. |
| TTS externo | Manter desativado até validação de fornecedor/DPA/transferência. |
| Aviso ao paciente | Informar chamada por painel/voz no ambiente físico ou política de privacidade. |

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F6.1 | Definir modo de chamada: código/senha, primeiro nome ou híbrido. | Decisão DPO/operação | P1 |
| F6.2 | Criar token de painel por unidade ou pareamento. | `unidades`, `frontend/server/api/sse/tv.get.ts`, `frontend/app/pages/painel-chamada/[id].vue` | P1 |
| F6.3 | Ajustar payload público para não incluir nome quando usado código. | `frontend/server/utils/chamadas.ts`, `frontend/server/utils/sse.ts` | P1 |
| F6.4 | Auditar criação/conclusão de chamado. | `frontend/server/api/chamadas/*.ts` ou backend dedicado | P1 |
| F6.5 | Auditar TTS sem texto completo. | `frontend/server/api/tts/speak.post.ts`, `backend/src/routes/tts_route.py` | P1 |
| F6.6 | Manter toggle operacional `ENABLE_TTS`. | `docker-compose.yml`, `.env.example` | P1 |
| F6.7 | Formalizar fornecedor TTS e transferência internacional. | ROPA/RIPD/política IA | P1 |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Painel não expõe dado além do aprovado | Revisão DPO e teste visual. |
| URL pública não basta para consumir chamadas | Token/pareamento obrigatório. |
| TTS não recebe conteúdo clínico | Testes com CPF, CID, exame, diagnóstico, medicamento. |
| Uso do TTS é auditável | Evento registra status sem texto sensível. |

## 12. Fase 7 - Logs, Headers, CSRF e Hardening

### Objetivo

Evitar vazamento em logs/erros e endurecer perímetro de aplicação/infra.

### Tarefas Técnicas

| ID | Tarefa | Arquivos prováveis | Prioridade |
|---|---|---|---|
| F7.1 | Criar sanitizador de logs para CPF, token, senha e payload clínico. | Backend e frontend server utils | P1 |
| F7.2 | Remover `String(error)` em respostas Nuxt que possam vazar detalhes. | `frontend/server/api/**/*.ts` | P1 |
| F7.3 | Validar CORS restrito em produção. | `.env.example`, `backend/src/__init__.py` | P1 |
| F7.4 | Avaliar CSRF para rotas Nuxt com cookie. | `frontend/server/api/**/*.ts` | P2 |
| F7.5 | Reduzir `unsafe-inline` na CSP se viável. | `Caddyfile`, Nuxt build | P2 |
| F7.6 | Validar certificado SQL Server em produção. | `SQLSERVER_TRUST_CERTIFICATE=no`, infraestrutura | P1 |
| F7.7 | Avaliar Docker secrets/cofre para segredos. | Deploy/infra | P2 |
| F7.8 | Adicionar varredura de secrets/dependências no pipeline. | CI/CD | P2 |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Logs não contêm CPF/senha/token | Testes e revisão de logs. |
| CORS só aceita domínio oficial | Teste com origem não autorizada. |
| Erros ao frontend são genéricos | Revisão de respostas 4xx/5xx. |
| Integrações usam TLS validado quando disponível | Configuração operacional aprovada. |

## 13. Fase 8 - Documentação, Governança e Incidentes

### Objetivo

Completar documentação e aprovações necessárias para responsabilização, prestação de contas e resposta a incidentes.

### Documentos a concluir

| Documento | Conteúdo mínimo | Responsável sugerido |
|---|---|---|
| Inventário de dados campo a campo | Campo, finalidade, sensibilidade, origem, armazenamento, acesso, retenção. | TI + DPO |
| ROPA | Operações, base legal, titulares, operadores, transferência, medidas técnicas. | DPO + jurídico |
| RIPD | Riscos, medidas, risco residual, plano de tratamento, aprovação. | DPO + segurança + jurídico |
| Política IA/TTS | Finalidade, fornecedor, dados enviados, proibições, incidentes, revisão. | DPO + TI |
| Compartilhamento de bases | SPData, BioData, hospedagem, backup, TTS, Redis. | Jurídico + TI |
| Incidentes | Detecção, classificação, contenção, evidências, comunicação, pós-incidente. | DPO + TI + segurança |
| Revisão de acessos | Periodicidade, responsáveis, evidência, desligamento/bloqueio. | TI + gestão |

### Critérios de aceite

| Critério | Como validar |
|---|---|
| Documentos aprovados | Registro de aprovação preenchido. |
| Responsáveis nomeados | Matriz RACI ou equivalente. |
| Playbook testado | Simulação de incidente TTS/painel/log. |
| Revisão periódica definida | Agenda mensal/trimestral registrada. |

## 14. Ordem Recomendada de Execução

| Sprint/Onda | Itens | Resultado |
|---|---|---|
| Onda 1 | F1 + F2 | Acesso seguro: senha, sessão, bloqueio, roles e unidade. |
| Onda 2 | F3 | Trilha de auditoria suficiente para dados sensíveis. |
| Onda 3 | F5 | Backup/retenção operacional com evidências. |
| Onda 4 | F4 | Dev/teste sem dados reais identificáveis. |
| Onda 5 | F6 | Painel/TTS minimizados e governados. |
| Onda 6 | F7 + F8 | Hardening e fechamento documental. |

## 15. Backlog Técnico Inicial

| ID | Entrega | Prioridade | Dependência |
|---|---|---|---|
| B1 | Comando `usuarios-senhas-legadas` e relatório sem expor senha. | P0 | Nenhuma |
| B2 | Migration de campos de segurança de conta. | P0 | Nenhuma |
| B3 | Bloqueio por falhas de login e reset por admin. | P0 | B2 |
| B4 | Remoção de fallback de senha texto puro. | P0 | B1, reset de usuários |
| B5 | Decorator de autenticação ativa para rotas sem role. | P0 | Nenhuma |
| B6 | Revisão de `procedimentos`, `unidades/minhas`, `login/me`, `logout`. | P0 | B5 |
| B7 | Auditoria de status de atendimento/finalização. | P0 | Nenhuma |
| B8 | Auditoria de modelos médicos/no-show/TTS/painel. | P1 | B7 |
| B9 | Script de anonimização dev/teste. | P1 | Mapeamento de campos |
| B10 | Token/pareamento de painel público. | P1 | Decisão DPO/operação |
| B11 | Sanitização de logs frontend/backend. | P1 | Nenhuma |
| B12 | Teste de restore e dry-run LGPD documentado. | P1 | Ambiente operacional |

## 16. Definition of Done Geral

Uma frente só deve ser considerada concluída quando:

| Requisito | Evidência |
|---|---|
| Código implementado | Pull request ou diff revisado. |
| Testes executados | Resultado anexado. |
| Migração segura | Migration revisada e rollback conhecido. |
| Logs/auditoria sem dados sensíveis | Revisão e testes de sanitização. |
| Documentação atualizada | Documento ou runbook correspondente. |
| Aprovação quando aplicável | DPO/jurídico/gestão conforme risco. |

## 17. Riscos e Cuidados

| Risco | Mitigação |
|---|---|
| Bloquear usuários legítimos ao endurecer login | Implementar desbloqueio admin e comunicação prévia. |
| Perder acesso por remover senha legada antes do reset | Primeiro listar/migrar/resetar, depois remover fallback. |
| Auditoria armazenar dado sensível demais | Sanitizar descrições e não gravar payload clínico completo. |
| Anonimização incompleta | Criar validações automáticas e amostragem formal. |
| Painel público impactar operação | Validar alternativa com recepção/equipe clínica antes de ativar. |
| Restore reintroduzir dado descartado | Registrar decisões de descarte e reaplicar após restore quando necessário. |

## 18. Próximo Passo Recomendado

Iniciar pela Onda 1:

1. Implementar relatório de senhas legadas.
2. Adicionar campos de segurança de conta.
3. Implementar bloqueio por falhas.
4. Aplicar validação de usuário ativo em todas as rotas autenticadas.
5. Criar testes de regressão para usuário bloqueado, role incorreta e unidade incorreta.

Essa onda reduz o maior risco técnico imediato: acesso indevido com credencial fraca, legada, bloqueada ou perfil insuficiente.
