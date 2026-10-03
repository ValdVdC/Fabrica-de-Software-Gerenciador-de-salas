# [SPEC-005] Motor de Alocação de Salas em C com Paralelismo OpenMP e Integração FastAPI

- **Sprint:** Sprint 05 — Segundo Módulo Funcional
- **Autor / Agente:** Planner-SDD (Antigravity) & Squad SIGAAS
- **Status:** Em Revisão (Aguardando Gate 1)
- **Data de Criação:** 2026-10-02
- **ID ClickUp (Épico/Task):** #CU-SPRINT05-MOTOR-C-OPENMP

---

## 1. Contexto e Objetivos

O projeto SIGAAS (Sistema Inteligente de Gestão Acadêmica e Alocação de Salas) tem como objetivo principal a alocação otimizada e livre de conflitos de espaços físicos universitários para turmas semestrais. Na Sprint 04, foi consolidado o Primeiro Módulo Completo (gestão de infraestrutura, salas, equipamentos, cursos, turmas, matrículas e visualização de grade horária).

A **Sprint 05** representa a entrega do **Segundo Módulo Funcional**, cujo núcleo técnico é o **Motor de Alocação de Salas em C com Paralelismo OpenMP**, integrado diretamente ao FastAPI via `ctypes` e persistido no PostgreSQL 16.

### Objetivos Específicos:
1. **Algoritmo Combinatório de Alocação em C**:
   - Implementar algoritmo com heurística *Best-Fit* para minimizar a ociosidade de carteiras/espaço físico nas salas (`desperdicio = capacidade_sala - num_matriculados`).
   - Garantir 100% de respeito às restrições rígidas (*hard constraints*):
     - Capacidade: `capacidade_sala >= num_matriculados`.
     - Tipo de sala: disciplinas com exigência de laboratório devem ser alocadas exclusivamente em salas do tipo `LABORATORIO`.
     - Compatibilidade de turno: a sala deve estar disponível no turno da turma (`matutino`, `vespertino`, `noturno`).
     - Não-sobreposição temporal: nenhuma sala pode ter mais de uma turma alocada no mesmo dia da semana e faixa horária.
2. **Paralelismo com OpenMP & Métricas Científicas**:
   - Paralelizar o espaço de busca combinatório entre threads OpenMP utilizando `#pragma omp parallel for`.
   - Medir tempos de execução com precisão de microssegundos via `omp_get_wtime()`.
   - Calcular experimentalmente:
     - Speedup: $S_k = \frac{T_s}{T_p(k)}$ para $k \in \{1, 2, 4, 8\}$ threads.
     - Eficiência Computacional: $E_k = \frac{S_k}{k} \times 100\%$.
     - Fração Paralelizável Teórica via Lei de Amdahl: $f = \frac{k(S_k - 1)}{S_k(k - 1)}$.
   - Avaliar 3 cenários de carga de benchmark:
     - Pequeno (Funcional): 20 turmas $\times$ 10 salas.
     - Médio (Operacional): 100 turmas $\times$ 40 salas.
     - Stress (Escala Computacional): 500 turmas $\times$ 150 salas.
3. **Ponte FFI Segura (`ctypes`) no FastAPI**:
   - Comunicação estrita com structs C 64-bit alinhadas na memória.
   - Gerenciamento explícito do ciclo de vida da memória (alocação e desalocação de buffers).
4. **Persistência Atômica no PostgreSQL**:
   - Transação atômica que grava os horários gerados na tabela `horario`.
   - Registro de trilha de auditoria na tabela `log_alocacao` com tipo `CRIACAO` e detalhes da execução paralela (tempo, threads e speedup).
5. **Interface Gráfica Angular (Painel de Alocação Inteligente)**:
   - Aba operacional no painel administrativo permitindo selecionar o número de threads e acionar a otimização com feedback em tempo real.
   - Exibição de cards com os indicadores científicos (tempo sequencial, tempo paralelo, speedup, taxa de sucesso na alocação) e visualização imediata da grade resultante.
6. **Atendimento Integral às Devolutivas da Banca**:
   - Padronização formal do dia da semana (ISO 8601: `0 = Segunda-feira` a `6 = Domingo`).
   - Evidência real do versionamento distribuído da equipe (tabela de commits com autores reais, datas e Conventional Commits).

---

## 2. Histórias de Usuário

### História 1: Alocação Automática de Salas pelo Administrador / Coordenador
> **Como** Coordenador ou Administrador do Campus  
> **Quero** acionar o algoritmo de alocação de salas para as turmas semestrais pendentes  
> **Para que** todas as turmas recebam salas compatíveis com sua capacidade e tipo sem conflitos de horário e sem trabalho manual repetitivo.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Alocação bem-sucedida de turmas em lote
  Dado que existem 10 turmas cadastradas para o período letivo 2026.1 sem horário atribuído
  E existem 5 salas ativas com capacidade e turnos compatíveis no campus
  Quando o Coordenador submeter a requisição POST /api/v1/alocacao/otimizar com max_threads=4
  Então a resposta HTTP deve retornar status 200 OK
  E o corpo da resposta deve conter o array de horários alocados, tempo_ms, threads_usadas=4 e speedup
  E os horários devem ser persistidos no PostgreSQL na tabela horario
  E um registro de auditoria deve ser gerado na tabela log_alocacao

Cenário: Bloqueio de alocação por usuário não autorizado
  Dado que um usuário autenticado possui perfil de Docente ou Discente
  Quando tentar acessar o endpoint POST /api/v1/alocacao/otimizar
  Então a API deve retornar HTTP 403 Forbidden
```

### História 2: Coleta de Métricas Científicas de Speedup OpenMP
> **Como** Professor avaliador da disciplina de Tópicos Avançados / Fábrica de Software  
> **Quero** visualizar a comparação experimental entre o tempo sequencial (1 thread) e paralelo (2, 4 e 8 threads)  
> **Para que** seja comprovado o ganho de desempenho computacional e a aderência à Lei de Amdahl.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Execução do benchmark comparativo sequencial vs paralelo
  Dado um cenário de carga sintético com 100 turmas e 40 salas
  Quando for disparada a rotina de benchmark científico
  Então o sistema deve medir o tempo de execução com 1, 2, 4 e 8 threads
  E o speedup calculado deve ser estritamente maior que 1.0x para 2 e 4 threads em cenários médios e de stress
  E as métricas devem ser formatadas com tempo_seq_ms, tempo_par_ms, speedup, eficiencia e fracao_amdahl
```

---

## 3. Arquitetura e Contratos Técnicos

### 3.1 Contrato FFI em C (`backend/motor_alocacao/motor.h`)

```c
#ifndef MOTOR_ALOCACAO_H
#define MOTOR_ALOCACAO_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int id;
    int capacidade;
    int tipo; // 0 = REGULAR, 1 = LABORATORIO, 2 = AUDITORIO, 3 = REUNIAO
    int turnos_mask; // Bitmask: 1=matutino, 2=vespertino, 4=noturno, 8=integral
} SalaC;

typedef struct {
    int id;
    int num_matriculados;
    int tipo_exigido; // 0 = REGULAR, 1 = LABORATORIO
    int turno; // 0=matutino, 1=vespertino, 2=noturno, 3=integral
    int dia_semana_sugerido; // 0 a 6
    int hora_inicio_min; // Ex: 480 (08:00)
    int hora_fim_min;    // Ex: 600 (10:00)
} TurmaC;

typedef struct {
    int turma_id;
    int sala_id;
    int dia_semana;
    int hora_inicio_min;
    int hora_fim_min;
    int score_desperdicio;
} AlocacaoItemC;

typedef struct {
    double tempo_sequencial_ms;
    double tempo_paralelo_ms;
    double speedup;
    double eficiencia;
    double fracao_amdahl;
    int threads_utilizadas;
    int total_alocado;
    int total_pendente;
} MetricasAlocacaoC;

// Otimiza a alocação combinatória com OpenMP
int otimizar_alocacao_salas(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    int max_threads,
    AlocacaoItemC* resultado_out,
    MetricasAlocacaoC* metricas_out
);

// Retorna a versão e status do motor C
const char* obter_versao_motor(void);

#ifdef __cplusplus
}
#endif

#endif // MOTOR_ALOCACAO_H
```

### 3.2 Endpoints FastAPI

- `POST /api/v1/alocacao/otimizar`:
  - **Permissão**: Admin ou Coordenador do Campus.
  - **Body**:
    ```json
    {
      "periodo_letivo": "2026.1",
      "campus_id": 1,
      "max_threads": 4,
      "salvar_no_banco": true
    }
    ```
  - **Response (200 OK)**:
    ```json
    {
      "sucesso": true,
      "mensagem": "Alocação executada com sucesso.",
      "metricas": {
        "tempo_sequencial_ms": 14.82,
        "tempo_paralelo_ms": 4.51,
        "speedup": 3.28,
        "eficiencia_pct": 82.0,
        "fracao_amdahl": 0.92,
        "threads": 4,
        "total_turmas": 45,
        "alocadas": 45,
        "conflitos": 0
      },
      "alocacoes": [
        {
          "turma_id": 12,
          "disciplina_codigo": "CC101",
          "disciplina_nome": "Algoritmos e Estruturas de Dados I",
          "sala_id": 3,
          "sala_bloco": "Bloco A",
          "sala_numero": "101",
          "dia_semana": 0,
          "hora_inicio": "08:00",
          "hora_fim": "10:00"
        }
      ]
    }
    ```

- `POST /api/v1/alocacao/benchmark`:
  - Executa a bateria científica de testes nos 3 cenários (Pequeno, Médio, Stress) para geração das tabelas e gráficos comparativos do relatório acadêmico.

### 3.3 Modelo de Dados e Integridade

- Utiliza as tabelas existentes `horario` e `log_alocacao`.
- Nenhuma migration de schema destrutiva é necessária; as colunas e restrições `CHECK (hora_inicio < hora_fim)` e `CHECK (dia_semana BETWEEN 0 AND 6)` já atendem perfeitamente.
- O campo `dia_semana` no PostgreSQL adota a convenção padronizada:
  - `0`: Segunda-feira
  - `1`: Terça-feira
  - `2`: Quarta-feira
  - `3`: Quinta-feira
  - `4`: Sexta-feira
  - `5`: Sábado
  - `6`: Domingo

---

## 4. Plano de Testes TDD (Test-Driven Development)

### 4.1 Testes Unitários e de Integração (Fase RED)
- [ ] `backend/tests/test_motor_c.py::test_versao_motor_c`: verifica carregamento da DLL/SO e string de versão com OpenMP.
- [ ] `backend/tests/test_motor_c.py::test_alocacao_best_fit`: valida escolha da menor sala com capacidade suficiente.
- [ ] `backend/tests/test_motor_c.py::test_bloqueio_sala_lotada`: valida que turma com 60 alunos não é alocada em sala de 40 alunos.
- [ ] `backend/tests/test_motor_c.py::test_incompatibilidade_laboratorio`: valida que turma de laboratório não é alocada em sala regular.
- [ ] `backend/tests/test_motor_c.py::test_incompatibilidade_turno`: valida rejeição de sala indisponível no turno da turma.
- [ ] `backend/tests/test_motor_c.py::test_speedup_concorrente`: valida cálculo de Speedup > 1.0x em cenário com carga suficiente.
- [ ] `backend/tests/test_api_alocacao.py::test_endpoint_otimizar_sucesso`: valida `POST /api/v1/alocacao/otimizar` com persistência no banco.
- [ ] `backend/tests/test_api_alocacao.py::test_endpoint_otimizar_permissao`: valida bloqueio de perfil não-autorizado (403).

### 4.2 Critérios de Conclusão TDD (Fase GREEN + REFACTOR)
- [ ] Todos os testes passando com 100% de sucesso.
- [ ] Cobertura de testes do backend mantida $\ge 85\%$.
- [ ] Compilação do motor C livre de warnings com `-Wall -Wextra -Werror -pedantic`.

---

## 5. Decomposição de Tarefas (Fatiamento em PRs $\le 400$ linhas)

1. **Subtarefa 1 (Motor C + OpenMP)**:
   - Implementação de `motor.c`, `motor.h`, `benchmark.c` e Makefile de compilação.
   - Testes unitários do algoritmo em C puro e medições de Speedup.
2. **Subtarefa 2 (Ponte ctypes + Endpoint FastAPI + Persistência PostgreSQL)**:
   - Atualização de `motor_service.py` e criação de `endpoints/alocacao.py`.
   - Suíte de testes Pytest cobrindo alocação e persistência atômica.
3. **Subtarefa 3 (Frontend Angular - Painel de Alocação e Speedup)**:
   - Componente de alocação inteligente em `frontend/src/app/pages/admin/` ou rota dedicada.
   - Visualização de cards de Speedup, tempo e matriz de horários alocados.
   - Testes unitários no Karma/Jasmine.
4. **Subtarefa 4 (Documentação e Relatório Unificado Sprint 01-05)**:
   - Elaboração da `PARTE 5` em `docs/entregas/relatorio-sprint05.md`.
   - Histórico oficial de commits com autores e datas da Sprint.
   - Geração do PDF oficial: `docs/entregas/Grupo31_SIGAAS_Sprints01-05.pdf`.
