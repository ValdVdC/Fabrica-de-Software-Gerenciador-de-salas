# Relatório Técnico: Sprint 09

## Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS)

**Disciplina:** Fábrica de Software & Tópicos Avançados em Computação  
**Curso:** Curso de Bacharelado em Ciência da Computação  
**Turma:** 8MB - CC  
**Equipe:** Grupo 31 — SIGAAS  
**Entrega:** Sprint 09 - Homologação, Testes Completos e Atendimento às Devolutivas da Banca  
**Data-Limite de Entrega:** 07 de Novembro de 2026 às 23:59  
**Repositório Oficial no GitHub:** [https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas)

---

### 1. Identificação da Equipe e Distribuição de Papéis

| Integrante | Matrícula | Papel no Squad | Responsabilidade Técnica Principal |
| :--- | :---: | :--- | :--- |
| **Ewerton Thyago Tavares da Silva** | 01573977 | Scrum Master (Líder) | Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams |
| **Wesclei Batista Da Cruz Júnior** | 01606772 | Product Owner | Levantamento de requisitos, regras de negócio e validação dos critérios de aceite |
| **Osvaldo Vasconcelos de Carvalho** | 01614171 | Dev Backend / Sistemas | Arquitetura de API, integração FFI C/OpenMP (`ctypes`), endpoints e migrations |
| **Gabriel Porfírio dos Santos** | 01591399 | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| **Flávio Vecch de Brito Farias** | 01600988 | DBA & Documentação | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica |

---

# PARTE 9 - SPRINT 09: HOMOLOGAÇÃO, TESTES COMPLETOS E ATENDIMENTO ÀS DEVOLUTIVAS

## 9.1 Contexto e Objetivos

A Sprint 09 encerra o ciclo de implementação funcional do SIGAAS e desloca o esforço da equipe para a **homologação científica e operacional** da solução. O objetivo central é preparar o sistema para a banca examinadora e responder, com evidência rastreável, às devolutivas docentes das Sprints 05 e 06.

A especificação normativa da sprint é a `SPEC-009`, em `docs/specs/sprint9-testes-completos.md` (commit `e9b74f4`), com status de proposta para aprovação no Gate 1 em 02 de Novembro de 2026. A spec organiza a entrega em quatro frentes: avaliação de ML, benchmark estatístico do motor C, testes de navegação ponta a ponta no frontend e o roteiro de demonstração para a banca.

**Situação real da sprint nesta data:** nenhum dos PRs de código da Sprint 09 está mesclado na `main`. O PR #100 (ML) e o PR #101 (frontend E2E) estão em revisão; o PR 2 (benchmark C) não foi aberto; este relatório corresponde ao PR 4, também não aberto. Portanto, este documento separa explicitamente o que está **em revisão**, o que está **pendente** e o que é apenas **planejado**, sem declarar entrega concluída.

A base estável permanece a `main` no commit `98e7578` (fechamento documental da Sprint 08). Os números oficiais de teste, cobertura e build da Sprint 09 somente poderão ser registrados após o merge e a execução do job da `main`, conforme a seção 9.6.

### 9.1.1 Atendimento às Devolutivas das Sprints 05 e 06

A tabela abaixo reproduz as exigências da seção 2 da `SPEC-009` e registra, para cada item, o que está comprovado hoje no repositório. Nenhum item é declarado resolvido sem evidência de merge ou de execução oficial.

| Devolutiva / Origem | Exigência Formal da Banca | Status Comprovado Hoje |
| :--- | :--- | :--- |
| **Sprint 05 (Motor C)** | Deixar explícito se o algoritmo é heurístico ou se garante solução ótima global. | [PREENCHER: formalização da heurística em `motor_alocacao.h` e na documentação, prevista no PR 2, que não está aberto]. A busca por caracterização de heurística no diretório `backend/motor_alocacao` na `main` não retornou resultado. |
| **Sprint 05 (Motor C)** | Incluir média, desvio padrão e configuração completa do ambiente de benchmark para reprodutibilidade. | [PREENCHER: benchmark do PR 2 com N=10, média, desvio padrão, coeficiente de variação e ambiente]. O PR 2 não está aberto. |
| **Sprint 05 (Motor C)** | Vincular cada bug corrigido ao respectivo teste de regressão e PR/Issue. | [PREENCHER: matriz consolidada de rastreabilidade bug x teste x PR/Issue, prevista no PR 2, que não está aberto]. |
| **Sprint 05 (Geral)** | Manter o padrão de identificação do Grupo 31, integrantes e Sprints anteriores. | Atendida neste relatório: o cabeçalho, a tabela de integrantes e a identificação seguem `.agent/rules/academic-deliverables.md`, sem nome de instituição, faculdade, universidade ou cidade. |
| **Sprint 06 (IA Preditiva)** | Apresentar métricas quantitativas de ML comprovando se as previsões são adequadas. | Pendente de merge (#100). O pipeline de avaliação está na branch `feat/ml-metrics-pipeline` (commit `e9b74f4`), ainda não mesclada. A execução oficial em dataset real permanece [PREENCHER: execução oficial em dataset real]. |
| **Sprint 06 (IA Preditiva)** | Justificar tecnicamente o limiar de 40% de absenteísmo para remanejamento. | Pendente de merge (#100). A análise de sensibilidade de limiar está implementada na mesma branch, mas não mesclada. A justificativa numérica depende de [PREENCHER: execução oficial em dataset real]. |
| **Sprint 06 (Sistema)** | Preparar demonstração completa do fluxo do sistema para a banca. | Atendida neste relatório na seção 9.7.2, com roteiro de 5 etapas e tempos da História 4 da `SPEC-009`. |

---

## 9.2 Backend

Nenhuma alteração de backend da Sprint 09 está na `main`. O único PR de backend em revisão é o #100, e o PR 2 (benchmark C) não foi aberto. Portanto, esta seção descreve o que existe na branch do PR #100 e registra o que ainda não existe.

### 9.2.1 Pipeline de Avaliação de ML (PR #100, em revisão)

O PR #100, branch `feat/ml-metrics-pipeline` no commit `e9b74f4`, adiciona:

- `backend/app/services/ml_evaluator.py`, com `avaliar_classificacao()` em `backend/app/services/ml_evaluator.py:24`, que calcula matriz de confusão, acurácia, precisão, recall, F1-Score, ROC-AUC, Brier Score, total de amostras e taxas de positivos real e predita.
- `analisar_sensibilidade_limiar()` em `backend/app/services/ml_evaluator.py:96`, com limiar recomendado padrão de 0,40 em `backend/app/services/ml_evaluator.py:100` e varredura de limiares de 0,10 a 0,90 em `backend/app/services/ml_evaluator.py:115`.
- `backend/scripts/evaluate_model.py`, com o entrypoint `main()` em `backend/scripts/evaluate_model.py:29` e partição de teste padrão de 0,20 em `backend/scripts/evaluate_model.py:55`.
- `backend/tests/test_ml_evaluation.py`, com oito funções de teste declaradas (linhas 33, 59, 80, 93, 109, 129, 150 e 167).
- Relatórios gerados `backend/app/ml/relatorio_metricas_ml.json` e `backend/app/ml/relatorio_metricas_ml.md`.

O pipeline é de avaliação e leitura de métricas. O diff do PR #100 não lista routers nem endpoints.

Ressalva obrigatória: o arquivo JSON versionado na branch registra `"total_amostras": 2` em `backend/app/ml/relatorio_metricas_ml.json:15`. Esse valor é insuficiente para inferência estatística e **não é usado como métrica oficial** neste relatório.

### 9.2.2 Benchmark Estatístico do Motor C (PR 2, não aberto)

O PR 2, previsto para formalizar a heurística construtiva e executar N=10 repetições por carga, não foi aberto. Não há branch remota correspondente. Consequentemente, não existe hoje, no repositório, harness estatístico, tabela de média e desvio padrão ou registro de ambiente de hardware da Sprint 09. O que existe é apenas o benchmark antigo da Sprint 06, referenciado na seção 9.6.1.

---

## 9.3 Banco de Dados e Migrations

A Sprint 09 **não introduziu alterações de schema até o momento**. A verificação por `git diff --name-only origin/main..<branch>` nos dois PRs de código em revisão não lista nenhum arquivo em `backend/alembic/versions/`:

- PR #100: `backend/app/ml/relatorio_metricas_ml.json`, `backend/app/ml/relatorio_metricas_ml.md`, `backend/app/services/ml_evaluator.py`, `backend/scripts/evaluate_model.py`, `backend/tests/test_ml_evaluation.py`, `docs/entregas/Grupo31_SIGAAS_Sprints01-07.pdf` e `docs/specs/sprint9-testes-completos.md`.
- PR #101: `frontend/src/app/pages/admin/admin.component.ts` e `frontend/src/app/pages/integration-flow.spec.ts`.

Consequências:

- Nenhuma migration nova foi necessária.
- Nenhuma tabela, coluna, índice ou constraint foi criada ou removida.
- O modelo relacional da Sprint 07 permanece válido e é reutilizado integralmente.
- A trilha de auditoria continua usando a tabela `LogAlocacao` já existente.

---

## 9.4 Frontend

Nenhuma alteração de frontend da Sprint 09 está na `main`. O único PR de frontend em revisão é o #101, branch `feat/frontend-e2e-navigation` no commit `e4baf56`, com dois arquivos alterados: `frontend/src/app/pages/integration-flow.spec.ts` (259 linhas adicionadas) e `frontend/src/app/pages/admin/admin.component.ts` (19 adições e 13 remoções, 32 linhas no total).

### 9.4.1 Suíte de Integração do Golden Path (PR #101, em revisão)

O arquivo `frontend/src/app/pages/integration-flow.spec.ts` declara o bloco `Sprint 09 - Integracao E2E (Golden Path), Isolamento de Perfis e Coerencia de Metricas` e cobre três cenários:

1. Golden Path completo: Login, Grade, Alocação OpenMP, notificação de IA, aprovação humana pela Coordenação, reflexo na grade docente e discente e Dashboard.
2. Navegação isolada, bloqueio de rotas, redirecionamento e banner de acesso restrito para os cinco perfis.
3. Estados vazios (empty states) e feedback visual de loading e erro nas abas do sistema.

O ajuste em `admin.component.ts` alinha os cards de benchmark e speedup ao payload da API, conforme o Cenário 3.1 da `SPEC-009`.

Enquanto o PR #101 não for mesclado, esses testes não fazem parte da suíte executada pela `main`. Não há resultado oficial de execução da Sprint 09 para registrar.

---

## 9.5 Evidências Visuais

Não foram adicionadas novas capturas de tela em `docs/entregas/images/` para a Sprint 09. O diretório contém as 22 figuras das sprints anteriores, de `print_01_login.png` a `print_22_banner_acesso_restrito.png`, e nenhuma figura nova.

[PREENCHER: prints da Sprint 09, a partir da Figura 23]

Não foram criadas figuras, imagens ou referências a arquivos inexistentes neste relatório.

---

## 9.6 Testes e Métricas

### 9.6.1 Rigor Estatístico do Motor C

A tabela exigida pela História 2 da `SPEC-009` depende do benchmark do PR 2, que não está aberto. Todas as células ficam pendentes até a execução oficial.

| Carga (turmas) | N | Média seq. (ms) | Desvio seq. (ms) | Média par. (ms) | Desvio par. (ms) | Speedup | CV |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 10 | 10 | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] |
| 50 | 10 | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] |
| 100 | 10 | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] |
| 500 | 10 | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] | [PREENCHER: dado do benchmark do PR 2] |

### 9.6.2 Ambiente de Benchmark

| Item | Valor |
| :--- | :--- |
| Modelo de CPU | [PREENCHER: dado do benchmark do PR 2] |
| Frequência (clock) | [PREENCHER: dado do benchmark do PR 2] |
| Núcleos físicos | [PREENCHER: dado do benchmark do PR 2] |
| Núcleos lógicos | [PREENCHER: dado do benchmark do PR 2] |
| Memória RAM | [PREENCHER: dado do benchmark do PR 2] |
| Sistema operacional | [PREENCHER: dado do benchmark do PR 2] |
| Compilador e flags | [PREENCHER: dado do benchmark do PR 2] |

### 9.6.3 Única Fonte Atual de Benchmark

A única fonte de benchmark disponível hoje no repositório é a tabela de `docs/entregas/relatorio-sprint06.md`, linhas 991 a 1005. Essa tabela registra **medições únicas**, sem desvio padrão e sem coeficiente de variação, nas cargas 20 x 10, 100 x 40 e 500 x 150, com 1, 2, 4 e 8 threads. Ela não substitui o protocolo N=10 por carga de 10, 50, 100 e 500 turmas exigido na Sprint 09, e não informa modelo de CPU, clock, núcleos, RAM ou SO.

### 9.6.4 Métricas de ML

A tabela oficial depende de execução em dataset real. O arquivo JSON da branch do PR #100 tem apenas 2 amostras e não é usado como métrica oficial.

| Métrica | Valor |
| :--- | :--- |
| Acurácia | [PREENCHER: execução oficial em dataset real] |
| Precisão | [PREENCHER: execução oficial em dataset real] |
| Recall | [PREENCHER: execução oficial em dataset real] |
| F1-Score | [PREENCHER: execução oficial em dataset real] |
| AUC-ROC | [PREENCHER: execução oficial em dataset real] |
| Brier Score | [PREENCHER: execução oficial em dataset real] |
| Total de amostras | [PREENCHER: execução oficial em dataset real] |
| Threshold operacional de 40% | [PREENCHER: execução oficial em dataset real] |

Nota: o relatório `backend/app/ml/relatorio_metricas_ml.json` da branch do PR #100 tem `total_amostras = 2` (linha 15) e, por isso, **não é usado como métrica oficial**.

### 9.6.5 Suítes Oficiais de Backend e Frontend

Não há log oficial da Sprint 09 na `main`, pois os PRs de código não foram mesclados.

| Camada | Resultado |
| :--- | :--- |
| Backend (Pytest) | [PREENCHER: log do job da main apos o merge] |
| Frontend (Karma/Jasmine) | [PREENCHER: log do job da main apos o merge] |

Não são declarados totais de testes aprovados, percentual de cobertura ou build sem erros enquanto não existir o log correspondente do job da `main`.

---

## 9.7 Governança Ágil e Gestão de Tarefas

### 9.7.1 Estado dos Pull Requests da Sprint 09

O estado foi confirmado com `git fetch --all` e `git branch -r`. As branches do PR #100 e do PR #101 existem em `upstream` e estão um commit à frente de `origin/main`; não há branch remota de benchmark nem branch remota deste relatório. A CLI `gh` não está disponível neste ambiente, portanto o estado de revisão foi inferido pela existência da branch e pela ausência do commit na `main`, não por consulta à API do GitHub.

| PR | Branch | Commit | Escopo | ID ClickUp | Situação |
| :---: | :--- | :---: | :--- | :---: | :--- |
| #100 | `feat/ml-metrics-pipeline` | `e9b74f4` | Avaliação de métricas de ML e sensibilidade do limiar de 40% | `#86e3y38a2` | em revisão (#100) |
| #101 | `feat/frontend-e2e-navigation` | `e4baf56` | Testes E2E do golden path e coerência de métricas no frontend | `#86e3y38ak` | em revisão (#101) |
| PR 2 | sem branch remota | - | Benchmark estatístico do motor C, heurística e ambiente | `#86e3y38aa` | não aberto |
| PR 4 | `docs/sprint09-relatorio` (somente local) | sem remoto | Este relatório da Sprint 09 | `#86e3y38ay` | não aberto |

Os identificadores do ClickUp acima são os registrados na `SPEC-009`. Não foram inventados nem atualizados por consulta à API.

### 9.7.2 Roteiro Oficial de Demonstração para a Banca

O roteiro segue a História 4 da `SPEC-009`, com cinco etapas e duração total de 12 minutos: 2, 3, 3, 2 e 2 minutos, respectivamente.

#### Pre-requisitos e credenciais de teste

As credenciais abaixo são exclusivamente as do script de seed. O `README.md` não contém usuários nem senhas de teste; a senha comum está em `scripts/seed_db.py:31` e os usuários em `scripts/seed_db.py:46` a `scripts/seed_db.py:54`. A senha não foi reproduzida de outra fonte.

| Perfil | E-mail | Senha | Origem |
| :--- | :--- | :--- | :--- |
| Admin | `admin@sigaas.edu` | `sigaas123` | `scripts/seed_db.py:31` e `scripts/seed_db.py:46` |
| Coordenação | `coord.cc@sigaas.edu` | `sigaas123` | `scripts/seed_db.py:31` e `scripts/seed_db.py:47` |
| Professor | `professor@sigaas.edu` | `sigaas123` | `scripts/seed_db.py:31` e `scripts/seed_db.py:49` |
| Aluno | `aluno@sigaas.edu` | `sigaas123` | `scripts/seed_db.py:31` e `scripts/seed_db.py:52` |
| Secretaria | `secretaria@sigaas.edu` | `sigaas123` | `scripts/seed_db.py:31` e `scripts/seed_db.py:54` |

Comandos de apoio e endereços locais:

```bash
# Subir a stack e popular o banco (Makefile:16; README.md:46)
make setup

# Verificar o estado dos containers
make ps

# Contingencia sem apagar dados: aplicar migracoes e repetir o seed idempotente
make migrate
make seed
```

- Frontend: `http://localhost:4200` (mapeamento `4200:80` em `docker/compose/docker-compose.local.yml:57`).
- Documentação interativa da API: `http://localhost:8000/docs` (mapeamento `8000:8000` em `docker/compose/docker-compose.local.yml:41`).
- Atenção: `make reset` executa `docker compose down -v` e apaga o volume de dados; está documentado em `README.md:72` e `README.md:73`. Não usar durante a apresentação.

#### Etapa 1 - Visão Geral e Arquitetura Multi-Campus (2 minutos)

1. Abrir `http://localhost:4200` e autenticar com `admin@sigaas.edu` / `sigaas123`.
2. No menu lateral, abrir `Dashboard` (`frontend/src/app/layout/shell/shell.component.ts:124`).
3. Apresentar os indicadores consolidados e explicar a separação por campus e por perfil.
4. Abrir o menu `Administracao` (`frontend/src/app/layout/shell/shell.component.ts:40`) e percorrer as abas `Salas & Espacos` (`frontend/src/app/pages/admin/admin.component.ts:30`), `Equipamentos` (`frontend/src/app/pages/admin/admin.component.ts:31`), `Alocacao Inteligente` (`frontend/src/app/pages/admin/admin.component.ts:32`), `Remanejamento IA` (`frontend/src/app/pages/admin/admin.component.ts:34`) e `Resumo & Metricas` (`frontend/src/app/pages/admin/admin.component.ts:39`).

#### Etapa 2 - Motor de Alocação C/OpenMP com Evidência de Speedup (3 minutos)

1. Em `Administracao`, selecionar a aba `Alocacao Inteligente` (`frontend/src/app/pages/admin/admin.component.ts:32`).
2. Preencher `Periodo Letivo` (`frontend/src/app/pages/admin/admin.component.ts:161`) com `2026.1` (`frontend/src/app/pages/admin/admin.component.ts:441`) e escolher a quantidade de threads no seletor `Threads OpenMP` (`frontend/src/app/pages/admin/admin.component.ts:165`).
3. Clicar em `Executar Alocacao Inteligente` (`frontend/src/app/pages/admin/admin.component.ts:180`).
4. Exibir o card `Speedup OpenMP` (`frontend/src/app/pages/admin/admin.component.ts:195`) e os demais cards de métricas retornados pela execução.
5. Opcionalmente, clicar em `Benchmark Cientifico` (`frontend/src/app/pages/admin/admin.component.ts:183`) para exibir a execução de benchmark.
6. Reforçar que os valores exibidos são os do payload da API e não números fixos de tela.

#### Etapa 3 - Previsão de Falta com IA e Human-in-the-Loop (3 minutos)

1. Em `Administracao`, selecionar a aba `Remanejamento IA` (`frontend/src/app/pages/admin/admin.component.ts:34`).
2. Clicar em `Executar Analise IA` (`frontend/src/app/pages/admin/admin.component.ts:272`).
3. Manter o filtro `Pendentes` (`frontend/src/app/pages/admin/admin.component.ts:265`) e abrir um card de sugestão.
4. Mostrar o badge de sugestões pendentes e explicar que a IA apenas grava `SugestaoRemanejamento` com status `pendente`.
5. Clicar em `Aprovar Troca` (`frontend/src/app/pages/admin/admin.component.ts:370`) para demonstrar a decisão humana obrigatória.
6. Se houver mais de uma sugestão, usar `Rejeitar` (`frontend/src/app/pages/admin/admin.component.ts:374`) em outra para evidenciar o fluxo alternativo.

#### Etapa 4 - Impacto em Tempo Real na Grade de Professores e Alunos (2 minutos)

1. Encerrar a sessão do Admin e autenticar com `professor@sigaas.edu` / `sigaas123`.
2. Abrir a grade horária do docente e apresentar as aulas do período.
3. Encerrar a sessão e autenticar com `aluno@sigaas.edu` / `sigaas123`.
4. Abrir a grade do discente e apresentar os horários e as matrículas.
5. Relacionar a grade exibida à sugestão aprovada na Etapa 3.
6. Nota: o reflexo da aprovação na grade depende do PR #101, ainda não mesclado; validar no sistema antes da banca.

#### Etapa 5 - Trilha de Auditoria e Relatórios em Streaming CSV (2 minutos)

1. Autenticar com um perfil autorizado (`admin@sigaas.edu` ou `coord.cc@sigaas.edu`).
2. No menu lateral, abrir `Relatorios` (`frontend/src/app/layout/shell/shell.component.ts:143`).
3. Selecionar o período e clicar em `Exportar CSV` (`frontend/src/app/pages/relatorios/relatorios.component.ts:25`).
4. Abrir `Historico` (`frontend/src/app/layout/shell/shell.component.ts:164`) e apresentar a trilha de eventos de criação, alteração, alocação e remanejamento.
5. Encerrar a demonstração reforçando o isolamento multi-campus e o registro de auditoria.

---

## 9.8 Conclusão e Próximos Passos

A Sprint 09 está em fase de homologação, não de entrega concluída. O PR #100 e o PR #101 estão em revisão e não foram mesclados; o PR 2 não foi aberto; este relatório (PR 4) também não foi aberto. Por isso, o documento mantém como pendentes as métricas de ML, o benchmark estatístico do motor C, o ambiente de hardware, os logs oficiais de backend e frontend e as capturas de tela da Sprint 09.

O que está comprovado nesta data é o diagnóstico das devolutivas, a existência do pipeline de avaliação de ML na branch do PR #100, a existência da suíte E2E na branch do PR #101, a ausência de alterações de schema nos dois PRs e o roteiro de demonstração da seção 9.7.2.

Próximos passos, em ordem de dependência:

1. Concluir a revisão e mesclar o PR #100 (métricas de ML e limiar de 40%).
2. Abrir o PR 2, executar o benchmark N=10 e preencher as tabelas de 9.6.1 e 9.6.2.
3. Executar a avaliação de ML em dataset real e preencher a tabela de 9.6.4.
4. Concluir a revisão e mesclar o PR #101 (suíte E2E do frontend).
5. Capturar as evidências visuais da Sprint 09 a partir da Figura 23 e preencher a seção 9.5.
6. Registrar os logs oficiais dos jobs da `main` após os merges e preencher a seção 9.6.5.
7. Abrir este relatório como PR 4, submetê-lo ao debate adversarial e ao Gate 2.
8. Publicar a tag da Sprint 09 somente após o merge e a aprovação do Gate 2.
