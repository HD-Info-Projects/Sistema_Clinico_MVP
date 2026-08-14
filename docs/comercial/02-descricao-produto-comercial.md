# MedSystem — Sistema Clínico

**Documento Comercial — Descrição do Produto**

_Data do documento: agosto de 2026_

---

## 1. Visão geral do produto

O **MedSystem** é uma plataforma web para gestão clínica e prontuário
eletrônico, projetada para clínicas que utilizam o sistema **SPDATA** como
sistema de origem. Ele opera em camadas:

- **Frontend** — aplicação web moderna (Nuxt/Vue) com telas dedicadas para
  médico, recepção e painel de chamada em TV;
- **Backend** — API própria (Flask/Python) que concentra as regras de
  negócio, autenticação, sincronização e integrações;
- **Integrações** — SPDATA (Firebird) e BioData (SQL Server), com
  sincronização de dados e consulta de histórico legado;
- **Banco local** — banco de dados próprio (MySQL) com espelhos dos dados do
  SPDATA e os dados clínicos gerados no dia a dia.

A arquitetura foi desenhada para **não substituir o SPDATA**, mas sim
adicionar sobre ele uma camada digital de operação e prontuário, com
sincronização dos dados essenciais.

---

## 2. Módulos e funcionalidades

### 2.1 Autenticação, perfis e unidades

**Descrição.** O acesso ao sistema é protegido por autenticação com token
(JWT) e os usuários possuem perfis que definem o que podem ver e fazer:
**médico**, **recepção** e **administrador**. Cada usuário pode estar
vinculado a uma ou mais unidades/clínicas, e o sistema permite alternar a
unidade ativa.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Login seguro | Autenticação por e-mail e senha com geração de token JWT e expiração configurável. |
| Proteção contra força bruta | Limitação de tentativas de login por IP e por e-mail (via Redis). |
| Perfis de acesso | Controle de permissões por rota: médico, recepção e admin. |
| Cadastro de médicos | Administrador cadastra médicos buscando o profissional no SPDATA (por CPF/CNPJ ou nome), com vínculo automático de CRM e especialidade. |
| Cadastro de recepção e admin | Comandos administrativos para criação de usuários de recepção e administrador. |
| Múltiplas unidades | Cadastro de unidades com código de centro de custo e código de agenda no SPDATA; vínculo de usuários a unidades; seleção de clínica no login. |
| Controle de acesso por unidade | Cada usuário acessa somente as unidades às quais está vinculado; os dados (agenda, atendimentos) são filtrados pela unidade ativa. |

**Benefícios.** Acesso controlado por perfil e por unidade, cadastro de
médicos aproveitando dados já existentes no SPDATA (sem redigitação) e
proteção do login contra tentativas repetidas.

---

### 2.2 Agenda médica

**Descrição.** A agenda do médico é alimentada automaticamente pela agenda do
SPDATA. Ao consultar um período, o sistema sincroniza os agendamentos e os
atendimentos do SPDATA para o espelho local e apresenta o dia de trabalho
completo: horário, paciente, convênio, especialidade e status.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Sincronização de agenda | Leitura da agenda do SPDATA (tabela `REPACAGD`) por período e por unidade, com criação/atualização do espelho local. |
| Sincronização de atendimentos | Leitura dos atendimentos do SPDATA (`ATCABECATEND`) do médico, por período. |
| Visão do dia | Lista de atendimentos com horário, paciente (nome, CPF, prontuário, convênio, contato), médico, especialidade e status. |
| Filtros e busca | Filtro por data/período, status e busca por nome do paciente. |
| Controle de status | Mudança de status do atendimento: agendado → em espera → em atendimento → atendido; além de **faltou** e **cancelado** (com regras de segurança). |
| Desfazer falta | Devolução de um paciente marcado como falta para a fila de espera. |
| Cancelamento seguro | Apenas atendimentos em andamento podem ser cancelados e devolvidos à fila. |

**Benefícios.** O médico abre o sistema e vê exatamente o dia que o SPDATA já
tinha agendado, sem digitar nada; a atualização de status mantém a clínica
informada sobre o andamento da agenda em tempo real.

---

### 2.3 Painel de chamada (TV) e fila de espera

**Descrição.** O MedSystem inclui um painel de chamada projetado para
exibição em TV na sala de espera. A partir do dashboard do médico, o
profissional chama o paciente para a sua sala; o painel exibe a chamada em
tempo real e anuncia o nome do paciente por voz.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Fila em tempo real | Atualização automática via SSE (Server-Sent Events) da fila de pacientes e do chamado ativo. |
| Chamada do paciente | Ação "chamar paciente" registra o chamado com nome, sala de atendimento e médico responsável. |
| Painel em TV | Tela pública por unidade (URL dedicada), com exibição do chamado atual e histórico de chamadas. |
| Chamada por voz | Síntese de voz em português do Brasil ("[Nome do paciente], por favor dirija-se à [sala]") usando vozes neurais (edge-tts). |
| Salas de atendimento | O médico informa a sala onde está atendendo; a chamada direciona o paciente para a sala correta. |
| Privacidade no painel | A tela pública não exibe dados sensíveis do paciente (apenas nome). |
| Histórico de chamadas | Lista das últimas chamadas realizadas na unidade. |

**Benefícios.** Redução do ruído na recepção, pacientes mais orientados sobre
para onde ir e fluxo de atendimento mais fluido entre a sala de espera e o
consultório.

> **Observação técnica:** os chamados ativos são mantidos em memória no
> servidor do frontend (histórico limitado). A solução atende ao uso
> operacional contínuo, mas os chamados não são persistidos em banco.

---

### 2.4 Recepção e check-in

**Descrição.** A tela da recepção consolida, para o dia selecionado, todos os
pacientes agendados **e** os atendimentos já iniciados no SPDATA, unificando
as duas fontes em uma única visão operacional. A recepção acompanha o
andamento do dia, filtra por médico, especialidade, convênio e status, e
busca pacientes por nome, CPF ou prontuário.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Visão consolidada do dia | Mescla agendamentos do SPDATA com atendimentos reais do dia (evitando duplicidade por registro ou CPF+horário). |
| Resumo do dia | Contadores de agendados, em espera, em atendimento, atendidos e faltas. |
| Filtros | Por médico, especialidade, status e busca livre (nome, CPF, prontuário, registro). |
| Painel de médicos do dia | Lista de médicos com especialidade e quantidade de pacientes. |
| Paginação | Navegação por páginas com até 100 itens por página. |
| Identificação de origem | Cada item indica se o status vem do MedSystem ou do SPDATA. |

**Benefícios.** A recepção enxerga o dia completo em uma tela, sem abrir dois
sistemas; a busca rápida reduz o tempo de localização do paciente; e o
resumo do dia permite uma reação imediata a gargalos (muita gente em espera,
atrasos, faltas).

---

### 2.5 Controle de no-show (faltas)

**Descrição.** O módulo de no-show identifica pacientes que não compareceram
às consultas e transforma a falta em informação gerenciável: com registro de
motivo, relatórios e gráficos. A recepção consegue medir a dimensão das
ausências e entender os padrões.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Identificação automática | Pacientes marcados como falta pelo médico (`faltou`) ou que não compareceram após o horário da consulta (`não confirmado`). |
| Registro de motivo | Motivos padronizados: **esquecimento**, **transporte** e **outros**. |
| Relatórios por período | Lista de faltas com filtros por médico, especialidade, convênio, status e período (mês a mês). |
| Gráficos | Distribuição de faltas por mês, por especialidade e por dia da semana. |
| Resumo gerencial | Totais de faltas, não confirmados e recuperáveis. |
| Filtros de opções | Listas dinâmicas de médicos, especialidades, convênios e anos disponíveis nos dados. |

**Benefícios.** A clínica passa a conhecer o tamanho real das ausências, os
motivos relatados e os dias/especialidades mais afetados — base para ações de
confirmação de consultas, lembretes e ajuste de agenda.

---

### 2.6 Retenção de exames

**Descrição.** O módulo de retenção de exames acompanha o que o médico
solicitou e verifica se o paciente realizou o exame no SPDATA. É a base para
a recepção atuar ativamente na conversão de solicitações em exames
realizados — um ponto direto de recuperação de faturamento e de melhoria do
desfecho clínico.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Solicitações locais | Lista de exames solicitados no prontuário, com data, paciente, convênio, médico e código do exame. |
| Cruzamento com realização | Consulta ao SPDATA para identificar se o exame solicitado foi lançado como realizado (por código, nome, paciente, CPF ou prontuário). |
| Status do exame | **Pendente** (não realizado), **Realizado** e **Não convertido** (após 90 dias sem realização). |
| Dias em aberto | Quantidade de dias entre a solicitação e hoje — priorização visual do acompanhamento. |
| Valor estimado | Valor estimado do exame conforme tabela do convênio no SPDATA (quando disponível). |
| Informações de contato | Telefone/celular do paciente para a recepção realizar o contato de retenção. |
| Indicadores | Conversão por médico, exames mais solicitados, oportunidades financeiras e análise por especialidade (gráficos). |

**Benefícios.** A clínica deixa de "solicitar e esquecer": passa a
acompanhar cada exame solicitado, priorizar os mais antigos em aberto e
visualizar o valor estimado que está deixando de ser faturado.

> **Observação técnica:** o módulo cruza dados locais com o que hoje é
> identificável no SPDATA. Dados como laudo/resultado, agendamento interno
> do exame e valores reais faturados dependem de fontes que ainda precisam
> ser mapeadas no SPDATA — ver seção 6 (Limitações).

---

### 2.7 Atendimento médico e prontuário eletrônico

**Descrição.** É o núcleo clínico do sistema. A partir da agenda, o médico
inicia o atendimento e registra todo o conteúdo da consulta em uma interface
organizada em etapas: anamnese e evolução, solicitação de exames, receita e
conclusão. O atendimento fica registrado, versionado e rastreável.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Início de atendimento | Marca o paciente como "em atendimento" e abre o prontuário com cronômetro de duração. |
| Anamnese | Texto livre com editor rico, com aplicação de modelos/padrões de anamnese. |
| Evolução médica | Registro da evolução com **versionamento automático** — cada alteração preserva a versão anterior (com autor e motivo da alteração quando aplicável). |
| Busca CID-10 | Busca por código ou descrição na tabela CID-10 do SPDATA, com cache para agilidade. |
| Diagnósticos | Seleção de CID principal e secundários, com descrição da doença. |
| Prescrição | Registro de medicamentos com nome, dosagem e orientações; modelos de receita e receita especial (com impressão). |
| Solicitação de exames | Seleção de exames do catálogo (sincronizado do SPDATA) com descrição, justificativa e orientações; impressão da solicitação. |
| Documentos médicos | **Atestado** (com dias de afastamento), **encaminhamento** (para especialista/profissional) e **solicitação de procedimento** (com procedimentos da tabela local). |
| Guia TISS | Geração da guia TISS para impressão, com dados do convênio, exames, procedimentos e logo do convênio. |
| Modelos/padrões por médico | Modelos de anamnese, receita, solicitação de exames e orientações de exame — cada médico cria e usa os seus. |
| Edição de atendimentos | Reabertura de atendimentos finalizados no mesmo dia para correção; documentos de atendimentos passados podem ser impressos, mas não alterados. |
| Rascunho automático | O conteúdo digitado é salvo automaticamente, reduzindo perda de dados. |
| Desfazer falta / cancelar | Fluxos de devolução à fila e cancelamento com regras de segurança. |

**Benefícios.** Atendimento estruturado e ágil, redução do retrabalho de
digitação (modelos e catálogos), rastreabilidade completa da evolução médica
e geração de documentos oficiais em poucos cliques.

---

### 2.8 Histórico do paciente

**Descrição.** Ao iniciar um atendimento, o médico pode consultar o histórico
clínico do paciente de duas origens: os atendimentos já finalizados no
próprio MedSystem e o histórico legado do BioData.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Histórico local | Atendimentos finalizados no MedSystem com anamnese, CIDs, medicamentos e exames solicitados. |
| Histórico BioData | Consulta ao histórico antigo de anamneses no SQL Server (BioData), com conversão automática do conteúdo RTF para texto legível. |
| Controle de acesso | A consulta ao histórico só ocorre para pacientes vinculados ao médico e à unidade ativa (autorização em múltiplas camadas). |
| Busca por CPF ou nome | O BioData é consultado por CPF e, em segundo plano, por nome quando necessário. |

**Benefícios.** O médico começa a consulta com contexto clínico, evitando
perguntas repetidas ao paciente e melhorando a continuidade do cuidado.

---

### 2.9 Dashboard do médico

**Descrição.** A tela inicial do médico apresenta o resumo do dia e a fila
de espera, com ações rápidas de atendimento.

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Resumo do dia | Totais de pacientes, fila, em atendimento, atendidos e faltas. |
| Tempo médio de espera | Cálculo do tempo médio de espera da fila atual. |
| Fila de espera | Lista ordenada por status e horário, com ações: chamar, atender, marcar falta, desfazer falta e editar atendimento. |
| Ação "chamar" | Integração direta com o painel de chamada e a voz. |
| Ação "atender" | Navegação direta para o prontuário do paciente. |

**Benefícios.** O médico gerencia o próprio fluxo de atendimento na tela
inicial, sem depender de terceiros para chamar o próximo paciente.

---

### 2.10 Integrações e sincronização

**Descrição.** O MedSystem conversa com os sistemas legados da clínica de
forma estruturada, mantendo espelhos locais e consultas diretas.

**SPDATA (Firebird):**

| Dado | Origem no SPDATA | Uso no MedSystem |
|------|------------------|------------------|
| Agenda | `REPACAGD` | Agenda médica, recepção, no-show. |
| Atendimentos | `ATCABECATEND` | Agenda médica, recepção, dashboard. |
| Pacientes | `RICADPAC` | Dados do paciente (nome, CPF, prontuário, contato). |
| Médicos | `TBPROFIS`, `TBCBOPRO`, `TBMEDESP` | Cadastro de médico e CRM, especialidades. |
| Convênios | `TBCONVEN` | Nome do convênio nos atendimentos. |
| Especialidades | `TBESPEC` | Especialidades de agenda e médicos. |
| Exames/Procedimentos | `SITABPRO` | Catálogo de exames e procedimentos para solicitação. |
| CID-10 | `TBCID10` | Busca de diagnósticos no prontuário. |
| Logos TISS | `TBTISS` | Exportação das logos dos convênios para guias e documentos. |

**BioData (SQL Server):** consulta ao histórico de anamneses antigas
(`tblAnamnese`, `tblCliente`, `tblProfissional`), com conversão de RTF para
texto.

**Comandos de importação (admin):**

| Comando | Finalidade |
|---------|------------|
| Importar convênios | Espelha os convênios do SPDATA no banco local. |
| Importar especialidades | Espelha as especialidades do SPDATA. |
| Importar exames | Espelha o catálogo de exames do SPDATA. |
| Importar procedimentos | Espelha o catálogo de procedimentos. |
| Exportar logos TISS | Extrai as logos dos convênios do SPDATA para uso nos documentos. |
| Registrar médico | Cria o usuário médico vinculado ao profissional do SPDATA. |

**Benefícios.** Sem digitação dupla: os dados que já existem no SPDATA fluem
para o MedSystem; e o prontuário local não "briga" com o sistema de origem —
cada um faz o seu papel.

---

### 2.11 Administração e operação

**Funcionalidades implementadas:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Cadastro de unidades | Criação de unidades com código de centro de custo e código de agenda SPDATA. |
| Vínculo de usuários a unidades | Associação de usuários às unidades com unidade principal. |
| Comandos CLI | Automação de cadastros e importações via linha de comando (Flask CLI). |
| Migrações de banco | Versionamento do banco de dados (Alembic/Flask-Migrate), aplicado automaticamente no deploy. |

---

## 3. Segurança e rastreabilidade

O que está implementado no MedSystem:

| Mecanismo | Detalhe |
|-----------|---------|
| Autenticação | Tokens JWT com expiração configurável; sessão mantida via cookie seguro (HTTPS). |
| Autorização por perfil | Restrições por rota para médico, recepção e admin (retorno 403 para acesso indevido). |
| Autorização por unidade | Usuário acessa somente as unidades vinculadas; dados filtrados pela unidade ativa. |
| Propriedade do atendimento | O médico só altera atendimentos de seu próprio CRM e da unidade selecionada. |
| Proteção de login | Rate limiting por IP e por e-mail (Redis). |
| Versionamento clínico | Evoluções médicas preservam versões anteriores (com autor e data). |
| Modelos de dados de auditoria | Estrutura de auditoria, fila de sincronização e logs de integração existem no banco. |

> **Importante:** os modelos de auditoria, fila de sincronização e logs de
> integração estão criados no banco, mas **ainda não estão totalmente
> conectados ao fluxo operacional** (nenhum código encontrado grava neles de
> forma ativa). A documentação não afirma conformidade com LGPD, HIPAA ou
> qualquer certificação — apenas descreve os mecanismos presentes na
> arquitetura.

---

## 4. Diferenciais competitivos

Com base nas funcionalidades implementadas, os diferenciais do MedSystem são:

1. **Integração nativa com SPDATA** — a agenda e os atendimentos já
   existentes entram no sistema sem digitação manual, e os catálogos
   (exames, procedimentos, convênios, especialidades) são espelhados
   automaticamente.
2. **Painel de chamada com voz em português** — a TV chama o paciente pelo
   nome e indica a sala, com síntese de voz neural e atualização em tempo
   real.
3. **Retenção de exames com cruzamento real** — a recepção vê exames
   solicitados, confere se foram realizados no SPDATA e prioriza os que
   estão há mais tempo em aberto, com valor estimado.
4. **No-show tratado como dado gerencial** — faltas com motivo, tendência por
   mês, por especialidade e por dia da semana.
5. **Prontuário com versionamento de evolução médica** — cada alteração fica
   preservada, com rastreabilidade de quem e quando alterou.
6. **Acesso ao histórico legado (BioData)** — o médico consulta anamneses
   antigas de outro sistema dentro do prontuário atual.
7. **Múltiplas unidades em uma conta** — o mesmo usuário opera em várias
   clínicas com troca rápida e filtragem correta dos dados.
8. **Deploy simples e seguro** — containers Docker com HTTPS automático e
   deploy documentado para VPS.

---

## 5. Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Frontend | Nuxt (Vue 3), @nuxt/ui, Pinia, Chart.js, pdfmake, SSE. |
| Backend | Flask (Python), SQLAlchemy, Flask-JWT-Extended, Flask-Limiter, Gunicorn. |
| Banco de dados | MySQL 8.4 (local), Firebird (SPDATA), SQL Server (BioData). |
| Cache e rate limiting | Redis 7. |
| Síntese de voz | edge-tts (vozes neurais em português do Brasil). |
| Proxy reverso / HTTPS | Caddy. |
| Infraestrutura | Docker Compose, healthchecks, deploy em VPS. |

---

## 6. Limitações e pontos de evolução identificados

Por transparência, esta seção descreve o que **ainda não está implementado**
ou está **parcial**:

| Item | Situação |
|------|----------|
| Rota genérica `/spdata/` | **Não implementada** (resposta 501). A integração com o SPDATA ocorre por serviços e comandos específicos, não por essa rota. |
| Auditoria ativa | Modelo de dados criado, porém sem código que grave registros no fluxo atual (função de auditoria no login é vazia). |
| Fila de sincronização e logs de integração | Modelos de dados criados, porém sem consumidores identificados no código em produção. |
| Retenção de exames — laudo/resultado | Sem fonte mapeada no SPDATA (necessita identificação das tabelas de pedido, agendamento, execução e laudo). |
| Retenção de exames — valor real faturado | Valor estimado é buscado quando disponível; valor realizado/faturado ainda não tem fonte mapeada. |
| Retenção de exames — guia/autorização e histórico de contato | Sem fonte mapeada. |
| Persistência do painel de chamada | Chamados são mantidos em memória (não persistidos em banco). |
| Cache de dashboard | Código de cache Redis presente, porém comentado na rota de dashboard. |

---

## 7. Conclusão

O MedSystem é um sistema clínico que **integra o que a clínica já tem** com o
que ela precisa para operar melhor: prontuário eletrônico ágil, recepção com
visão completa do dia, controle de faltas, acompanhamento de exames e um
painel de chamada moderno. Suas decisões de arquitetura — integração nativa
com SPDATA, espelhos locais e deploy containerizado — reduzem o atrito de
adoção e os custos de infraestrutura, enquanto os módulos de no-show e
retenção de exames endereçam diretamente dois pontos de perda de receita das
clínicas.

---

_Continue lendo: [Público-alvo e personas](./03-publico-alvo-personas.md)_
