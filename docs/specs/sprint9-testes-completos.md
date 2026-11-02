# [SPEC-009] Homologação, Testes Completos e Atendimento às Devolutivas da Banca

- **Sprint:** Sprint 09 — Testes Completos
- **Autores / Papéis:** Wesclei Batista (Product Owner), Ewerton Thyago (Scrum Master) & Squad SIGAAS
- **Status:** Proposta para Aprovação (Gate 1 em 2026-11-02)
- **Data de Criação:** 2026-11-02
- **Prazo de Entrega Acadêmica:** 2026-11-07 às 23:59
- **IDs ClickUp (Tasks da Sprint 09):**
  - PR 1 (Backend ML Evaluator & Regressão): `#86e3y38a2`
  - PR 2 (Backend HPC C Benchmark & Heurística): `#86e3y38aa`
  - PR 3 (Frontend E2E Navigation & Coerência Visual): `#86e3y38ak`
  - PR 4 (Pacote Acadêmico, Roteiro Banca & PDF Oficial): `#86e3y38ay`

---

## 1. Contexto e Objetivos

Com a conclusão da Sprint 08, o SIGAAS alcançou o marco de **Sistema Praticamente Concluído**:
- Todas as entidades acadêmicas possuem ciclo de vida completo (criação, edição, cancelamento atômico e inativação).
- As permissões hierárquicas (RBAC) e o isolamento multi-campus mitigam integralmente os riscos OWASP API Top 10 (especificamente BFLA e BOLA/IDOR).
- O CI da branch `main` opera com 415 testes automatizados aprovados (255 backend com 91,18% de cobertura e 160 specs no frontend).

Para a **Sprint 09 (Testes Completos)**, o objetivo central deixa de ser a criação de novas entidades e passa a ser a **homologação científica e operacional da solução**, preparando o sistema para a banca examinadora e atendendo categoricamente a todas as exigências das devolutivas docentes das Sprints 05 e 06.

---

## 2. Diagnóstico e Atendimento às Devolutivas da Banca

A banca avaliadora apontou exigências precisas nas devolutivas das etapas anteriores:

| Devolutiva / Origem | Exigência Formal da Banca | Diagnóstico Atual no SIGAAS | Solução Normativa na Sprint 09 |
| :--- | :--- | :--- | :--- |
| **Sprint 05 (Motor C)** | Deixar explícito se o algoritmo é heurístico ou se garante solução ótima global. | O código C aplica alocação gulosa, mas o relatório e o cabeçalho não continham a formalização matemática como heurística construtiva determinística. | Formalizar formalmente em `motor_alocacao.h` e na documentação que o Timetabling é NP-difícil e o motor é uma heurística construtiva com restrições rígidas (sem garantia de ótimo global). |
| **Sprint 05 (Motor C)** | Incluir média ($\mu$), desvio padrão ($\sigma$) e configuração completa do ambiente de benchmark para reprodutibilidade. | Os benchmarks anteriores mediram 1 execução por carga (10, 50, 100, 500 turmas) sem dispersão estatística nem especificação do processador/clock. | Criar script runner automatizado executando $N=10$ repetições para cada carga, calculando média, desvio padrão e coeficiente de variação ($CV$), com registro completo de hardware e SO. |
| **Sprint 05 (Motor C)** | Vincular cada bug corrigido ao respectivo teste de regressão e PR/Issue. | Bugs de bounds e compilação foram corrigidos ao longo das sprints, mas sem uma matriz consolidada de rastreabilidade. | Mapear formalmente os bugs históricos a testes de regressão automatizados em `tests/test_motor_ctypes.py`. |
| **Sprint 05 (Geral)** | Manter o padrão de identificação do Grupo 31, integrantes e Sprints anteriores. | Padrão elogiado e validado pela banca: Grupo 31, Ciência da Computação, Turma 8MB - CC, sem alucinações. | Manutenção estrita da regra de blindagem documental sem nomes de faculdades ou cidades não declaradas. |
| **Sprint 06 (IA Preditiva)** | Apresentar métricas quantitativas de ML comprovando se as previsões são adequadas (não apenas que o modelo executa). | O pipeline treina o `GradientBoostingClassifier` e gera sugestões, mas faltava a exibição no relatório de Matriz de Confusão, Acurácia, F1-score e ROC/AUC. | Implementar serviço/script avaliador de ML (`ml_evaluator.py`) gerando Matriz de Confusão, Precisão, Recall, F1, ROC/AUC e Brier Score (calibração probabilística). |
| **Sprint 06 (IA Preditiva)** | Justificar tecnicamente o limiar (*threshold*) de 40% de absenteísmo para remanejamento. | O limiar de 40% foi adotado de forma empírica sem demonstrar a curva de sensibilidade e trade-off operacional. | Elaborar estudo de sensibilidade documentando o trade-off entre custos de falsos positivos (trocar sala à toa) e falsos negativos (manter sala vazia). |
| **Sprint 06 (Sistema)** | Preparar demonstração completa do fluxo do sistema para a banca. | Os módulos funcionavam individualmente, mas faltava um roteiro estruturado (*golden path*) para a apresentação ao vivo. | Elaborar o *Script Oficial de Demonstração para a Banca*, cobrindo o fluxo integrado de ponta a ponta em tempo real. |

---

## 3. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Avaliação Científica do Modelo Preditivo de Absenteísmo (ML)
> **Como** comitê examinador acadêmico,  
> **Quero** inspecionar métricas formais de classificação e calibração probabilística do modelo de absenteísmo,  
> **Para** comprovar a eficácia estatística das previsões antes da emissão de sugestões de remanejamento.

#### Cenário 1.1: Geração da matriz de confusão e métricas de classificação
- **Given** o dataset histórico de frequência acadêmica particionado em treino e teste (estratificado 80/20);
- **When** o pipeline de avaliação de Machine Learning for executado;
- **Then** deve calcular e registrar:
  - Matriz de confusão (Verdadeiros Positivos, Falsos Positivos, Verdadeiros Negativos, Falsos Negativos);
  - Acurácia, Precisão, Recall e F1-Score;
  - Área sob a Curva ROC (AUC-ROC);
  - Índice de Brier para aferição da calibração probabilística;
- **And** exportar relatório estruturado em JSON e Markdown para o relatório da sprint.

#### Cenário 1.2: Justificativa formal do limiar de 40% de absenteísmo
- **Given** as probabilidades calibradas geradas pelo estimador preditivo;
- **When** for analisada a curva de trade-off de negócio (falsos positivos vs. falsos negativos);
- **Then** deve demonstrar que o limiar de 0,40 maximiza o equilíbrio operacional:
  - Evita remanejamentos precipitados em turmas com frequência moderada ($\le 39\%$);
  - Dispara a sugestão apenas quando o risco de ociosidade crítica justifica o custo de transição da turma;
- **And** confirmar que toda previsão $\ge 40\%$ gera `SugestaoRemanejamento` com status `pendente` (Human-in-the-Loop inviolável).

---

### História 2: Rigor Estatístico no Motor de Alocação em C e Formalização Teórica
> **Como** professor de Tópicos Avançados em Computação,  
> **Quero** analisar o benchmark estatístico do motor C com repetições controladas e formulação explícita do algoritmo,  
> **Para** atestar o ganho científico de desempenho paralelo via OpenMP com reprodutibilidade metodológica.

#### Cenário 2.1: Formalização da heurística construtiva determinística
- **Given** o problema combinatorial de alocação de salas e horários (NP-difícil);
- **When** for inspecionado o código-fonte em `motor_alocacao.h` e a documentação técnica;
- **Then** deve constar a caracterização teórica explícita:
  - Algoritmo baseado em **heurística construtiva gulosa com priorização de restrições rígidas** e busca de capacidade mínima viável;
  - Ausência de garantia de ótimo global, justificando a abordagem heurística pela complexidade temporal tratável em larga escala.

#### Cenário 2.2: Benchmark automatizado com média e desvio padrão
- **Given** o motor compilado com flags `-O3 -fopenmp`;
- **When** o harness de benchmark for disparado para as cargas de 10, 50, 100 e 500 turmas com $N=10$ repetições independentes;
- **Then** deve calcular e tabular para cada carga:
  - Tempo sequencial médio ($\mu_{seq}$) e desvio padrão ($\sigma_{seq}$);
  - Tempo paralelo médio ($\mu_{par}$) e desvio padrão ($\sigma_{par}$);
  - Speedup real obtido ($S = \mu_{seq} / \mu_{par}$);
  - Coeficiente de variação ($CV = \sigma / \mu$) garantindo estabilidade amostral ($CV < 15\%$);
- **And** registrar as especificações de hardware (modelo de CPU, frequência, núcleos físicos/lógicos, memória e SO).

---

### História 3: Testes de Navegação Ponta a Ponta e Coerência Visual na UI
> **Como** usuário institucional (Admin, Coordenador, Secretaria, Docente ou Aluno),  
> **Quero** vivenciar uma navegação fluida, sem divergências visuais e com dados perfeitamente consistentes,  
> **Para** executar as rotinas acadêmicas sem inconsistências entre o que o motor processa e o que a tela exibe.

#### Cenário 3.1: Coerência entre dados de benchmark e cards visuais
- **Given** os resultados do motor de alocação processados via backend;
- **When** o painel de Alocação e Dashboard for renderizado no Angular;
- **Then** os cards de tempo de execução e speedup devem exibir exatamente os valores consistentes com o payload da API;
- **And** badges de status devem refletir o estado real das entidades sem dados desatualizados em cache.

#### Cenário 3.2: Suíte de testes de integração do fluxo completo (Golden Path)
- **Given** a suíte de testes de componentes no Angular (Karma + ChromeHeadless);
- **When** forem simulados os fluxos de navegação:
  1. Autenticação e redirecionamento conforme perfil;
  2. Execução da alocação automática e exibição dos cards;
  3. Visualização e aprovação de sugestão de remanejamento pela Coordenação;
  4. Reflexo automático da nova sala na grade do Docente e do Aluno;
- **Then** todos os testes de integração devem ser aprovados com 100% de sucesso;
- **And** a interface deve exibir *empty states* limpos quando não houver dados cadastrados.

---

### História 4: Roteiro da Demonstração para a Banca e Consolidação Acadêmica
> **Como** equipe do Grupo 31 e banca examinadora,  
> **Quero** dispor de um roteiro cronometrado e objetivo para a apresentação ao vivo do sistema,  
> **Para** demonstrar todo o ciclo de vida do SIGAAS de forma clara, segura e integrada.

#### Cenário 4.1: Estruturação do Roteiro de Demonstração
- **Given** o sistema completo rodando via Docker Compose (`docker compose up`);
- **When** for seguida a sequência de apresentação para a banca:
  1. Visão Geral e Arquitetura Multi-Campus (2 minutos);
  2. Motor de Alocação C/OpenMP com evidência de speedup (3 minutos);
  3. Previsão de Falta com IA e Human-in-the-Loop na aprovação (3 minutos);
  4. Impacto em tempo real na grade de professores e alunos (2 minutos);
  5. Trilha de auditoria e relatórios em streaming CSV (2 minutos);
- **Then** o roteiro deve conter as credenciais de teste de cada perfil, os passos exatos de clique e os comandos de apoio para contingência.

---

## 4. Design de Engenharia e Arquitetura

### 4.1 Novos Componentes e Módulos

```text
c:\Work\workspace\SIGAAS
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   └── ml_evaluator.py            # Serviço de métricas estatísticas e calibração do modelo ML
│   ├── tests/
│   │   ├── test_ml_evaluation.py          # Testes unitários do pipeline de métricas e threshold
│   │   └── test_benchmark_estatistico.py  # Harness estatístico com repetições (mu, sigma)
│   └── scripts/
│       ├── evaluate_model.py              # Script CLI para geração de relatório JSON/Markdown de ML
│       └── run_benchmarks_ci.py           # Runner automatizado de benchmark estatístico C
├── frontend/
│   └── src/app/pages/
│       └── integration-flow.spec.ts       # Testes de integração do fluxo completo dos 5 perfis
└── docs/
    ├── entregas/
    │   ├── relatorio-sprint09.md          # Relatório oficial autônomo da Sprint 09
    │   └── relatorio-consolidado-sprints-01-a-09.md
    └── roteiro-apresentacao-banca.md      # Guia passo a passo da demonstração ao vivo
```

---

## 5. Plano de Fatiamento de PRs (Diff $\le 400$ Linhas)

| PR | Ramo (Branch) | Escopo e Entregáveis | Limite de Diff | Responsável |
| :---: | :--- | :--- | :---: | :--- |
| **PR 1** | `feat/ml-metrics-pipeline` | Pipeline de avaliação de métricas de ML (`ml_evaluator.py`), justificativa do limiar de 40%, testes unitários e de regressão da IA (`#86e3y38a2`). | $\le 350$ linhas | Osvaldo Vasconcelos |
| **PR 2** | `feat/c-benchmark-stats` | Formalização da heurística em `motor_alocacao.h`, harness estatístico com $N=10$ repetições ($\mu, \sigma, CV$), ambiente de hardware e testes de regressão do motor C (`#86e3y38aa`). | $\le 300$ linhas | Osvaldo Vasconcelos |
| **PR 3** | `feat/frontend-e2e-navigation` | Testes de integração do fluxo completo (*golden path* dos 5 perfis), validação de coerência visual dos cards de speedup e tratamento de empty states (`#86e3y38ak`). | $\le 350$ linhas | Gabriel Porfírio |
| **PR 4** | `docs/sprint09-relatorio-banca` | Relatório da Sprint 09 com atendimento às devolutivas, roteiro da banca, consolidação cumulativa e compilação do PDF oficial ABNT sem alucinações (`#86e3y38ay`). | Documentação | Flávio Vecch |

---

## 6. Plano de Testes TDD e Cobertura Mínima

- **Backend (Pytest):** Cobertura obrigatória $\ge 85\%$ mantida em todas as etapas, com asserções estritas para:
  - Matriz de confusão com valores não-nulos e métricas válidas no intervalo $[0, 1]$;
  - $CV < 15\%$ nas repetições de benchmark de alocação;
  - Garantia de que previsões de absenteísmo nunca realizam mutação direta na tabela `Horario`.
- **Frontend (Karma/Jasmine):** 100% de aprovação na suíte de testes de componentes e serviços.
- **Docker Smoke Test:** Inicialização do ecossistema full-stack (`db` e `app`), migrações aplicadas e testes de healthcheck e endpoints via HTTP.
