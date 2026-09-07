## Descricao da Mudanca
Breve descricao do que este Pull Request implementa ou corrige.

- **Sprint:** Sprint X
- **Spec SDD:** `docs/specs/<nome-da-spec>.md`
- **Tarefa ClickUp:** [ID da Tarefa ou URL]
- **Tipo de Mudanca:**
  - [ ] Nova Feature (SDD)
  - [ ] Correcao de Bug (Hotfix)
  - [ ] Refatoracao / Melhoria
  - [ ] Documentacao / DevOps

---

## Checklist SDD & TDD (Inviolavel)
- [ ] **Spec Aprovada:** A especificacao foi previamente aprovada no Gate 1.
- [ ] **Fase RED cumprida:** Foram escritos testes automatizados antes da implementacao.
- [ ] **Fase GREEN cumprida:** Todos os testes unitarios e de integracao estao passando (100% verde).
- [ ] **Limite de Diff:** PR contem no maximo 300 a 400 linhas de codigo modificado.
- [ ] **Sem Logica no Frontend:** Nenhuma regra de negocio pesada foi colocada no Angular.
- [ ] **Sem Banco no Motor C:** O modulo C permanece isolado e sem dependencias externas.
- [ ] **Migration Alembic:** Se houve alteracao de banco de dados, a migration foi gerada e testada.
- [ ] **Status ClickUp:** Tarefa no ClickUp atualizada para `Review` ou `Concluido`.

---

## Padroes de Codigo e Seguranca (`sec-reviewer`)
- [ ] **Conventional Commits:** Titulo do PR segue o padrao `<tipo>(<escopo>): <descricao curta no imperativo>`.
- [ ] **Zero Emojis:** Nenhum emoji em codigo, comentarios, mensagens ou frontend (icones formais usados se aplicavel).
- [ ] **Comentarios Concisos:** Comentarios estritamente necessarios com no maximo 1 a 2 linhas.
- [ ] **Seguranca:** Sem credenciais hardcoded ou arquivos `.env` commitados.
- [ ] **Validacao:** Inputs sanitizados e validados com Pydantic.
- [ ] **Autorizacao:** Permissoes por perfil (Admin, Professor, Aluno, Secretaria) verificadas.

---

## Screenshots / Demonstracao (se aplicavel ao Frontend)
*(Insira capturas de tela ou logs de execucao aqui)*
