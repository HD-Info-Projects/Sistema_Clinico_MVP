# MedSystem — Público-alvo e Personas

**Documento Comercial**

_Data do documento: agosto de 2026_

---

## 1. Público-alvo

O MedSystem é direcionado a **clínicas e grupos de saúde que utilizam o
SPDATA** como sistema de gestão e desejam digitalizar o prontuário, organizar
a operação de recepção e ganhar visibilidade gerencial — sem substituir o
sistema de origem e sem perder o histórico existente.

### Segmentos de clientes

| Segmento | Por que se encaixa |
|----------|--------------------|
| **Clínicas multiespecialidade** | Agenda diária intensa, múltiplos médicos, necessidade de prontuário e controle de faltas. |
| **Clínicas com sistema SPDATA** | A integração nativa evita digitação dupla e migração de dados. |
| **Clínicas com histórico em BioData/SQL Server** | Acesso ao histórico legado de anamneses dentro do novo prontuário. |
| **Grupos de clínicas com múltiplas unidades** | Controle por unidade, usuários vinculados a várias clínicas e troca de unidade sem novo login. |
| **Clínicas que atendem convênios** | Geração de guia TISS, catálogo de exames por convênio e controle de retenção de exames. |
| **Clínicas que querem modernizar a experiência do paciente** | Painel de chamada em TV com voz, fila em tempo real e tempo de espera medido. |

### Tamanhos típicos

O sistema se adequa a:

- **Pequeno porte** — 1 a 5 médicos, uma unidade;
- **Médio porte** — 6 a 20 médicos, uma ou mais unidades;
- **Grupos** — múltiplas unidades com médicos atuando em mais de uma delas.

---

## 2. Personas

### Persona 1 — Diretora / Gestora da clínica

**Perfil.** Responsável pela operação e pelos resultados da clínica. Precisa
entender o que está acontecendo sem depender de planilhas ou de perguntar a
cada pessoa.

**Dores.**

- Não sabe quantas consultas foram perdidas (no-show) e nem por quê;
- Não acompanha se os exames solicitados foram realizados — e quanto de
  faturamento está "preso" nisso;
- Depende de informações espalhadas entre SPDATA, papel e planilhas;
- Não tem visão clara do tempo de espera do paciente e do fluxo do dia.

**Como o MedSystem ajuda.**

| Necessidade | Recurso do MedSystem |
|-------------|----------------------|
| Ver o tamanho das faltas | Módulo de no-show com gráficos por mês, especialidade e dia da semana. |
| Recuperar exames não realizados | Módulo de retenção de exames com status, dias em aberto e valor estimado. |
| Centralizar a visão do dia | Dashboard da recepção com resumo de agendados, em espera, em atendimento e atendidos. |
| Tomar decisão com dados | Indicadores de conversão por médico e oportunidades financeiras. |

**O que valoriza.** Visão gerencial em tempo real, recuperação de receita,
profissionalismo do sistema e facilidade de adoção pela equipe.

---

### Persona 2 — Médico(a)

**Perfil.** Atende na clínica diariamente ou em alguns períodos. Quer agilidade
para registrar a consulta, gerar documentos e seguir para o próximo paciente.

**Dores.**

- Perde tempo digitando anamnese e evolução do zero;
- Demora para localizar CID-10 ou montar receitas e exames;
- Precisa emitir atestados e encaminhamentos com frequência;
- Não tem acesso fácil ao histórico antigo do paciente;
- Quer ser chamado ao próximo paciente sem depender da recepção gritando.

**Como o MedSystem ajuda.**

| Necessidade | Recurso do MedSystem |
|-------------|----------------------|
| Registrar rápido | Modelos de anamnese, receita, exames e orientações por médico. |
| Emitir documentos | Atestado, encaminhamento e solicitação de procedimento em poucos cliques. |
| Buscar diagnóstico | Busca CID-10 com cache e seleção de diagnóstico principal e secundário. |
| Ver histórico | Histórico local e histórico BioData com conversão automática de texto. |
| Gerenciar a fila | Dashboard com fila, chamada do próximo paciente e marcação de falta. |

**O que valoriza.** Agilidade, menos retrabalho, organização e rastreabilidade
da evolução médica.

---

### Persona 3 — Recepção / Assistente administrativa

**Perfil.** Opera o sistema o dia inteiro: confirma pacientes, organiza a fila,
informa atrasos e auxilia os médicos.

**Dores.**

- Muitos sistemas e telas abertas ao mesmo tempo;
- Dificuldade para saber quem chegou, quem está em atendimento e quem faltou;
- Não tem um jeito simples de saber se o paciente fez o exame solicitado;
- Precisa lidar com o fluxo da sala de espera e orientar os pacientes.

**Como o MedSystem ajuda.**

| Necessidade | Recurso do MedSystem |
|-------------|----------------------|
| Um único lugar para o dia | Tela de recepção consolidando agendados e atendidos do dia. |
| Atualizar o status | Mudança de status com regras claras (em espera, em atendimento, atendido, faltou). |
| Acompanhar exames | Módulo de retenção com telefone do paciente para contato de cobrança de exame. |
| Orientar pacientes | Painel de chamada com voz e sala indicada. |
| Registrar faltas | Motivos de no-show com poucos cliques. |

**O que valoriza.** Simplicidade, velocidade, menos troca de telas e menos
retrabalho.

---

### Persona 4 — Responsável de TI / suporte da clínica

**Perfil.** Cuida da infraestrutura e dos sistemas legados (SPDATA/Firebird,
BioData/SQL Server). Avalia o risco da integração e a facilidade de manter a
solução.

**Dores.**

- Receia que uma nova ferramenta "quebre" o sistema de origem;
- Não quer redigitar ou duplicar dados entre sistemas;
- Precisa de deploy simples e manutenção viável;
- Quer documentação clara do que o sistema acessa no SPDATA.

**Como o MedSystem ajuda.**

| Necessidade | Recurso do MedSystem |
|-------------|----------------------|
| Integração segura | Acesso de leitura/espelhamento ao SPDATA; a origem continua sendo a fonte. |
| Deploy simples | Docker Compose com MySQL, Redis, backend e frontend; HTTPS automático (Caddy). |
| Manutenção | Migrações automáticas de banco e comandos CLI para importações e cadastros. |
| Documentação | Documento técnico de tabelas e integrações incluído no repositório. |

**O que valoriza.** Baixo risco, documentação, infraestrutura conteinerizada e
facilidade de operação.

---

## 3. Canais de aquisição recomendados

| Canal | Abordagem |
|-------|-----------|
| **Venda direta consultiva** | Demonstração guiada pelos módulos de no-show e retenção de exames — os de maior impacto financeiro. |
| **Parceiros de sistemas SPDATA** | Integração como valor agregado para clientes que já usam SPDATA. |
| **Indicação de médicos** | A adoção pelo médico gera demanda pela clínica inteira. |
| **Material de apoio comercial** | Documentos desta pasta (visão geral, descrição de produto, personas e proposta). |

---

## 4. Mensagens-chave por persona

| Persona | Mensagem central |
|---------|------------------|
| Gestora | "Veja onde a clínica está perdendo consultas e exames — e recupere receita com dados." |
| Médico | "Registre a consulta e emita documentos em segundos, com histórico do paciente na tela." |
| Recepção | "Um só lugar para o dia inteiro: quem chegou, quem falta e quem precisa de contato." |
| TI | "Integração segura com o SPDATA e deploy simples com Docker." |

---

_Continue lendo: [Proposta comercial executiva](./04-proposta-comercial-executivo.md)_
