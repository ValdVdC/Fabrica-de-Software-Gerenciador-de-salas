## 📌 Descrição da Mudança
Breve descrição do que este Pull Request implementa ou corrige.

- **Sprint:** Sprint X
- **Spec SDD:** `docs/specs/<nome-da-spec>.md`
- **Tarefa ClickUp:** [ID da Tarefa ou URL]
- **Tipo de Mudança:**
  - [ ] Nova Feature (SDD)
  - [ ] Correção de Bug (Hotfix)
  - [ ] Refatoração / Melhoria
  - [ ] Documentação / DevOps

---

## 🧪 Checklist SDD & TDD (Inviolável)
- [ ] **Spec Aprovada:** A especificação foi previamente aprovada no Gate 1.
- [ ] **Fase RED cumprida:** Foram escritos testes automatizados antes da implementação.
- [ ] **Fase GREEN cumprida:** Todos os testes unitários e de integração estão passando (100% verde).
- [ ] **Sem Lógica no Frontend:** Nenhuma regra de negócio pesada foi colocada no Angular.
- [ ] **Sem Banco no Motor C:** O módulo C permanece isolado e sem dependências externas.
- [ ] **Migration Alembic:** Se houve alteração de banco de dados, a migration foi gerada e testada.
- [ ] **Status ClickUp:** Tarefa no ClickUp atualizada para `Review` ou `Concluído`.

---

## 🔒 Auditoria de Segurança & Code Review (`sec-reviewer`)
- [ ] Sem credenciais hardcoded ou arquivos `.env` commitados.
- [ ] Inputs sanitizados e validados com Pydantic.
- [ ] Permissões por perfil (Admin, Professor, Aluno, Secretaria) verificadas.

---

## 📸 Screenshots / Demonstração (se aplicável ao Frontend)
*(Insira capturas de tela ou logs de execução aqui)*
