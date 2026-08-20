# Guia simples de GitHub e Gitflow (Hackathon)

## 1. Uso correto do GitHub

* Sempre trabalhe em **branches** (nunca direto na main)
* Nomeie branches de forma clara:

  * feature/nome-da-feature
  * fix/nome-do-bug
* Faça commits pequenos e frequentes
* Sempre escreva mensagens de commit claras
* Abra um **Pull Request (PR)** para revisar antes de juntar na main
* Revise o código dos colegas quando possível

---

## 2. Status dos arquivos no Git

* **Untracked**: arquivo novo ainda não monitorado
* **Modified**: arquivo modificado
* **Staged**: pronto para commit (usando git add)
* **Committed**: salvo no histórico

Fluxo básico:

1. Criar/editar arquivos
2. git add .
3. git commit -m "mensagem"
4. git push

---

## 3. Padrão de mensagens de commit

Use mensagens curtas e objetivas:

* feat: nova funcionalidade
* fix: correção de bug
* docs: documentação
* refactor: melhoria de código
* config: configurações globais ou locais o ambiente/projeto
* remove: remoção de algum arquivo ou dado
* test: testes

Exemplo:

feat: adiciona tela de login
fix: corrige erro no cadastro

---

## 4. Gitflow simplificado

Branches principais:

* **main** → versão estável
* **develop** → desenvolvimento

Outras branches:

* feature/* → novas funcionalidades
* fix/* → correções

Fluxo:

1. Criar branch a partir de develop
2. Desenvolver a feature
3. Fazer commits
4. Abrar Pull Request para develop
5. Após validação → merge
6. Quando tudo estiver pronto → merge develop → main

---

## 5. Boas práticas para o Hackathon

* Comunicação constante
* Não sobrescrever código dos outros
* Sempre dar pull antes de começar
* Evitar commits gigantes
* Testar antes de subir

---

## 6. Comandos essenciais

* git clone
* git pull
* git add .
* git commit -m "mensagem"
* git push
* git checkout -b nome-da-branch

