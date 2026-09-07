# Guia de Handoff e Inicialização de Sessões com IA

Este documento é o guia prático de cabeceira para você (ou qualquer membro da equipe) saber **como abrir novas sessões** com o Antigravity e interagir em linguagem natural nos mais diversos cenários.

---

## 🎯 Princípios Fundamentais

1. **Uma Sessão por Objetivo:** Abra uma sessão limpa para cada Sprint ou feature relevante para garantir foco, máxima velocidade e evitar degradação de contexto.
2. **A Memória está nos Arquivos:** O Antigravity não precisa se lembrar do chat anterior. Ele lê automaticamente:
   - As regras em [`AGENTS.md`](../AGENTS.md)
   - As tarefas e status no ClickUp via [`scripts/clickup_sync.py`](../scripts/clickup_sync.py)
   - O código e testes existentes em `backend/` e `frontend/`
3. **Linguagem Natural Livre:** Você **não precisa** usar frases engessadas. Fale normalmente, como falaria com um líder técnico ou engenheiro sênior.

---

## 📋 Catálogo de Prompts por Cenário (Copie e Cole)

### 1. Iniciar o Planejamento de uma Nova Sprint (Padrão Acadêmico)
> *"Olá! Vamos iniciar o planejamento da **Sprint X** utilizando o agente `planner-sdd` com `/grill-me`."*
- **O que a IA fará:** Lerá o backlog no ClickUp e o documento normativo, fará uma rodada de perguntas via `/grill-me`, criará a spec técnica em `docs/specs/sprintX-<nome>.md` e quebrará as tarefas no ClickUp.

---

### 2. Nova Feature Avulsa (Fora do Backlog ou no Meio da Sprint)
> *"Tive uma ideia de feature: quero permitir que a Secretaria faça o upload de uma planilha CSV para cadastrar vários alunos de uma vez. Use o `/grill-me` para refinarmos os detalhes técnicos."*
- **O que a IA fará:** Conduzirá a entrevista `/grill-me`, gerará a spec correspondente, criará a tarefa no ClickUp e seguirá para o ciclo TDD.

---

### 3. Feature com Requisitos Já Claros (Sem Precisar de Perguntas)
> *"Quero criar um endpoint simples `GET /campi/{id}/salas` que retorne apenas as salas ativas de um campus específico. Pode criar os testes que falham e implementar direto via TDD."*
- **O que a IA fará:** Como você já foi específico, ela pula o `/grill-me`, cria a branch `feature/...`, implementa o teste Pytest (RED), escreve a rota (GREEN) e abre o PR.

---

### 4. Correção de Bug ou Ajuste Rápido (Hotfix)
> *"A rota de login está retornando erro 500 quando o email não existe no banco (deveria ser 401). Vamos criar um teste que reproduza esse cenário e corrigir esse bug?"*
- **O que a IA fará:** Cria branch `fix/login-401`, cria o teste que falha demonstrando o erro, corrige o código da rota, valida a suíte de testes e abre o PR para `homolog`.

---

### 5. Melhoria Técnica, Refatoração ou Aumento de Cobertura
> *"Notei que a cobertura de testes do módulo de alocação está em 82%. Vamos criar testes de integração adicionais para cobrir os casos de borda e garantir mais de 90%?"*
- **O que a IA fará:** Analisa os relatórios do `pytest-cov`, identifica as linhas não cobertas e implementa novos cenários de teste reais.

---

### 6. Dúvidas Técnicas, Arquitetura e Consulta (Sem Alterar Código)
> *"Pode me explicar como está estruturada a comunicação entre o FastAPI e o motor em C via ctypes hoje? Quero entender o fluxo de memória."*
- **O que a IA fará:** Consultará o código, explicará detalhadamente com diagramas e não fará nenhum commit ou alteração desnecessária.

---

### 7. Quando Acabarem as Sprints do Semestre (Evolução Contínua)
> *"Finalizamos todas as Sprints da disciplina! Agora quero evoluir o SIGAAS para um produto real de mercado. Vamos planejar a integração com OAuth do Google e notificações via WhatsApp?"*
- **O que a IA fará:** Atuará como arquiteto de produto, planejando a nova fase de evolução além do escopo acadêmico inicial.

---

## 🧭 O Ciclo de Execução Automático

Independentemente de como você iniciar, os agentes sempre seguirão este fluxo:

```
[Sua Mensagem] ➔ [Spec / Alinhamento] ➔ [Branch feature/...] ➔ [Testes RED] 
       ➔ [Código GREEN] ➔ [PR para homolog] ➔ [CodeRabbit AI + CI 85%] 
       ➔ [Você Aprova] ➔ [Merge + Auto-Delete] ➔ [ClickUp Concluído]
```
