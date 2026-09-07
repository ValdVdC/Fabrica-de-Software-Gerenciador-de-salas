# Guia de Handoff e Inicializacao de Sessoes com IA

Este documento e o guia pratico para abertura de novas sessoes com o Antigravity e interacao em linguagem natural nos mais diversos cenarios de desenvolvimento.

---

## 1. Principios Fundamentais

1. **Uma Sessao por Objetivo:** Abra uma sessao limpa para cada Sprint ou feature relevante para garantir foco, maxima velocidade e evitar degradacao de contexto.
2. **Memoria Persistente em Arquivos:** O Antigravity nao depende da memoria do chat anterior. Ele le automaticamente:
   - As regras em `AGENTS.md`
   - As tarefas e status no ClickUp via `scripts/clickup_sync.py`
   - O codigo e testes existentes em `backend/` e `frontend/`
3. **Linguagem Natural Livre:** Nao ha necessidade de frases fixas. Comunique-se de forma natural, tecnica e objetiva.

---

## 2. Catalogo de Exemplos de Prompts por Cenario

### Cenario A: Iniciar o Planejamento de uma Nova Sprint (Padrao Academico)
> *"Ola! Vamos iniciar o planejamento da Sprint X utilizando o agente planner-sdd com /grill-me."*
- **Comportamento do Agente:** Le o backlog e o documento normativo, conduz a entrevista `/grill-me`, cria a spec tecnica em `docs/specs/sprintX-<nome>.md` e mapeia tarefas no ClickUp.

---

### Cenario B: Nova Feature Avulsa (Fora do Backlog ou no Meio da Sprint)
> *"Tive uma ideia de feature: quero permitir que a Secretaria faca o upload de uma planilha CSV para cadastrar varios alunos de uma vez. Use o /grill-me para refinarmos os detalhes tecnicos."*
- **Comportamento do Agente:** Conduz a entrevista `/grill-me`, gera a spec correspondente, cria a tarefa no ClickUp e inicia o ciclo TDD.

---

### Cenario C: Feature com Requisitos Ja Claros (Sem Necessidade de Perguntas)
> *"Quero criar um endpoint simples GET /campi/{id}/salas que retorne apenas as salas ativas de um campus especifico. Pode criar os testes que falham e implementar direto via TDD."*
- **Comportamento do Agente:** Pula o `/grill-me`, cria a branch `feature/...`, implementa o teste Pytest (RED), escreve a rota (GREEN) e abre o PR.

---

### Cenario D: Correcao de Bug ou Ajuste Rapido (Hotfix)
> *"A rota de login esta retornando erro 500 quando o email nao existe no banco (deveria ser 401). Vamos criar um teste que reproduza esse cenario e corrigir esse bug?"*
- **Comportamento do Agente:** Cria branch `fix/...`, cria o teste que reproduz a falha, corrige o codigo da rota, valida a suite de testes e abre o PR para `homolog`.

---

### Cenario E: Melhoria Tecnica, Refatoracao ou Aumento de Cobertura
> *"Notei que a cobertura de testes do modulo de alocacao esta em 82%. Vamos criar testes de integracao adicionais para cobrir os casos de borda e garantir mais de 90%?"*
- **Comportamento do Agente:** Analisa relatorios do `pytest-cov`, identifica linhas nao cobertas e implementa novos cenarios de teste reais.

---

### Cenario F: Duvidas Tecnicas e Arquitetura (Sem Alterar Codigo)
> *"Pode me explicar como esta estruturada a comunicacao entre o FastAPI e o motor em C via ctypes hoje? Quero entender o fluxo de memoria."*
- **Comportamento do Agente:** Consulta o codigo, explica detalhadamente e nao realiza commits ou alteracoes desnecessarias.

---

### Cenario G: Evolucao do Produto Pos-Sprints (Novo Ciclo)
> *"Finalizamos todas as Sprints da disciplina. Agora quero evoluir o SIGAAS para um produto de mercado. Vamos planejar a integracao com OAuth do Google e notificacoes via WhatsApp?"*
- **Comportamento do Agente:** Atua como arquiteto de produto, planejando o novo roadmap e fatiando os epicos.

---

## 3. Fluxo de Execucao Padrao

```
[Mensagem do Usuario] -> [Spec / Alinhamento] -> [Branch feature/...] -> [Testes RED] 
       -> [Codigo GREEN] -> [PR para homolog] -> [CodeRabbit AI + CI 85%] 
       -> [Aprovacao Humana] -> [Merge + Auto-Delete] -> [ClickUp Concluido]
```
