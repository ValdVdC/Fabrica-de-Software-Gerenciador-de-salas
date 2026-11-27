# SPEC-012: Sprint 12 — Versão Final do Sistema (Code Freeze, Vídeos e Ensaio Completo)

- **Status:** Aguardando Aprovação (Gate 1)
- **Sprint:** 12 (Data-Limite: 28/11/2026 às 23:59)
- **Responsáveis:** Wesclei Batista (PO), Ewerton Thyago (SM) e Squad SIGAAS (Osvaldo, Gabriel, Flávio)
- **Referência Normativa:** `docs/projeto-gestao-salas-escalas.md` (Seção 4 — Sprint 12)

---

## 1. Contexto e Objetivo

A Sprint 12 encerra o desenvolvimento ativo do SIGAAS, consolidando a **Versão Final do Sistema (`v1.0.0`)** mediante:
1. Verificação integral de estabilidade e correção de quaisquer ajustes finais indispensáveis antes do congelamento;
2. **Code Freeze (`v1.0.0`)** formalizado por Git Tag e Release oficial no GitHub (`.github/workflows/release.yml`);
3. Planejamento e roteirização detalhada dos **dois vídeos obrigatórios**:
   - **Vídeo Horizontal (16:9):** duração máxima de **10 minutos** (problema, solução, arquitetura, tecnologias, funcionamento completo, motor C/OpenMP e IA preditiva);
   - **Vídeo Vertical (9:16):** dinâmico e criativo para Instagram, marcando `@pryscillabgoncalves` e `@antenorparnaiba`;
4. **Ensaio Completo da Apresentação:** checklist de ambiente/banco, sequência de demonstração ao vivo, **distribuição exata das falas entre os 5 integrantes**, cronometragem e registro de contingências;
5. **Pacote Acadêmico Final da Sprint 12:** `relatorio-sprint12.md`, `relatorio-consolidado-sprints-01-a-12.md` e PDF único `Grupo31_SIGAAS_Sprints01-12.pdf`.

---

## 2. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Validação Final Pré-Freeze e Estabilidade Ponta a Ponta
> **Como** equipe de engenharia,  
> **Quero** validar a suíte completa (backend Pytest, motor C/OpenMP, frontend Karma/build, ambiente local/Docker e seed), aplicando eventuais correções críticas indispensáveis,  
> **Para** congelar a versão `v1.0.0` com zero regressões ou bugs bloqueantes.

#### Cenário 1.1: Verificação integral e liberação para Code Freeze
- **Given** o código consolidado na `main` após a Sprint 11;
- **When** forem executadas as suítes completas de backend, motor C e frontend e verificada a execução real integrada (banco, API, alocação OpenMP, IA 40% e interface);
- **Then** 100% dos testes e checks de CI devem passar sem regressões;
- **And** quaisquer limitações técnicas conhecidas devem estar explicitamente documentadas sem comprometer o fluxo essencial.

---

### História 2: Planejamento dos Vídeos (16:9 e 9:16) e Ensaio Completo da Apresentação
> **Como** equipe do Grupo 31,  
> **Quero** dispor de roteiros cronometrados para os dois vídeos (16:9 até 10 min e 9:16 Instagram) e para o ensaio completo da apresentação com falas divididas entre os 5 integrantes,  
> **Para** executar a gravação e a apresentação final com rigor técnico, clareza e dentro do tempo limite.

#### Cenário 2.1: Roteiros audiovisuais e distribuição de falas
- **Given** a arquitetura final do SIGAAS (`v1.0.0`);
- **When** for estruturado o documento `docs/entregas/roteiro-videos-e-apresentacao.md`;
- **Then** deve conter:
  - Roteiro detalhado do **Vídeo Horizontal (16:9, <= 10 min)** cobrindo problema, solução, arquitetura 3 camadas, stack, demonstração ao vivo dos fluxos, motor C/OpenMP (speedup) e IA `scikit-learn` (limiar 40% *Human-in-the-Loop*);
  - Roteiro/storyboard do **Vídeo Vertical (9:16, Instagram)** com menção explícita a `@pryscillabgoncalves` e `@antenorparnaiba`;
  - Registro do **Ensaio Completo da Apresentação** com preparação do ambiente (`make setup` / `serve_local.py`), verificação de banco/serviços, divisão das falas entre Ewerton, Wesclei, Osvaldo, Gabriel e Flávio, tempo total cronometrado e plano de contingência.

---

### História 3: Code Freeze (`v1.0.0`), Relatório Sprint 12 e PDF Cumulativo `01-12`
> **Como** Scrum Master e banca examinadora,  
> **Quero** a versão final congelada via tag/release `v1.0.0` no GitHub e um PDF único cumulativo (Sprints 01 a 12) contendo todas as entregas obrigatórias da Sprint 12,  
> **Para** formalizar a entrega no Microsoft Teams dentro do prazo de `28/11/2026`.

#### Cenário 3.1: Congelamento formal e pacote acadêmico final
- **Given** os PRs 1 e 2 mesclados na `main`;
- **When** for gerado o pacote acadêmico da Sprint 12 (`relatorio-sprint12.md`, `relatorio-consolidado-sprints-01-a-12.md`, `Grupo31_SIGAAS_Sprints01-12.pdf`) e publicada a tag **`v1.0.0`**;
- **Then** o PDF deve atender todos os 8 tópicos exigidos no edital da Sprint 12 e cumprir rigorosamente a Regra 8 do `AGENTS.md` (zero alucinações institucionais);
- **And** a tag `v1.0.0` deve estar publicada no GitHub acionando o release oficial.

---

## 3. Fatiamento em Pull Requests (Limite <= 400 linhas de código por PR)

| Ordem | PR / Branch | Task ClickUp | Responsável | Escopo |
| :---: | :--- | :---: | :--- | :--- |
| **PR 1** | `chore/sprint12-freeze-validation` | `#1dft1fan6p0` | Osvaldo / Gabriel | `SPEC-012`, verificação integral pré-freeze (backend, C/OpenMP, frontend, execução local integrada) e eventuais ajustes críticos indispensáveis |
| **PR 2** | `docs/sprint12-videos-ensaio` | `#1dft1fan6p1` | Wesclei / Ewerton / Gabriel | `docs/entregas/roteiro-videos-e-apresentacao.md` (roteiro 16:9 <= 10 min, 9:16 Instagram, ensaio completo e falas dos 5 integrantes) |
| **PR 3** | `docs/sprint12-relatorio-pdf` | `#1dft1fan6p2` | Flávio / SM | `relatorio-sprint12.md`, `relatorio-consolidado-sprints-01-a-12.md`, `Grupo31_SIGAAS_Sprints01-12.pdf` + publicação da tag **Code Freeze `v1.0.0`** |

---

## 4. Revisão de Escopo (Decisão do Usuário em 27/11/2026) — Pendente de Re-Aprovação no Gate 1

O Code Freeze `v1.0.0` passa a incluir o motor paralelo em OpenCL, conforme `docs/specs/spec-motor-opencl-cuda.md` (SPEC-M2-01). Os demais itens da auditoria (segurança/MFA, fluxos acadêmicos, redesign UX/UI e DevOps) ficam para os ajustes finais entre 29/11 e 07/12.

### 4.1 Escopo do Code Freeze (entrega de 28/11)

| Ordem | PR / Branch | Conteúdo |
| :---: | :--- | :--- |
| 1 | `feat/motor-c-professor-conflict` | `professor_id` em `TurmaC`, checagem de conflito docente (SPEC-M2-01, PR 1) |
| 2 | `feat/motor-opencl-discovery` | Descoberta de plataforma/dispositivo e compilação JIT do kernel (SPEC-M2-01, PR 2a) |
| 3 | `feat/motor-opencl-kernel-exec` | Execução do kernel multi-start, profiling e fallback OpenCL para OpenMP (SPEC-M2-01, PR 2b) |
| 4 | `feat/motor-ffi-status-opencl` | Ponte `ctypes`, seleção de backend e `GET /api/v1/motor/dispositivos` autenticado (SPEC-M2-01, PR 3) |
| 5 | `docs/sprint12-videos-ensaio` | Roteiro dos vídeos e ensaio |
| 6 | `docs/sprint12-relatorio-pdf` | Relatório, PDF `01-12` com benchmark OpenCL medido e tag `v1.0.0` |

### 4.2 Regra de Honestidade da Entrega

Se o PR 3 (kernel) não estiver mesclado e medido a tempo, o relatório e o PDF NÃO podem declarar OpenCL como implementado. Nesse caso a tag registra apenas o que existe e o OpenCL segue como pendência declarada.

### 4.3 Adiado para os Ajustes Finais (29/11 a 07/12)

- `PR 4` da SPEC-M2-01 (persistência não destrutiva de `Horario`, migration).
- Specs de segurança/MFA, fluxos acadêmicos, redesign UX/UI e DevOps.
- Conflito de numeração de migrations a resolver antes de implementar: SPEC-M2-01 (PR 4) e a spec de segurança (PR 2) reservam a migration `004`; a spec de fluxos usa `005`.

### 4.4 Governança do Debate Adversarial

- PRs de código do motor C/OpenCL: debate completo com 4 subagentes e re-review.
- PRs somente de documentação: debate reduzido a 2 subagentes (`adversary-compliance` e `adversary-breaker`).

### 4.5 Tarefas no ClickUp (Lista `901716884864`)

| Escopo | Task |
| :--- | :---: |
| Motor 1: conflito de professor | `#1dft1fan6rn` |
| Motor 2a: descoberta de dispositivo OpenCL | `#1dft1fan6rp` |
| Motor 2b: kernel OpenCL e fallback | `#1dft1fan6rq` |
| Motor 3: ponte `ctypes` e endpoint de dispositivos | `#1dft1fan6rr` |
| Roteiro dos vídeos e ensaio | `#1dft1fan6p1` |
| Relatório, PDF `01-12` e tag `v1.0.0` | `#1dft1fan6p2` |
| Verificação final antes da tag (suítes completas) | `#1dft1fan6p0` |
