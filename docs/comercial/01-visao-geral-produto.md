# MedSystem — Sistema Clínico

**Documento Comercial — Visão Geral do Produto**

_Data do documento: agosto de 2026_

---

## Elevator Pitch

O **MedSystem** é um sistema clínico que conecta a operação da clínica ao
prontuário do paciente em um único fluxo digital: a agenda que já existe no
seu sistema hospitalar entra automaticamente no dia do médico, a recepção
faz o check-in e o painel de chamada conduz o paciente até a sala, e o
médico registra o atendimento completo — anamnese, evolução, CID, receita e
solicitações de exames — sem digitar duas vezes a mesma informação.

Em vez de substituir o sistema que a clínica já utiliza, o MedSystem se
**integra a ele** (SPDATA/Firebird), sincroniza agenda, pacientes, médicos,
convênios e exames, e devolve à gestão dois instrumentos que normalmente
faltam nas clínicas: o **controle de faltas (no-show)** e o **acompanhamento
da conversão de exames solicitados em exames realizados** — com indicadores
que apontam oportunidades financeiras diretas.

O resultado é uma operação mais rápida na recepção, um atendimento médico
mais ágil e rastreável, e uma gestão que enxerga, em números, onde estão
perdendo pacientes e faturamento.

---

## O que é

O MedSystem é uma plataforma web de **gestão clínica e prontuário eletrônico**
voltada para clínicas e consultórios que já operam com o sistema SPDATA. Ele
é composto por:

- **Área do médico** — agenda do dia, fila de pacientes, prontuário
  eletrônico com anamnese, evolução, diagnóstico (CID-10), prescrição e
  solicitação de exames;
- **Área da recepção** — check-in dos pacientes, gestão de faltas com
  registro de motivos e relatórios, e acompanhamento da retenção de exames
  solicitados;
- **Painel de chamada em TV** — fila de pacientes em tempo real, com chamada
  por voz nas salas de atendimento;
- **Integrações** — sincronização bidirecional com o SPDATA (agenda,
  atendimentos, pacientes, médicos, convênios, especialidades, exames,
  CID-10 e logos TISS) e consulta ao histórico legado do BioData;
- **Indicadores** — taxas de conversão de exames, exames mais solicitados,
  motivos de falta, oportunidades financeiras e tendências.

---

## Problema que resolve

Clínicas que usam sistemas legados de gestão (como o SPDATA) enfrentam
desafios operacionais que impactam diretamente a receita:

1. **Informação espalhada e retrabalho** — a agenda do médico está em um
   sistema, o prontuário em papel ou em outro sistema, e a recepção precisa
   "caçar" o histórico do paciente;
2. **Faltas silenciosas** — pacientes agendados não comparecem, a clínica não
   sabe o motivo e não consegue medir o impacto das ausências;
3. **Exames solicitados e nunca realizados** — o médico solicita exames, mas
   a clínica não acompanha se o paciente os realizou, perdendo faturamento
   de guias e desfechos clínicos;
4. **Filas e espera sem controle** — não há visibilidade em tempo real de
   quem está aguardando, quanto tempo está esperando e para qual sala o
   paciente deve se dirigir;
5. **Histórico clínico fragmentado** — o médico não tem acesso rápido ao
   histórico de atendimentos anteriores do paciente ao iniciar a consulta;
6. **Documentos manuais** — atestados, encaminhamentos, receitas e guias TISS
   são digitados do zero a cada atendimento.

O MedSystem foi desenhado para resolver exatamente esses pontos, mantendo o
SPDATA como sistema de origem (fonte da verdade) e adicionando a camada de
experiência digital que faltava.

---

## Para quem foi desenvolvido

O sistema foi desenvolvido para **clínicas médicas e unidades de saúde** que:

- utilizam o **SPDATA** (Firebird) como sistema de gestão;
- possuem **agenda médica com múltiplos profissionais** e especialidades;
- precisam de **prontuário eletrônico** estruturado e rastreável;
- atendem **pacientes de convênios** (uso de guias TISS) e particulares;
- desejam **controlar faltas** e **converter exames solicitados em realizados**;
- podem operar em **uma ou múltiplas unidades/clínicas**.

---

## Proposta de valor

> **"Integre sua clínica ao prontuário digital sem trocar o sistema que já
> funciona — e transforme faltas e exames não realizados em oportunidades
> gerenciadas."**

Em resumo, o MedSystem oferece:

| Valor | Como entrega |
|-------|--------------|
| **Zero redigitação de agenda** | Sincronização automática da agenda e dos atendimentos do SPDATA para a área do médico e da recepção. |
| **Atendimento mais rápido** | Prontuário com busca de CID-10, modelos de anamnese, receita, exame e orientação, e documentos prontos para impressão. |
| **Menos faltas e mais retenção** | Controle de no-show com motivos, gráficos e relatórios; acompanhamento de exames solicitados até a realização. |
| **Gestão com dados** | Indicadores de conversão de exames, exames mais solicitados, motivos de falta e oportunidades financeiras. |
| **Experiência moderna na clínica** | Painel de chamada em TV com voz, fila em tempo real e telas dedicadas para médico e recepção. |
| **Segurança e rastreabilidade** | Autenticação por perfil, controle de acesso por unidade, versionamento de evolução médica e registro de ações. |

---

## Diferenciais em uma frase

- **Integração nativa com SPDATA** — agenda, atendimentos, pacientes,
  convênios, exames e CID-10 sincronizados sem digitação manual;
- **Painel de chamada com voz** — a TV da clínica chama o paciente pelo nome
  e indica a sala, em tempo real;
- **Retenção de exames com valor estimado** — a recepção enxerga exames em
  aberto, dias sem realização e oportunidades de conversão;
- **No-show tratado como dado** — faltas com motivo, tendência por mês,
  especialidade e dia da semana;
- **Prontuário com versionamento** — toda alteração de evolução médica é
  preservada em versões anteriores;
- **Histórico legado acessível** — anamneses antigas do BioData (SQL Server)
  consultáveis no atendimento atual.

---

## Modelo de operação em uma imagem

```
        SPDATA (Firebird)                    MedSystem                        Usuários
  ┌──────────────────────┐        ┌──────────────────────────┐      ┌──────────────────┐
  │ Agenda (REPACAGD)    │──sync──▶│  Área do médico          │◀─────│  Médicos          │
  │ Atendimentos         │◀────sync│  • agenda, fila, chamada │      │                   │
  │ Pacientes            │         │  • prontuário eletrônico │      │                  │
  │ Médicos/CRM          │         │  • CID-10, prescrição    │      │                  │
  │ Convênios            │──sync──▶│  • exames, documentos    │      │                  │
  │ Exames/Procedimentos │         │  • guia TISS             │      │                  │
  │ CID-10, Logos TISS   │         ├──────────────────────────┤      │                  │
  └──────────────────────┘         │  Área da recepção        │◀─────│  Recepção        │
                                   │  • check-in e fila       │      │                  │
  BioData (SQL Server)             │  • no-show e retenção    │      │                  │
  ┌──────────────────────┐         │  • relatórios e gráficos │      │                  │
  │ Histórico de         │──consulta├──────────────────────────┤      │                  │
  │ anamneses legado     │         │  Painel de chamada (TV)  │◀─────│  Sala de espera  │
  └──────────────────────┘         └──────────────────────────┘      └──────────────────┘
```

---

## Funcionalidades principais (resumo)

| Área | Funcionalidades |
|------|-----------------|
| **Autenticação e perfis** | Login com JWT, perfis médico / recepção / admin, vínculo de usuário a múltiplas unidades, seleção de clínica. |
| **Agenda médica** | Agenda sincronizada do SPDATA, status de atendimento, busca e filtros, fila de pacientes. |
| **Painel de chamada** | Fila em tempo real via SSE, chamada por voz (texto-para-fala em português), salas de atendimento, tela para TV. |
| **Recepção e check-in** | Visão consolidada do dia (agendados + atendidos), filtros por médico/especialidade/status, resumo de atendimentos. |
| **No-show** | Identificação de faltas, registro de motivos, relatórios e gráficos por mês, especialidade e dia da semana. |
| **Retenção de exames** | Acompanhamento de exames solicitados, status (pendente/realizado/não convertido), dias em aberto, valor estimado, oportunidades financeiras. |
| **Atendimento médico** | Prontuário eletrônico: anamnese, evolução com versionamento, CID-10, prescrição, solicitação de exames, documentos médicos, guia TISS, modelos/padrões. |
| **Histórico do paciente** | Histórico local de atendimentos finalizados e histórico legado do BioData. |
| **Integrações** | Importação de convênios, especialidades, exames e procedimentos do SPDATA; exportação de logos TISS; sincronização de agenda e atendimentos. |
| **Administração** | Comandos de linha de comando para cadastro de admin, recepção, médicos, unidades e importações. |
| **Infraestrutura** | Implantação via Docker Compose com HTTPS automático (Caddy), MySQL 8.4, Redis 7, healthchecks e deploy documentado para VPS. |

---

## Notas de transparência

- O sistema **não substitui o SPDATA**: ele se integra ao SPDATA e mantém
  espelhos locais dos dados (agenda, atendimentos, convênios, especialidades,
  exames).
- Algumas estruturas previstas no banco (fila de sincronização, logs de
  integração e auditoria) estão **implementadas como modelo de dados**, mas
  ainda não estão totalmente conectadas ao fluxo operacional — detalhes na
  [descrição do produto](./02-descricao-produto-comercial.md).
- A tela de retenção de exames funciona com os dados disponíveis hoje; dados
  como laudo/resultado e valores reais de faturamento dependem de fontes que
  ainda precisam ser mapeadas no SPDATA — detalhes na
  [descrição do produto](./02-descricao-produto-comercial.md).
- Nenhum dado sensível ou credencial é divulgado nesta documentação.

---

_Continue lendo: [Descrição do produto comercial](./02-descricao-produto-comercial.md)_
