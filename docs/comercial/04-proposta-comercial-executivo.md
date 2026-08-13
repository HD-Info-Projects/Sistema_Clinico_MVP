# MedSystem — Proposta Comercial Executiva

**Documento Comercial — Resumo executivo para decisores**

_Data do documento: agosto de 2026_

---

## 1. Resumo executivo

O **MedSystem** é um sistema clínico web que digitaliza o prontuário, organiza
a recepção e dá visibilidade gerencial à clínica, **integrado ao SPDATA** —
sem substituir o sistema de origem e sem perder o histórico existente.

Ele resolve, de forma objetiva, três problemas de negócio:

1. **Consultas perdidas (no-show)** — visibilidade das faltas, com motivos e
   tendências;
2. **Exames solicitados e não realizados** — acompanhamento e recuperação de
   exames com valor estimado;
3. **Retrabalho operacional** — agenda sincronizada, prontuário com modelos,
   documentos médicos automáticos e painel de chamada com voz.

---

## 2. Escopo da solução

| Módulo | Entrega |
|--------|---------|
| **Agenda e atendimento** | Agenda sincronizada do SPDATA, fila de espera, status do atendimento, dashboard do médico. |
| **Prontuário eletrônico** | Anamnese, evolução com versionamento, CID-10, prescrição, solicitação de exames, rascunho automático. |
| **Documentos médicos** | Atestado, encaminhamento, solicitação de procedimento e guia TISS com logo do convênio. |
| **Recepção** | Visão consolidada do dia, check-in, filtros, resumo em tempo real, painel de chamada em TV com voz. |
| **Gestão de faltas** | No-show com motivos, relatórios e gráficos por mês, especialidade e dia da semana. |
| **Retenção de exames** | Acompanhamento de exames solicitados, status de realização, dias em aberto, valor estimado e indicadores. |
| **Integrações** | SPDATA (agenda, atendimentos, pacientes, médicos, convênios, especialidades, exames, CID-10, logos TISS) e BioData (histórico de anamneses). |
| **Administração** | Cadastro de unidades e usuários, importações de catálogos, multiunidade com um login. |

---

## 3. Escopo de implantação

1. **Preparação** — levantamento do ambiente (SPDATA/Firebird e BioData/SQL
   Server), definição das unidades, cadastro de administrador;
2. **Importações de dados-base** — convênios, especialidades, exames,
   procedimentos e logos TISS;
3. **Cadastro de usuários** — admin, recepção e médicos (vinculados ao SPDATA);
4. **Operação assistida** — acompanhamento do primeiro mês de uso com ajustes;
5. **Treinamento** — recepção, médicos e administradores.

---

## 4. Entregáveis

| Item | Detalhe |
|------|---------|
| Sistema implantado | Ambiente Docker (frontend, backend, MySQL, Redis, HTTPS) operando com o SPDATA do cliente. |
| Dados-base carregados | Catálogos de convênios, especialidades, exames, procedimentos e logos TISS importados. |
| Usuários ativos | Admin, recepção e médicos cadastrados e treinados. |
| Documentação | Guia de deploy e documentação das tabelas/integrações fornecidos com o sistema. |

---

## 5. Responsabilidades da contratada

- Implantar e configurar o sistema nos ambientes acordados;
- Realizar importações e cadastros iniciais;
- Treinar os usuários;
- Prestar suporte e manutenção conforme contrato;
- Corrigir defeitos identificados no escopo entregue.

---

## 6. Responsabilidades do cliente

- Disponibilizar acesso de rede ao SPDATA (Firebird) e ao BioData (SQL Server)
  com credenciais de leitura;
- Disponibilizar um servidor (VPS ou on-premise) com recursos compatíveis;
- Indicar responsáveis para o cadastro e o treinamento;
- Manter o ambiente de origem estável e acessível durante a implantação.

---

## 7. Premissas

- O SPDATA permanece como **fonte da verdade** para agenda, atendimentos,
  pacientes e catálogos; o MedSystem espelha e consulta esses dados;
- O acesso ao SPDATA/BioData é de **leitura** (com comandos de importação
  executados pela contratada quando necessário);
- Dados de laudo/resultado de exames e valores reais faturados dependem de
  fontes ainda não mapeadas no SPDATA (ver documento de limitações).

---

## 8. Itens fora do escopo

- Migração ou substituição do SPDATA;
- Alterações estruturais no banco de dados do SPDATA;
- Desenvolvimento de módulos não listados neste documento;
- Integrações com operadoras de planos de saúde além do que já é feito via
  guia TISS;
- Auditoria ativa de todas as ações do sistema (estrutura prevista, porém
  ainda não totalmente conectada ao fluxo).

---

## 9. Cronograma

**Investimento: A definir.**

O cronograma típico, em fases, pode ser planejado em conjunto após o
levantamento do ambiente:

| Fase | Duração estimada |
|------|------------------|
| Preparação e levantamento | 1 semana |
| Implantação e importações | 1 a 2 semanas |
| Treinamento | 1 semana |
| Operação assistida | 4 semanas |

> O cronograma exato depende do número de unidades, médicos e da
> disponibilidade dos acessos pelo cliente.

---

## 10. Investimento e condições comerciais

| Item | Descrição |
|------|-----------|
| Licenciamento | **A definir** em negociação comercial (modalidade mensal por unidade/usuário ou proposta fixa). |
| Implantação | **A definir** conforme escopo e ambiente. |
| Suporte e manutenção | **A definir** (nível de SLA e canal de atendimento). |
| Condições de pagamento | **A definir** em negociação comercial. |

> Nenhum valor é apresentado neste documento. A proposta comercial detalhada
> deve ser emitida após o levantamento do ambiente e o alinhamento do escopo.

---

## 11. Por que o MedSystem

| Critério | Resposta |
|----------|----------|
| **Para clínicas com SPDATA** | Aproveita o investimento existente, sem migração de dados. |
| **Para a gestão** | Faltas e exames não realizados deixam de ser invisíveis — viram painéis com valor estimado. |
| **Para o médico** | Consulta mais rápida, documentos automáticos e histórico do paciente na tela. |
| **Para a recepção** | Um sistema único para o dia inteiro, com painel de chamada moderno. |
| **Para a operação** | Deploy com Docker e documentação técnica incluída. |

---

## 12. Próximos passos

1. Agendar demonstração do sistema;
2. Realizar levantamento do ambiente (SPDATA, BioData, rede e servidor);
3. Definir cronograma e valores;
4. Iniciar a implantação em fases.

---

_Voltar ao [índice](./README.md)_
