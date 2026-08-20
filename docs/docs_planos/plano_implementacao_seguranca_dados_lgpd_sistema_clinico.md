# Plano de Implementação de Segurança de Dados e LGPD para o Sistema Clínico

## Objetivo

Implementar controles técnicos e operacionais para proteger dados pessoais e dados sensíveis tratados pelo Sistema Clínico, em conformidade com a LGPD e com as diretrizes do documento `Plano de Implementação das Melhorias - Diretoria Médica - Inovação e IA.docx`.

Este plano adapta o documento original para o escopo atual do sistema: segurança de dados, rastreabilidade, minimização, controle de acesso e proteção de bases de desenvolvimento/homologação.

## Escopo

### Incluído

| Tema | Objetivo |
|---|---|
| Autenticação segura | Evitar acesso indevido por credenciais frágeis ou expostas. |
| Controle de acesso | Aplicar menor privilégio por perfil e escopo. |
| Auditoria LGPD | Registrar acessos e operações sensíveis. |
| Minimização | Trafegar e exibir somente dados necessários. |
| Mascaramento | Reduzir exposição visual de dados pessoais. |
| Anonimização/pseudonimização | Proteger bases de teste, homologação e desenvolvimento. |
| Controle de exportação | Restringir downloads, cópias e relatórios sensíveis. |
| Retenção e descarte | Evitar manutenção indefinida de dados temporários. |
| Segurança técnica | Reforçar headers, CORS, secrets, HTTPS e logs. |

### Fora do escopo técnico direto

| Item | Responsável principal |
|---|---|
| NDA | Jurídico |
| Aditivo contratual | Jurídico / DPO |
| Base legal | Jurídico / DPO |
| ROPA | DPO |
| RIPD | DPO |
| Aprovação formal institucional | Diretoria |
| Política institucional de privacidade | DPO / Diretoria |
| Plano jurídico de incidentes | Jurídico / DPO |

## Relação com o documento original

| Pedido do documento | Implementação no sistema |
|---|---|
| Classificar dados pessoais, sensíveis, anonimizados e administrativos | Inventário e classificação LGPD dos dados. |
| Criar ambiente separado de produção | Base de homologação/teste segregada e protegida. |
| Remover dados desnecessários | Minimização de campos nas APIs e telas. |
| Anonimizar ou pseudonimizar dados | Rotina técnica para bases não produtivas. |
| Definir quem terá acesso | Perfis, permissões e validação de escopo. |
| Criar usuário exclusivo para desenvolvimento | Usuários técnicos controlados, expirados e auditados. |
| Implantar autenticação multifator | MFA para perfis sensíveis. |
| Registrar logs de acesso | Auditoria LGPD centralizada. |
| Restringir download da base | Controle de exportação e justificativa. |
| Bloquear compartilhamento externo | Permissões, auditoria e bloqueio de exportação indevida. |
| Criptografar transmissão | HTTPS/TLS e configuração segura. |
| Implantar backup seguro | Política de backup e proteção de volumes. |
| Definir política de retenção | Retenção e descarte de bases temporárias. |
| Auditar acessos periodicamente | Painel LGPD e relatórios de auditoria. |

## Responsabilidades

### Backend

| Responsabilidade | Implementação |
|---|---|
| Autenticação segura | Hash de senha, validação de token e rate limit. |
| Autorização | `jwt_required`, `roles_required` e validação de escopo. |
| Auditoria | Serviço central para registrar eventos sensíveis. |
| Minimização | Serializadores/respostas por contexto. |
| Anonimização | Rotinas server-side para bases de teste/homologação. |
| Exportação | Endpoints controlados, justificativa e logs. |
| Retenção | Rotinas de expiração e descarte. |
| Integrações | Evitar logs com payloads sensíveis de SPDATA/BioData. |

### Frontend

| Responsabilidade | Implementação |
|---|---|
| Experiência por perfil | Menus, rotas e botões condicionados à permissão. |
| Máscaras visuais | CPF, telefone, e-mail e identificadores sensíveis. |
| Painéis administrativos | Auditoria, exportações, inventário e conformidade. |
| Confirmações | Justificativa para exportações e ações sensíveis. |
| Erros de permissão | Tratamento de `401` e `403`. |
| Sanitização | Manter DOMPurify onde houver HTML dinâmico. |

### Infraestrutura

| Responsabilidade | Implementação |
|---|---|
| HTTPS | Caddy com TLS obrigatório em produção. |
| Headers de segurança | HSTS, X-Frame-Options, X-Content-Type-Options e CSP quando aplicável. |
| Secrets | Variáveis de ambiente e rotação periódica. |
| Backup | Volumes protegidos, retenção e restauração testada. |
| Ambientes | Produção, homologação e desenvolvimento separados. |
| Banco | Usuários com menor privilégio e acesso restrito. |

### DPO, Jurídico e Diretoria

| Responsabilidade | Entregável |
|---|---|
| Classificação legal | Base legal e finalidade do tratamento. |
| Documentação LGPD | ROPA, RIPD, políticas e procedimentos. |
| Contratos | NDA, aditivos e termos de responsabilidade. |
| Aprovação | Autorização formal para compartilhamento ou uso de bases. |
| Incidentes | Plano de resposta e comunicação. |

## Fases de implementação

### Fase 1 - Segurança de autenticação

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Substituir senha em texto puro por hash seguro. | Manter login atual com mensagens genéricas. |
| Corrigir validação de senha no login. | Exibir sessão expirada em caso de `401`. |
| Criar compatibilidade controlada para senhas legadas. | Não armazenar token em `localStorage`. |
| Validar `SECRET_KEY` e `JWT_SECRET_KEY` em produção. | Manter cookie HTTP-only. |
| Registrar login, falha de login e logout. | Evitar revelar se e-mail existe. |

Critério de aceite: usuários autenticam com senha hasheada, tentativas são auditadas e credenciais inválidas não vazam informação.

### Fase 2 - Controle de acesso e menor privilégio

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Revisar todos os endpoints com dados sensíveis. | Ajustar menus por perfil. |
| Garantir autenticação e papéis em endpoints críticos. | Criar tela de acesso negado. |
| Validar escopo do acesso, não apenas papel. | Ocultar telas e botões não permitidos. |
| Registrar tentativas negadas. | Tratar `403` com mensagem clara. |

Critério de aceite: dados sensíveis não podem ser acessados por chamada direta sem perfil e escopo adequados.

### Fase 3 - Auditoria LGPD

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Criar serviço central de auditoria. | Criar painel simples de auditoria. |
| Registrar login, falha, acesso negado e consultas sensíveis. | Filtros por ação, usuário, entidade e período. |
| Registrar acessos a prontuário, histórico, agenda, check-in e retenção. | Exibir metadados dos eventos. |
| Evitar salvar conteúdo clínico no log. | Restringir painel a perfis administrativos. |

Critério de aceite: cada acesso sensível informa quem acessou, quando, de onde e qual entidade foi acessada.

### Fase 4 - Inventário e classificação de dados

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Criar cadastro de inventário de dados. | Tela de inventário LGPD. |
| Mapear SPDATA, BioData e banco local. | Listar origem, tabela, campo e finalidade. |
| Classificar dados como administrativo, pessoal ou sensível. | Badges de classificação. |
| Registrar alterações em auditoria. | Histórico de alterações. |

Critério de aceite: cada módulo possui dados mapeados, classificados e vinculados a uma finalidade.

### Fase 5 - Minimização e mascaramento

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Revisar respostas das APIs. | Mascarar CPF, telefone e e-mail em listas. |
| Separar respostas resumidas e detalhadas. | Exibir dado completo apenas onde necessário. |
| Evitar enviar dados clínicos para telas operacionais. | Avisar quando dado for sensível. |

Critério de aceite: listagens e telas operacionais exibem somente dados necessários ao propósito.

### Fase 6 - Controle de exportação

Prioridade: alta.

| Backend | Frontend |
|---|---|
| Criar política e endpoints de exportação controlada. | Botões apenas para perfis autorizados. |
| Exigir justificativa. | Modal de confirmação. |
| Registrar usuário, IP, data, formato e volume. | Histórico de exportações. |
| Bloquear exportação indevida de dados sensíveis. | Informar quando ação for bloqueada. |

Critério de aceite: nenhuma exportação sensível ocorre sem permissão, justificativa e auditoria.

### Fase 7 - Base de homologação e testes

Prioridade: média/alta.

| Backend | Frontend |
|---|---|
| Gerar base segura para homologação. | Solicitação/status da geração, se necessário. |
| Remover campos desnecessários. | Exibir campos protegidos. |
| Anonimizar dados pessoais. | Alertar sobre risco residual. |
| Registrar geração, acesso e descarte. | Histórico da base. |

Critério de aceite: homologação não usa cópia direta da produção com dados reais expostos.

### Fase 8 - Retenção e descarte

Prioridade: média.

| Backend | Frontend |
|---|---|
| Criar política de retenção para dados temporários. | Tela de retenção e descarte. |
| Expirar bases temporárias. | Alertas de vencimento. |
| Registrar descarte em auditoria. | Status ativa, vencida ou descartada. |

Critério de aceite: bases temporárias não permanecem disponíveis indefinidamente.

### Fase 9 - MFA para perfis sensíveis

Prioridade: média.

| Backend | Frontend |
|---|---|
| Implementar segundo fator. | Tela de configuração e validação de MFA. |
| Exigir MFA para `admin`, `dpo` e `ti`. | Segunda etapa após login. |
| Aplicar rate limit. | Mensagens para código inválido/expirado. |
| Auditar sucesso e falha. | Fluxo de recuperação. |

Critério de aceite: perfis administrativos não acessam áreas sensíveis apenas com senha.

### Fase 10 - Segurança técnica e infraestrutura

Prioridade: média/alta.

| Backend | Frontend/Infra |
|---|---|
| Restringir CORS. | HTTPS obrigatório. |
| Evitar dados sensíveis em logs de erro. | Headers de segurança. |
| Validar entradas. | HSTS e CSP quando aplicável. |
| Proteger secrets. | Não expor variáveis sensíveis ao frontend. |

Critério de aceite: configurações de produção reduzem risco de vazamento, interceptação e exposição acidental.

### Fase 11 - Painel LGPD

Prioridade: média.

| Backend | Frontend |
|---|---|
| Endpoints de resumo LGPD. | Dashboard LGPD. |
| Listar acessos sensíveis recentes. | Cards de eventos críticos. |
| Listar exportações. | Histórico de exportações. |
| Listar usuários por perfil. | Visão de permissões. |
| Listar pendências de classificação. | Checklist de conformidade. |

Critério de aceite: administração/DPO acompanham riscos e pendências em uma visão única.

## MVP LGPD

| Entrega | Backend | Frontend |
|---|---|---|
| MVP 1 | Hash de senha, permissões e auditoria básica. | Login ajustado e tela de acesso negado. |
| MVP 2 | Auditoria de prontuário, histórico e exportação. | Painel simples de auditoria. |
| MVP 3 | Minimização nas APIs. | Máscaras em listas e tabelas. |
| MVP 4 | Inventário de dados. | Tela de classificação LGPD. |
| MVP 5 | Controle de exportação. | Justificativa e histórico. |
| MVP 6 | Base anonimizada e retenção. | Tela de bases temporárias. |

## Ordem recomendada

1. Corrigir senha com hash.
2. Revisar permissões e escopo dos endpoints.
3. Criar auditoria central.
4. Registrar acessos sensíveis.
5. Implementar minimização e mascaramento.
6. Criar inventário e classificação de dados.
7. Controlar exportações.
8. Criar rotina de base anonimizada para homologação.
9. Implementar retenção e descarte.
10. Implementar MFA para perfis sensíveis.
11. Criar painel LGPD.

## Checklist de acompanhamento

| Controle | Status inicial |
|---|---|
| Senhas com hash seguro | Pendente |
| Rate limit de login | Existente |
| JWT em cookie HTTP-only no frontend | Existente |
| Perfis por endpoint | Parcial |
| Validação de escopo | Parcial |
| Auditoria central | Pendente |
| Painel de auditoria | Pendente |
| Inventário de dados | Pendente |
| Minimização de APIs | Parcial |
| Mascaramento de dados | Parcial |
| Controle de exportação | Pendente |
| Base de homologação anonimizada | Pendente |
| Retenção/descarte | Pendente |
| MFA | Pendente |
| Headers de segurança | Parcial |

## Prioridade máxima

Para reduzir risco LGPD rapidamente, priorizar:

1. Senha segura.
2. Auditoria real.
3. Controle de acesso por perfil e escopo.
4. Minimização de dados nas APIs e telas.
5. Controle de exportação.
