# [SPEC-M2-01] Paralelismo OpenCL no Motor de Alocação, Conflito Docente e Persistência Não-Destrutiva

- **Sprint / Marco:** Marco M2 — Evolução HPC e Integridade da Alocação (Pós-`v1.0.0-rc.1`)
- **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
- **Curso / Turma:** Curso de Bacharelado em Ciência da Computação — Turma 8MB - CC
- **Equipe:** Grupo 31 — SIGAAS (Ewerton Thyago Tavares da Silva [01573977], Wesclei Batista Da Cruz Júnior [01606772], Osvaldo Vasconcelos de Carvalho [01614171], Gabriel Porfírio dos Santos [01591399], Flávio Vecch de Brito Farias [01600988])
- **Autor / Agente:** Planner-SDD (Antigravity) & Squad SIGAAS
- **Status:** Draft — Aguardando Gate 1
- **Data de Criação:** 2026-11-27
- **ID ClickUp (Épico/Task):** `[Pendente sync]` (preenchido após `python scripts/clickup_sync.py sync-spec docs/specs/spec-motor-opencl-cuda.md`)
- **Referências Normativas:** `AGENTS.md`, `docs/projeto-gestao-salas-escalas.md`, `docs/specs/template-spec.md`, `docs/specs/sprint5-motor-alocacao-c-openmp.md`, `docs/specs/sprint12-versao-final.md`

---

## 1. Contexto e Diagnóstico Atual

### 1.1 Estado Atual Auditado

A auditoria técnica da base atual do SIGAAS comprovou que o motor de alocação opera exclusivamente em CPU via **OpenMP**, sem nenhuma implementação em **OpenCL** ou **CUDA**, além de apresentar falhas estruturais na modelagem de restrições docentes, na persistência de horários e na metodologia estatística de benchmarking. A tabela a seguir sintetiza os achados verificados por caminho e linha exata no repositório:

| Componente | Evidência Verificada (Caminho e Linhas) | Diagnóstico / Defeito Encontrado | Ação Planejada em M2 |
| :--- | :--- | :--- | :--- |
| **Motor C (Paralelismo)** | `backend/motor_alocacao/motor.c:4, 224-274, 309-336, 422`; `backend/motor_alocacao/Makefile:2-3`; `backend/app/services/motor_service.py:143` | Usa exclusivamente `<omp.h>` (`#pragma omp parallel`, `schedule(dynamic, 16)`, `omp_get_wtime()`). Busca textual em `backend/`, `frontend/`, `docker/` e `.github/` confirma zero ocorrências de OpenCL ou CUDA (`<CL/cl.h>`, `<cuda_runtime.h>`, `cl_platform`, `__global__`, `nvcc`). | Adicionar backend **OpenCL 1.2+** (`motor_opencl.{h,c}` e `kernels/alocacao.cl`) mantendo OpenMP e Sequencial com seleção explícita e fallback auditável. |
| **Struct `TurmaC` e Conflito Docente** | `backend/motor_alocacao/motor.h:32-40`; `backend/app/services/motor_service.py:87-96`; `backend/motor_alocacao/motor.c:154`; `backend/app/models/academico.py:60` | `TurmaC` possui 7 campos `int` (28 bytes, não múltiplo de 8 bytes) e omite `professor_id`, embora `Turma.professor_id` exista no ORM. `executar_tentativa` verifica apenas `sala_tem_conflito()`, permitindo que um mesmo professor seja alocado simultaneamente em duas salas. | Expandir `TurmaC` para 32 bytes (múltiplo de 8 bytes) com `int32_t professor_id` (`0` como sentinela sem docente) e checar conflito de horário do docente em C/OpenMP/OpenCL. |
| **Alocação Dinâmica no Loop Quente** | `backend/motor_alocacao/motor.c:39-53, 228-286` | `adicionar_reserva` usa `realloc` e `executar_busca_combinatoria` usa `malloc` por thread dentro das tentativas. Kernels OpenCL C 1.2 não suportam `malloc`/`realloc` no device. | Empacotar intervalos ocupados em `uint32_t` de tamanho fixo (`(dia << 22) | (ini << 11) | fim`) sobre buffers pré-alocados no host. |
| **Atribuição Sintética de Slots** | `backend/app/api/v1/endpoints/alocacao.py:185, 187-194` | `dia_sugerido = idx % 5` e faixa horária fixa única por turno (`08:00-10:00`, `14:00-16:00`, `19:00-21:00`, `08:00-12:00`), ignorando choques determinísticos entre turmas do mesmo docente e subutilizando janelas do turno. | Substituir atribuição fixa por seleção/busca multi-slot nos blocos válidos do turno e considerar `professor_id` na distribuição inicial. |
| **Cascata Destrutiva de `Horario`** | `backend/app/api/v1/endpoints/alocacao.py:295`; `backend/app/models/ia.py:27, 44, 61`; `backend/alembic/versions/001_initial_schema.py:212, 230, 251`; `backend/tests/test_api_alocacao.py:30-41` | `delete(Horario).where(Horario.turma_id.in_(turmas_ids))` aciona `ondelete="CASCADE"` em `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento` no PostgreSQL (ocultado nos testes em SQLite `:memory:` por ausência de `PRAGMA foreign_keys=ON`). | Introduzir `modo_reotimizacao` não-destrutivo (`preservar_alocados`, `atualizar_inplace`, `arquivar_historico`), colunas `Horario.ativo`/`substituido_em` e migration Alembic alterando FKs para `ondelete="RESTRICT"`. |
| **Execução Dupla e Clamping no Motor C** | `backend/motor_alocacao/motor.c:325-336, 339-340` | `otimizar_alocacao_salas` executa sempre `num_threads=1` e `threads_alvo` em produção (descartando `res_seq`) e força `t_seq_ms`/`t_par_ms >= 0.01` ms. | Expor parâmetro `medir_baseline_seq` (`0` por padrão operacional em `/otimizar`, `1` em `/benchmark` e comparação explícita) e preservar medições reais de alta resolução. |
| **Clamping Artificial no Benchmark CI** | `backend/scripts/run_benchmarks_ci.py:191, 205-212` | Comprime amostras que desviam `> 14%` da mediana para `[med * 0.88, med * 1.12]` antes de calcular desvio padrão e CV, além de usar `sub_amostras = 2` silencioso para cargas `<= 50`. | Remover clamping artificial e média oculta; registrar amostras brutas, mediana, IQR, p95, mínimo, máximo e contagem explícita de outliers IQR. |
| **Drift e Segurança de `/motor/*`** | `backend/app/api/v1/endpoints/motor.py:21-25, 34-74`; `backend/app/services/motor_service.py:213-219`; `.github/workflows/ci.yml:199, 203` | `MotorStatusResponse` omite `"heuristica"` retornada por `get_status()`, e `/motor/status` e `/motor/teste-integracao` não exigem autenticação (enquanto `ci.yml` consulta `/motor/status` sem token). | Alinhar `MotorStatusResponse` (incluindo `heuristica` e metadados OpenCL), adicionar `GET /api/v1/motor/dispositivos` e coordenar proteção JWT com o Marco M3 e atualização de `ci.yml`. |
| **Dockerfiles, CI e Sombreamento de `.so`** | `docker/backend/Dockerfile:7-9, 19`; `backend/Dockerfile:6-8, 18`; `.github/workflows/ci.yml:115`; `docker/compose/docker-compose.local.yml:43` | Ausência de `ocl-icd-opencl-dev`, `pocl-opencl-icd` e `clinfo` para compilação e execução OpenCL; em desenvolvimento local, o bind mount `../../backend:/app` sobrescreve o `motor_alocacao.so` compilado na imagem Docker. | Instalar pacotes OpenCL ICD/POCL nos Dockerfiles e CI, instalar `.so` em `/opt/sigaas/motor/` com variável `MOTOR_LIB_PATH` e criar override opcional `docker-compose.gpu.yml`. |

### 1.2 Objetivos Específicos

1. Adicionar backend paralelo heterogêneo em **OpenCL 1.2+** (`motor_opencl.{h,c}` e `kernels/alocacao.cl`) com execução determinística em GPUs compatíveis ou em CPU multicore via `pocl-opencl-icd` nos ambientes Docker e CI.
2. Preservar execução em **OpenMP** e **CPU Sequencial** com seleção explícita (`auto`, `opencl`, `openmp`, `cpu_sequencial`), fallback auditável e métricas de transferência host-device (`tempo_transferencia_ms`) e execução de kernel (`tempo_kernel_ms`).
3. Eliminar colisões de horário docente adicionando `professor_id` à struct `TurmaC` (32 bytes, alinhamento de 64 bits) e verificando conflitos de sala e professor em todos os backends.
4. Garantir persistência não-destrutiva da tabela `Horario` com proteção em banco (`ondelete="RESTRICT"` e arquivamento lógico via `Horario.ativo`), preservando integralmente `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento`.
5. Desacoplar a execução dupla obrigatória sequencial+paralela do caminho produtivo e eliminar o clamping estatístico artificial do harness de benchmark.
6. Manter estrita aderência às fronteiras arquiteturais do `AGENTS.md`, fatiamento em PRs incrementais `<= 300-400` linhas e disciplina TDD com cobertura mínima de `85%`.

---

## 2. Decisão Arquitetural: OpenCL vs. CUDA e Fronteiras Invioláveis

### 2.1 Comparativo Técnico: OpenCL vs. CUDA no Contexto SIGAAS

A escolha tecnológica deve atender simultaneamente ao requisito acadêmico de paralelismo em aceleradores (OpenCL ou CUDA, conforme registrado em `ORIGINAL_REQUEST.md`) e às restrições operacionais reais do pipeline do SIGAAS (containers `python:3.12-slim`, GitHub Actions `ubuntu-latest` sem GPU física e instâncias AWS EC2 de baixo custo `t2`/`t3` em CPU, com suporte opcional a GPU):

| Critério Técnico | OpenCL 1.2+ (`<CL/cl.h>`) | NVIDIA CUDA (`nvcc` / `cuda_runtime.h`) | Impacto no SIGAAS |
| :--- | :--- | :--- | :--- |
| **Linguagem e Toolchain do Motor** | API host em **C11 puro** (`gcc -std=c11 -O3 -fPIC -fopenmp -lOpenCL`), compatível diretamente com `motor.c` e `Makefile` atuais. | Exige compilador proprietário `nvcc` (C++/CUDA) e runtime C++ (`libcudart`), aumentando acoplamento de build. | OpenCL preserva o núcleo C11 exigido para `motor_alocacao.so`. |
| **Portabilidade de Hardware (Vendor Lock-in)** | Executa em GPUs **NVIDIA, AMD e Intel** via ICDs do fabricante e em **CPUs x86_64/ARM64** via `pocl-opencl-icd`. | Executa exclusivamente em GPUs **NVIDIA** proprietárias. | OpenCL evita lock-in de fornecedor e aproveita qualquer acelerador presente. |
| **Execução em CI (`ubuntu-latest`) e AWS EC2 `t2`/`t3`** | **Execução real do kernel `.cl`** via `ocl-icd-opencl-dev` + `pocl-opencl-icd`, validando compilação JIT, buffers e reduções em cada PR. | Sem GPU NVIDIA no runner/EC2, o binário CUDA não executa kernels reais no CI (ou exige emuladores não oficiais). | OpenCL permite testar 100% do código paralelo real no CI e na nuvem CPU. |
| **Tamanho de Imagem Docker (`python:3.12-slim`)** | Pacotes Debian leves (`ocl-icd-opencl-dev`, `pocl-opencl-icd`, `clinfo`: ~90-140 MB adicionais). | Base `nvidia/cuda` + toolkit ultrapassa vários gigabytes e requer NVIDIA Container Toolkit no host. | OpenCL mantém deploy ágil compatível com `docker-compose.prod.yml` (`memory: 1G`). |
| **Risco Operacional** | Baixo: fallback auditável automático para OpenMP quando não houver plataforma OpenCL no host. | Alto em ambientes sem driver NVIDIA instalado. | Decisão segura para entrega acadêmica contínua. |

**Decisão Arquitetural:** Adota-se **OpenCL 1.2+ (`<CL/cl.h>`) com compilação via `ocl-icd-opencl-dev`, execução CPU padrão via `pocl-opencl-icd` (e GPU automática quando houver ICD de hardware no host) e fallback auditável para OpenMP/Sequencial**. Quando um host possuir GPU NVIDIA, AMD ou Intel com driver OpenCL ICD montado via `docker-compose.gpu.yml`, o mesmo `motor_alocacao.so` executa o kernel nativamente na GPU sem recompilação.

### 2.2 Fronteiras Arquiteturais Invioláveis (`AGENTS.md` §2 e §4)

1. **Zero Regra de Negócio no Frontend Angular:** O Angular apenas envia parâmetros opcionais (`backend`, `modo_reotimizacao`, `executar_baseline_sequencial`) e exibe métricas retornadas pela API, sem cálculos combinatórios ou lógica de conflito.
2. **Motor C Isolado via `ctypes`:** A biblioteca `motor_alocacao.so` opera no mesmo processo do FastAPI sem dependências externas de rede, ORM ou conexão direta ao PostgreSQL (`AGENTS.md` §2). Todos os dados de turmas, salas e slots ocupados entram por structs C alinhadas em memória.
3. **Medição Científica Completa:** Para ensaios comparativos, benchmarks e quando `executar_baseline_sequencial=True`, o motor mede e registra $T_s$ (`tempo_sequencial_ms`), $T_p$ (`tempo_paralelo_ms`), Speedup ($S_k = \frac{T_s}{T_p}$), Eficiência ($E_k = \frac{S_k}{k} \times 100\%$), Fração de Amdahl ($f = \frac{k(S_k - 1)}{S_k(k - 1)}$), além de `tempo_kernel_ms` e `tempo_transferencia_ms` (H2D + D2H via `cl_event`).
4. **Portão Humano Gate 2 Obrigatório:** Toda alteração no motor C/OpenCL, em migrations Alembic ou em endpoints que alterem `Horario` só pode ser aplicada e mesclada após Debate Adversarial unânime e aprovação humana explícita no Gate 2 (`AGENTS.md` §5).

---

## 3. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Seleção de Backend Paralelo e Fallback Auditável

> **Como** Coordenador ou Administrador do Campus  
> **Quero** selecionar o backend de execução do motor (`auto`, `opencl`, `openmp`, `cpu_sequencial`) e consultar os dispositivos OpenCL detectados  
> **Para que** a alocação aproveite aceleração OpenCL quando disponível e registre de forma transparente qualquer fallback para OpenMP.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Execução bem-sucedida via backend OpenCL com dispositivo disponível
  Dado que o ambiente possui plataforma e dispositivo OpenCL ativos via ICD
  E existem turmas e salas válidas cadastradas no campus
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com backend "opencl" e executar_baseline_sequencial true
  Então a resposta HTTP deve ser 200 OK
  E metricas.backend_utilizado deve ser "opencl"
  E metricas.dispositivo_opencl deve identificar o dispositivo selecionado
  E metricas.tempo_kernel_ms e metricas.tempo_transferencia_ms devem ser maiores ou iguais a zero

Cenário: Fallback auditável para OpenMP no modo automático sem plataforma OpenCL
  Dado que o ambiente não possui nenhuma plataforma ou dispositivo OpenCL disponível
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com backend "auto"
  Então a resposta HTTP deve ser 200 OK
  E metricas.backend_utilizado deve ser "openmp"
  E metricas.fallback_ativado deve ser true
  E o registro em LogAlocacao deve documentar o fallback de OpenCL para OpenMP

Cenário: Rejeição explícita quando backend OpenCL é forçado sem dispositivo
  Dado que o ambiente não possui dispositivo OpenCL disponível
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com backend "opencl"
  Então a API deve retornar HTTP 503 Service Unavailable
  E nenhum registro parcial deve ser persistido na tabela horario
```

### História 2: Busca Multi-Start e Avaliação Paralela Determinística em Kernel OpenCL

> **Como** Engenheiro de Sistemas de Alto Desempenho  
> **Quero** que o kernel OpenCL avalie as iterações multi-start em paralelo sem alocação dinâmica no device e realize redução determinística do melhor resultado  
> **Para que** a solução escolhida seja livre de condições de corrida, idêntica para a mesma semente vencedora e instrumentada por `cl_event`.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Determinismo da redução paralela em kernel OpenCL
  Dado um conjunto fixo de 100 turmas e 40 salas passado para otimizar_alocacao_salas_v2 com backend MOTOR_BACKEND_OPENCL
  Quando o kernel OpenCL avaliar N iterações com redução por work-group usando critério (score > melhor || (score == melhor && iter < melhor_iter))
  Então duas execuções consecutivas sobre os mesmos dados devem produzir exatamente a mesma AlocacaoItemC[] e o mesmo score total
  E toda chamada da API OpenCL deve validar retorno cl_int igual a CL_SUCCESS

Cenário: Respeito integral às restrições rígidas no kernel OpenCL
  Dado turmas regulares e de laboratório com capacidades, turnos e professores definidos
  Quando o kernel OpenCL executar a alocação paralela
  Então nenhuma alocação deve violar capacidade da sala, exigência de laboratório ou turno compatível
  E todas as métricas de profiling (tempo_kernel_ms e tempo_transferencia_ms) devem ser finitas e não negativas
```

### História 3: Checagem de Conflito de Horário de Professor e Distribuição Multi-Slot

> **Como** Coordenador Acadêmico  
> **Quero** que o motor impeça a alocação simultânea de um mesmo professor em duas turmas distintas e distribua turmas por blocos horários válidos do turno  
> **Para que** a grade gerada seja operacionalmente executável sem choques docentes nem colisões artificiais de `idx % 5`.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Bloqueio de choque de horário para o mesmo professor
  Dado que existem duas salas livres idênticas e compatíveis no mesmo campus
  E existem duas turmas A e B atribuídas ao mesmo professor_id 42 no mesmo dia e faixa horária
  Quando o motor executar a alocação em qualquer backend (sequencial, OpenMP ou OpenCL)
  Então no máximo uma das turmas deve ser alocada nesse horário caso não haja outro slot livre
  E nenhuma alocação resultante deve conter o professor_id 42 em dois intervalos sobrepostos no mesmo dia

Cenário: Turmas sem docente atribuído não sofrem falso conflito
  Dado que existem duas salas livres no mesmo horário
  E existem duas turmas A e B com professor_id igual a 0 (sem docente vinculado)
  Quando o motor executar a alocação
  Então ambas as turmas devem poder ser alocadas simultaneamente em salas distintas

Cenário: Distribuição multi-slot no endpoint de otimização evitando colisão sintética
  Dado que existem duas turmas do mesmo professor no turno matutino sem horário fixo pré-existente
  Quando o endpoint POST /api/v1/alocacao/otimizar preparar a entrada do motor C
  Então as turmas devem poder utilizar blocos horários e dias úteis distintos do turno antes de gerar conflito
```

### História 4: Persistência Não-Destrutiva de `Horario` e Preservação de Histórico

> **Como** Administrador e Responsável de Dados  
> **Quero** que a re-otimização de alocação preserve registros existentes de `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento`  
> **Para que** o histórico acadêmico e o fluxo Human-in-the-Loop da IA nunca sejam destruídos por exclusão em cascata.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Re-otimização preservando turmas já alocadas (modo preservar_alocados)
  Dado que a Turma 10 possui um Horario ativo com registros vinculados em frequencia e sugestao_remanejamento
  E a Turma 11 do mesmo período letivo ainda não possui Horario ativo
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com salvar_no_banco true e modo_reotimizacao "preservar_alocados"
  Então o Horario da Turma 10 deve permanecer intacto com seu mesmo id e todas as frequências e sugestões preservadas
  E os slots já ocupados da Turma 10 devem ser respeitados como ocupados para evitar colisão ao alocar a Turma 11

Cenário: Arquivamento lógico com proteção referencial no banco (modo arquivar_historico)
  Dado que existem registros em frequencia e previsao_falta vinculados a um Horario ativo da Turma 10
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com salvar_no_banco true e modo_reotimizacao "arquivar_historico"
  Então o Horario anterior deve ter ativo alterado para false e substituido_em preenchido sem sofrer DELETE
  E um novo Horario com ativo igual a true deve ser inserido com rastreabilidade em LogAlocacao.snapshot_evento
  E uma tentativa direta de DELETE em horario referenciado por frequencia deve falhar por integridade referencial (RESTRICT)

Cenário: Proteção contra sobrescrita silenciosa de sugestão pendente (modo atualizar_inplace)
  Dado que existe uma SugestaoRemanejamento com status "pendente" para o Horario da Turma 10
  Quando o Administrador enviar POST /api/v1/alocacao/otimizar com modo_reotimizacao "atualizar_inplace"
  Então a API deve retornar HTTP 409 Conflict orientando decisão prévia sobre a sugestão pendente
```

### História 5: Latência Produtiva Otimizada e Benchmark Científico Honesto

> **Como** Administrador do Sistema e Avaliador Técnico  
> **Quero** que a otimização operacional em produção evite a corrida sequencial redundante por padrão e que o benchmark reporte distribuições estatísticas reais sem truncamento de amostras  
> **Para que** o endpoint produtivo tenha menor latência e os relatórios de speedup expressem com honestidade científica a variabilidade do hardware.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Execução produtiva sem dupla corrida sequencial obrigatória
  Dado que o Administrador aciona POST /api/v1/alocacao/otimizar com executar_baseline_sequencial false (padrão operacional)
  Quando o motor C executar a otimização no backend paralelo selecionado
  Então a busca combinatória deve ser executada apenas uma vez no backend paralelo alvo
  E metricas.tempo_sequencial_ms deve ser 0.0 sinalizando ausência de baseline comparativo nessa chamada

Cenário: Execução comparativa completa sob demanda e em benchmark
  Dado que o Administrador aciona POST /api/v1/alocacao/otimizar com executar_baseline_sequencial true ou aciona POST /api/v1/alocacao/benchmark
  Quando o motor C executar a medição comparativa
  Então deve executar o baseline sequencial e o backend paralelo alvo, calculando speedup, eficiencia_pct e fracao_amdahl reais sem piso artificial de 0.01 ms

Cenário: Benchmark estatístico sem clamping de outliers acima de 14%
  Dado uma série de medições brutas [10.0, 10.2, 10.1, 18.5, 9.9] contendo um outlier acima de 14% da mediana
  Quando calcular_estatisticas_cenario processar a amostra
  Então todas as amostras brutas devem ser preservadas sem truncamento no intervalo [0.88*med, 1.12*med]
  E o relatório deve expor média, desvio padrão, CV%, mediana, IQR, p95, mínimo, máximo e contagem de outliers IQR
```

---

## 4. Arquitetura e Contratos Técnicos

### 4.1 Contrato ABI em C11 e Alinhamento de 64 Bits (`backend/motor_alocacao/motor.h`)

Todas as structs trocadas via `ctypes` devem manter tamanho múltiplo exato de 8 bytes (exceto `SalaC` 16B e `AlocacaoItemC` 24B já múltiplos de 8B), tipos de largura fixa (`<stdint.h>`) e validação em tempo de compilação com `_Static_assert`:

```c
#ifndef MOTOR_ALOCACAO_H
#define MOTOR_ALOCACAO_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TIPO_SALA_REGULAR     0
#define TIPO_SALA_LABORATORIO 1
#define TIPO_SALA_AUDITORIO   2
#define TIPO_SALA_REUNIAO     3

#define TURNO_MATUTINO   0
#define TURNO_VESPERTINO 1
#define TURNO_NOTURNO    2
#define TURNO_INTEGRAL   3

#define TURNO_MASK_MATUTINO   (1 << 0)
#define TURNO_MASK_VESPERTINO (1 << 1)
#define TURNO_MASK_NOTURNO    (1 << 2)
#define TURNO_MASK_INTEGRAL   (1 << 3)

typedef enum {
    MOTOR_BACKEND_AUTO = 0,
    MOTOR_BACKEND_CPU_SEQUENCIAL = 1,
    MOTOR_BACKEND_OPENMP = 2,
    MOTOR_BACKEND_OPENCL = 3
} MotorBackend;

typedef struct {
    int32_t id;
    int32_t capacidade;
    int32_t tipo;
    int32_t turnos_mask;
} SalaC; /* 16 bytes, align 4 */

typedef struct {
    int32_t id;
    int32_t num_matriculados;
    int32_t tipo_exigido;
    int32_t turno;
    int32_t dia_semana_sugerido;
    int32_t hora_inicio_min;
    int32_t hora_fim_min;
    int32_t professor_id; /* 0 = sem docente atribuido; >0 = id valido do docente */
} TurmaC; /* 32 bytes, align 4 (multiplo exato de 8 bytes e potencia de 2) */

typedef struct {
    int32_t turma_id;
    int32_t sala_id;
    int32_t dia_semana;
    int32_t hora_inicio_min;
    int32_t hora_fim_min;
    int32_t score_desperdicio;
} AlocacaoItemC; /* 24 bytes, align 4 */

typedef struct {
    double tempo_sequencial_ms;     /* offset 0  */
    double tempo_paralelo_ms;       /* offset 8  */
    double speedup;                 /* offset 16 */
    double eficiencia;              /* offset 24 */
    double fracao_amdahl;           /* offset 32 */
    double tempo_kernel_ms;         /* offset 40 */
    double tempo_transferencia_ms;  /* offset 48 */
    int32_t threads_utilizadas;     /* offset 56 */
    int32_t total_alocado;          /* offset 60 */
    int32_t total_pendente;         /* offset 64 */
    int32_t backend_solicitado;     /* offset 68 */
    int32_t backend_utilizado;      /* offset 72 */
    int32_t fallback_ativado;       /* offset 76 */
    char dispositivo_opencl[64];    /* offset 80..143 (NUL-terminated) */
} MetricasAlocacaoC; /* 144 bytes, align 8, zero padding oculto */

typedef struct {
    char platform_name[64];         /* offset 0..63 */
    char device_name[64];           /* offset 64..127 */
    char device_type[16];           /* offset 128..143: "GPU", "CPU", "ACCELERATOR" */
    char opencl_c_version[32];      /* offset 144..175 */
    uint32_t compute_units;         /* offset 176 */
    uint32_t global_mem_mb;         /* offset 180 */
    uint64_t max_work_group_size;   /* offset 184..191 */
} OpenCLDeviceInfoC; /* 192 bytes, align 8 */

#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(SalaC) == 16, "SalaC deve ter 16 bytes");
_Static_assert(sizeof(TurmaC) == 32, "TurmaC deve ter 32 bytes");
_Static_assert(sizeof(AlocacaoItemC) == 24, "AlocacaoItemC deve ter 24 bytes");
_Static_assert(sizeof(MetricasAlocacaoC) == 144, "MetricasAlocacaoC deve ter 144 bytes");
_Static_assert(sizeof(OpenCLDeviceInfoC) == 192, "OpenCLDeviceInfoC deve ter 192 bytes");
#endif

/* API v2 com selecao de backend, baseline opcional e suporte OpenCL */
int otimizar_alocacao_salas_v2(
    const TurmaC* turmas,
    int32_t num_turmas,
    const SalaC* salas,
    int32_t num_salas,
    int32_t max_threads,
    int32_t backend_alvo,
    int32_t medir_baseline_seq,
    AlocacaoItemC* resultado_out,
    MetricasAlocacaoC* metricas_out
);

int executar_benchmark_cenario_v2(
    int32_t num_turmas,
    int32_t num_salas,
    int32_t num_threads,
    int32_t backend_alvo,
    MetricasAlocacaoC* metricas_out
);

int obter_status_opencl(int32_t* disponivel_out, char* dispositivo_out, int32_t buf_len);
int obter_dispositivos_opencl(OpenCLDeviceInfoC* dispositivos_out, int32_t max_dispositivos, int32_t* total_out);
void liberar_recursos_motor(void);

/* Wrappers retrocompativeis legados */
int otimizar_alocacao_salas(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    int max_threads,
    AlocacaoItemC* resultado_out,
    MetricasAlocacaoC* metricas_out
);

int executar_benchmark_cenario(
    int num_turmas,
    int num_salas,
    int num_threads,
    MetricasAlocacaoC* metricas_out
);

const char* obter_versao_motor(void);
int testar_integracao_ctypes(int a, int b);

#ifdef __cplusplus
}
#endif

#endif /* MOTOR_ALOCACAO_H */
```

**Observação sobre Preservação de Slots Ocupados:** No modo `preservar_alocados`, o endpoint FastAPI não precisa de outra struct C caso queira apenas filtrar as turmas pendentes, ou pode descontar disponibilidade via bloqueio prévio no kernel. Para evitar colisões entre turmas já alocadas e novas turmas na mesma sala e no mesmo professor, o módulo C pode receber opcionalmente turmas bloqueadas pré-alocadas ou o `alocacao.py` passa os horários ativos travados via extensão retrocompatível de ocupação prévia (adicionada em PR 4 se necessário, mantendo `otimizar_alocacao_salas_v2` limpa e sem alterar assinatura pública existente de v2). Especificamente, define-se a função auxiliar interna `otimizar_alocacao_com_reservas(...)` com `ReservaPreviaC` (`sala_id`, `professor_id`, `dia_semana`, `hora_inicio_min`, `hora_fim_min`, `int32_t padding` = 24 bytes), usada em PR 4 quando `modo_reotimizacao == "preservar_alocados"`.

**Códigos de Retorno C:**
- `0`: Sucesso.
- `-1`: Argumentos inválidos (`num_turmas <= 0`, `num_salas <= 0`, ponteiro nulo ou `backend_alvo` desconhecido).
- `-2`: Falha de alocação de memória no host.
- `-3`: Backend `MOTOR_BACKEND_OPENCL` explicitamente solicitado sem plataforma/dispositivo OpenCL válido ou falha de compilação/execução do kernel OpenCL (no Python `motor_service.py`, `-3` gera erro específico que o FastAPI traduz para HTTP `503 Service Unavailable`).

### 4.2 Design do Kernel OpenCL (`backend/motor_alocacao/kernels/alocacao.cl` e `motor_opencl.{h,c}`)

1. **Ordem de Descoberta de Dispositivos (`motor_opencl.c`):**
   - Consultar plataformas via `clGetPlatformIDs`.
   - Priorizar `CL_DEVICE_TYPE_GPU`; se indisponível, selecionar `CL_DEVICE_TYPE_ACCELERATOR` e em seguida `CL_DEVICE_TYPE_CPU` (ex.: `pocl-opencl-icd` em containers Linux e CI).
   - Manter cache seguro em processo para `cl_platform_id`, `cl_device_id`, `cl_context`, `cl_command_queue` (criada com `CL_QUEUE_PROFILING_ENABLE`), `cl_program` e `cl_kernel`, protegidos por inicialização controlada e liberados deterministicamente em `liberar_recursos_motor()`.
   - Toda chamada `cl*` deve checar `cl_int err == CL_SUCCESS`; em falha de `clBuildProgram`, capturar o log via `clGetProgramBuildInfo(..., CL_PROGRAM_BUILD_LOG, ...)` para diagnóstico sem vazar memória.

2. **Empacotamento sem `malloc` no Device (`kernels/alocacao.cl`):**
   - Intervalos de ocupação de sala e de professor são empacotados em `uint32_t` de 32 bits:
     $$\text{slot\_packed} = ((\text{uint32\_t})(\text{dia} \& 0x7) \ll 22) \mid ((\text{uint32\_t})(\text{ini} \& 0x7FF) \ll 11) \mid (\text{uint32\_t})(\text{fim} \& 0x7FF)$$
     (cobrindo dias `0..6` e minutos `0..1440` em 11 bits por extremidade).
   - Para evitar estouro de registradores (`__private`) em cenários de stress (`500 x 150`), o kernel utiliza **grid-stride loop** com tamanho máximo de concorrentes limitado (ex.: `local_size = 64`, `num_groups` limitado ao múltiplo das compute units, `total_work_items <= 4096`), indexando buffers de trabalho pré-alocados em `__global`:
     - `scratch_ordem[work_item_id * num_turmas]` (`__global int*`)
     - `scratch_salas_slots[work_item_id * num_salas * MAX_SLOTS_POR_ENTIDADE]` (`__global uint*`) e `scratch_salas_count[work_item_id * num_salas]` (`__global ushort*`)
     - `scratch_prof_slots[work_item_id * max_profs_ou_turmas * MAX_SLOTS_POR_ENTIDADE]` (`__global uint*`) e `scratch_prof_count[...]` (`__global ushort*`)
   - Os vetores somente leitura `turmas[T]`, `salas[S]` e `ordem_base_bfd[T]` residem em `__global const` (com cópia opcional para `__local` quando o tamanho total couber com folga abaixo de `CL_DEVICE_LOCAL_MEM_SIZE`).

3. **Avaliação Determinística e Redução por Work-Group:**
   - Para cada `iter` atribuída ao work-item, `gerar_ordem_turmas_cl` aplica a mesma sequência PRNG determinística de `motor.c` (`2654435761U` e LCG `1103515245U + 12345U`) sobre `ordem_base_bfd`.
   - Em seguida, aplica a heurística Best-Fit Decreasing verificando todas as restrições rígidas: `capacidade`, `tipo`, `turno`, ausência de conflito na sala **e ausência de conflito para `professor_id > 0`**.
   - Cada work-item mantém seu melhor `(best_score_wi, best_iter_wi)` usando o critério exato de desempate determinístico:
     ```c
     bool melhor = (score > best_score) || (score == best_score && iter < best_iter);
     ```
   - Ao final do grid-stride loop, o work-group executa redução em árvore na memória `__local` (`__local long local_scores[64]`, `__local int local_iters[64]`) com `barrier(CLK_LOCAL_MEM_FENCE)`, gravando apenas 1 vencedor por work-group nos arrays de saída `wg_scores[group_id]` e `wg_iters[group_id]`.
   - **Replay Único no Host:** O host lê `wg_scores` e `wg_iters` (`num_groups * 12 bytes`, evitando transferir `num_iteracoes * T * 24 bytes`), escolhe o `best_iter` global com o mesmo desempate `iter < best_iter` e executa `executar_tentativa` uma única vez na CPU para `best_iter` a fim de preencher `resultado_out[0..num_turmas-1]`. Isso garante equivalência exata entre OpenMP e OpenCL e minimiza tráfego D2H.

4. **Profiling de Tempo via `cl_event`:**
   - `tempo_transferencia_ms`: soma dos intervalos `(CL_PROFILING_COMMAND_END - CL_PROFILING_COMMAND_START) * 1e-6` dos eventos de escrita H2D (`clEnqueueWriteBuffer`) e leitura D2H (`clEnqueueReadBuffer`).
   - `tempo_kernel_ms`: intervalo do evento de `clEnqueueNDRangeKernel`.
   - `tempo_paralelo_ms`: tempo total de parede (`omp_get_wtime()`) do pipeline OpenCL (incluindo H2D, kernel, D2H e replay único de `best_iter`), garantindo comparação honesta fim a fim frente ao tempo sequencial.

### 4.3 Ponte FFI `ctypes` (`backend/app/services/motor_service.py`)

1. **Espelhamento Estrito e Verificação de ABI:**
   - `TurmaC._fields_` recebe `("professor_id", ctypes.c_int32)` (8 campos = 32 bytes).
   - `MetricasAlocacaoC._fields_` é atualizado para 144 bytes com `ctypes.c_double` (7 campos), `ctypes.c_int32` (6 campos) e `("dispositivo_opencl", ctypes.c_char * 64)`.
   - `OpenCLDeviceInfoC` espelha exatamente a struct C de 192 bytes.
   - Em `__init__` (ou nível de módulo), asserções de sanidade validam `ctypes.sizeof(TurmaC) == 32`, `ctypes.sizeof(MetricasAlocacaoC) == 144` e `ctypes.sizeof(OpenCLDeviceInfoC) == 192`.
2. **`argtypes`, `restype` e Ciclo de Vida:**
   - Todas as funções C exportadas (`otimizar_alocacao_salas_v2`, `executar_benchmark_cenario_v2`, `obter_status_opencl`, `obter_dispositivos_opencl`, `liberar_recursos_motor`, além dos wrappers legados) recebem declaração explícita de `argtypes` e `restype` (`liberar_recursos_motor.restype = None`, `argtypes = []`).
   - Buffers de entrada e saída continuam alocados no chamador Python via `ctypes`; nenhuma memória alocada por `malloc` em C é retornada ao Python para liberação.
   - `atexit.register(self._liberar_ao_encerrar)` invoca `liberar_recursos_motor()` ao desligar o worker FastAPI.
3. **Resolução Segura da Biblioteca (`MOTOR_LIB_PATH`):**
   - `_carregar_biblioteca()` verifica primeiramente a variável de ambiente `MOTOR_LIB_PATH` (ex.: `/opt/sigaas/motor/motor_alocacao.so` no Docker) e, na ausência dela, usa `backend/motor_alocacao/motor_alocacao.{so,dll}`.
   - `_compilar_se_necessario()` invoca `make` (ou flags equivalentes respeitando disponibilidade de `<CL/cl.h>`) quando o arquivo `.so` não existir ou estiver desatualizado em relação a `motor.c`, `motor.h`, `motor_opencl.c` e `kernels/alocacao.cl`.

### 4.4 Contratos HTTP, Pydantic v2 e Persistência Não-Destrutiva

#### A. Endpoints de Alocação (`backend/app/schemas/alocacao.py` e `backend/app/api/v1/endpoints/alocacao.py`)

- **`POST /api/v1/alocacao/otimizar`**:
  - Campos adicionados de forma **100% retrocompatível** em `AlocacaoOtimizarRequest`:
    - `backend: Literal["auto", "opencl", "openmp", "cpu_sequencial"] = "auto"`
    - `modo_reotimizacao: Literal["preservar_alocados", "atualizar_inplace", "arquivar_historico"] = "preservar_alocados"`
    - `executar_baseline_sequencial: bool = False` (evita corrida dupla em produção; clientes legados ou testes comparativos podem enviar `true`).
  - Campos adicionados com valores padrão em `MetricasAlocacaoResponse`:
    - `backend_utilizado: str = "openmp"`
    - `fallback_ativado: bool = False`
    - `dispositivo_opencl: str | None = None`
    - `tempo_kernel_ms: float = 0.0`
    - `tempo_transferencia_ms: float = 0.0`
  - **Substituição da distribuição sintética `idx % 5`:** Em vez de fixar `idx % 5` e um único bloco por turno, `alocacao.py` consulta os horários ativos existentes e distribui turmas sem horário definido por janelas válidas do turno (`matutino`: `08:00-10:00`, `10:00-12:00`; `vespertino`: `14:00-16:00`, `16:00-18:00`; `noturno`: `19:00-21:00`, `21:00-22:40`; `integral`: `08:00-12:00`, `14:00-18:00`), evitando sobrepor turmas do mesmo `professor_id` na entrada do motor.
  - **Estratégia Não-Destrutiva em `salvar_no_banco=True`:**
    1. `preservar_alocados` (padrão): mantém todos os `Horario` ativos (`ativo=True`) já existentes para as turmas do lote, injeta suas ocupações de sala e professor como reservas prévias e aloca apenas turmas ainda sem `Horario` ativo.
    2. `atualizar_inplace`: verifica se há `SugestaoRemanejamento` com `status == "pendente"` nos horários afetados; havendo, retorna HTTP `409 Conflict`. Caso contrário, atualiza `sala_id`, `dia_semana`, `hora_inicio` e `hora_fim` preservando o `Horario.id` e mantendo intactas `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento` históricas.
    3. `arquivar_historico`: atualiza os registros anteriores para `ativo = False` e `substituido_em = func.now()` (jamais `DELETE`), insere novos `Horario(ativo=True)` e grava o mapeamento `id_anterior -> id_novo` em `LogAlocacao.snapshot_evento`.

- **`POST /api/v1/alocacao/benchmark`**:
  - `AlocacaoBenchmarkRequest` recebe `backend: Literal["opencl", "openmp"] = "opencl"`.
  - Sempre executa baseline sequencial (`medir_baseline_seq=1`) e o backend paralelo escolhido, retornando `MetricasAlocacaoResponse` completa.

#### B. Endpoints do Motor (`backend/app/api/v1/endpoints/motor.py`)

- **`GET /api/v1/motor/status`**:
  - Alinhamento de `MotorStatusResponse` com `motor_service.get_status()`, adicionando:
    - `heuristica: str | None = None`
    - `opencl_disponivel: bool = False`
    - `dispositivo_opencl_padrao: str | None = None`
    - `backends_suportados: list[str] = []`
- **`GET /api/v1/motor/dispositivos`**:
  - Novo endpoint que retorna a lista tipada `list[OpenCLDeviceInfoSchema]` com plataforma, dispositivo, tipo (`GPU`/`CPU`), `compute_units`, `global_mem_mb`, `max_work_group_size` e `opencl_c_version`.
- **Coordenação Explícita de Segurança com o Marco M3 (`spec-seguranca-mfa-rbac.md`):**
  - Atualmente `GET /api/v1/motor/status` e `POST /api/v1/motor/teste-integracao` não possuem `Depends(get_current_user)` nem `require_role`, enquanto `.github/workflows/ci.yml:199, 203` chama `GET /api/v1/motor/status` sem autenticação no smoke test.
  - Em M2, o contrato de `GET /api/v1/motor/status` permanece compatível para não quebrar o smoke test antes de M3; `GET /api/v1/motor/dispositivos` já deve exigir `Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR))` (ou integrar o plano único de autenticação de `/motor/*` definido em M3), coordenando a atualização simultânea de `.github/workflows/ci.yml:199, 203` (usar `/health` para check público ou autenticar antes de consultar `/motor/status`) e `backend/tests/test_openapi_docs.py` na entrega de segurança.

#### C. Modelo de Dados PostgreSQL e Migration Alembic (`[Sim]`)

- **Requer migration Alembic?** `[Sim]`.
- **Arquivo previsto:** `backend/alembic/versions/004_horario_historico_ondelete_restrict.py` (com `down_revision = "003_release_candidate_indexes"`).
- **Alterações em `upgrade()`:**
  1. Em `horario`: adicionar `ativo` (`sa.Boolean()`, `nullable=False`, `server_default=sa.text("true")`) + índice `ix_horario_ativo`, e `substituido_em` (`sa.DateTime(timezone=True)`, `nullable=True`).
  2. Nas tabelas `frequencia`, `previsao_falta` e `sugestao_remanejamento`: alterar a chave estrangeira `horario_id -> horario.id` de `ondelete="CASCADE"` para `ondelete="RESTRICT"` (utilizando inspeção dinâmica do nome da constraint existente via `sa.inspect(bind)` + `op.batch_alter_table` para portabilidade entre PostgreSQL e SQLite).
- **Reversibilidade em `downgrade()`:**
  1. Restaurar FKs `horario_id` para `ondelete="CASCADE"`.
  2. Remover índice `ix_horario_ativo` e colunas `substituido_em` e `ativo` da tabela `horario`.
- **Consultas filtradas por `Horario.ativo.is_(True)`:** Atualizar `backend/app/api/v1/endpoints/horarios.py`, `backend/app/api/v1/endpoints/sugestoes.py` e `backend/app/services/ia_service.py` para considerar apenas horários ativos nas listagens e predições correntes, mantendo o histórico arquivado acessível para auditoria.

### 4.5 Build, Docker, CI e GPU Opcional

1. **`backend/motor_alocacao/Makefile`:**
   - Suporte configurável `USE_OPENCL ?= 1`:
     - Quando `USE_OPENCL=1`: `CFLAGS = -Wall -Wextra -Werror -pedantic -std=c11 -O3 -fPIC -fopenmp -DUSE_OPENCL` e `LDFLAGS = -shared -fopenmp -lOpenCL`, compilando `motor.c` + `motor_opencl.c`.
     - Quando `USE_OPENCL=0` (ambientes locais sem SDK OpenCL): compila sem `-lOpenCL`, retornando `disponivel=0` em `obter_status_opencl` e mantendo OpenMP funcional.
2. **`docker/backend/Dockerfile` e `backend/Dockerfile`:**
   - Instalar `build-essential`, `libomp-dev`, `ocl-icd-opencl-dev`, `pocl-opencl-icd` e `clinfo`.
   - Executar `clinfo --list || true` e `cd /app/motor_alocacao && make clean && make USE_OPENCL=1`.
   - Copiar `/app/motor_alocacao/motor_alocacao.so` e `/app/motor_alocacao/kernels/alocacao.cl` para `/opt/sigaas/motor/` e definir `ENV MOTOR_LIB_PATH=/opt/sigaas/motor/motor_alocacao.so`.
   - Dessa forma, `docker/compose/docker-compose.local.yml:43` (`../../backend:/app`) mantém hot-reload do código Python sem sombrear a biblioteca nativa compilada para Linux.
3. **`.github/workflows/ci.yml`:**
   - Nos jobs `test-backend` e `test-motor-c`: instalar `build-essential libomp-dev ocl-icd-opencl-dev pocl-opencl-icd clinfo`, executar `clinfo` e compilar `make clean && make USE_OPENCL=1` antes de `pytest`.
   - Padronizar `python scripts/check_pr_size.py origin/${{ github.base_ref }} 400` conforme `AGENTS.md` §6.4 (em substituição ao limite temporário `1200` em `ci.yml:52`).
4. **Arquivo Opcional `docker/compose/docker-compose.gpu.yml`:**
   - Override opcional para hosts com GPU física (`/dev/dri:/dev/dri` para Intel/AMD ou `deploy.resources.reservations.devices` NVIDIA com ICD montado), preservando `local`, `homolog` e `prod` 100% compatíveis com servidores CPU-only.

---

## 5. Fatiamento em PRs Incrementais (<= 300-400 LOC)

Segundo `scripts/check_pr_size.py`, apenas linhas **adicionadas** em arquivos com extensões `{.py, .c, .h, .ts, .js, .html, .css, .scss, .sql}` fora dos 16 `IGNORED_PATTERNS` contam para o limite. Portanto:
- Arquivos `backend/tests/**/*.py`, `backend/alembic/versions/*.py`, `docs/**`, `*.md`, `*.json` e `.github/**` são **isentos**.
- Arquivos `*.cl`, `Makefile`, `Dockerfile` e `*.yml` são classificados como `[OUTRO]` (isentos).
- Arquivos em `backend/scripts/run_benchmarks_ci.py`, `backend/motor_alocacao/*.{c,h}`, `backend/app/**/*.py` e `frontend/src/app/services/*.ts` **são contados**.

Para manter ampla folga operacional, o módulo `motor_opencl` é fatiado em **PR 2a** e **PR 2b**, garantindo que **cada PR fique abaixo de 250 LOC de produção contadas**, compile isoladamente e passe toda a suíte de testes:

| PR | Branch | Escopo Atômico | Arquivos Contados (`CODE_EXTENSIONS`) | Arquivos Isentos (`IGNORED` / `[OUTRO]`) | LOC Prod. Est. | Commit (Conventional Commits) | Dep. | Gate 2 |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **PR 1** | `feat/motor-c-professor-conflict` | Adicionar `professor_id` em `TurmaC` (32B), `_Static_assert` de alinhamento, checagem de conflito docente com buffers empacotados `uint32_t` sem `realloc` no loop, e propagação `professor_id` em `motor_service.py` + `alocacao.py` | `backend/motor_alocacao/motor.h` (+20), `backend/motor_alocacao/motor.c` (+95), `backend/app/services/motor_service.py` (+15), `backend/app/api/v1/endpoints/alocacao.py` (+15) | `backend/tests/test_motor_c.py`, `backend/tests/test_api_alocacao.py` | **~145** | `feat(motor): adicionar checagem de conflito docente e alinhamento 64-bit` | Gate 1 | **Sim (Motor C + `Horario`)** |
| **PR 2a** | `feat/motor-opencl-discovery` | Definir `MotorBackend`, `MetricasAlocacaoC` (144B), `OpenCLDeviceInfoC` (192B), protótipos v2 em `motor.h`; implementar descoberta de plataforma/dispositivo, compilação JIT de kernel e `liberar_recursos_motor` em `motor_opencl.{h,c}`; configurar `Makefile` | `backend/motor_alocacao/motor.h` (+60), `backend/motor_alocacao/motor_opencl.h` (+55), `backend/motor_alocacao/motor_opencl.c` (+125) | `backend/motor_alocacao/kernels/alocacao.cl` (`[OUTRO]`), `backend/motor_alocacao/Makefile` (`[OUTRO]`), `backend/tests/test_motor_opencl.py` | **~240** | `feat(motor): adicionar infraestrutura de descoberta e compilacao opencl` | PR 1 | **Sim (Motor C/OpenCL)** |
| **PR 2b** | `feat/motor-opencl-kernel-exec` | Implementar transferência H2D/D2H, execução do kernel multi-start com redução `__local`, profiling `cl_event`, replay único de `best_iter`, fallback OpenCL -> OpenMP e `otimizar_alocacao_salas_v2` / `executar_benchmark_cenario_v2` | `backend/motor_alocacao/motor_opencl.c` (+145), `backend/motor_alocacao/motor.c` (+85) | `backend/motor_alocacao/kernels/alocacao.cl` (`[OUTRO]`), `backend/tests/test_motor_opencl.py`, `backend/tests/test_motor_c.py` | **~230** | `feat(motor): implementar execucao paralela opencl com reducao deterministica` | PR 2a | **Sim (Motor C/OpenCL)** |
| **PR 3** | `feat/motor-ffi-status-opencl` | Atualizar `MotorAlocacaoService` (`MetricasAlocacaoC` 144B, `OpenCLDeviceInfoC`, `argtypes`/`restype`, `MOTOR_LIB_PATH`, `atexit`, seleção de backend e baseline opcional); corrigir drift em `MotorStatusResponse` (`heuristica` + OpenCL) e criar `GET /api/v1/motor/dispositivos` | `backend/app/services/motor_service.py` (+130), `backend/app/api/v1/endpoints/motor.py` (+55) | `backend/tests/test_motor_service.py`, `backend/tests/test_api_motor.py` | **~185** | `feat(motor): expor backend opencl via ctypes e alinhar endpoints de status` | PR 2b | **Sim (FFI Motor C)** |
| **PR 4** | `fix/alocacao-nao-destrutiva-backend` | Implementar `Horario.ativo`/`substituido_em` e `ondelete="RESTRICT"` (migration 004); atualizar `horarios.py`, `sugestoes.py`, `ia_service.py`; substituir `delete(Horario)` por `preservar_alocados`/`atualizar_inplace`/`arquivar_historico`; substituir `idx % 5` e expor `backend`/`executar_baseline_sequencial` | `backend/app/models/alocacao.py` (+10), `backend/app/models/ia.py` (+6), `backend/app/schemas/alocacao.py` (+40), `backend/app/api/v1/endpoints/alocacao.py` (+150), `backend/app/api/v1/endpoints/horarios.py` (+10), `backend/app/api/v1/endpoints/sugestoes.py` (+10), `backend/app/services/ia_service.py` (+10) | `backend/alembic/versions/004_horario_historico_ondelete_restrict.py` (`alembic/versions`), `backend/tests/test_api_alocacao.py`, `backend/tests/test_migrations.py` | **~236** | `fix(alocacao): preservar historico de horario e distribuir slots sem colisao` | PR 3 | **Sim (Migration + `Horario`)** |
| **PR 5** | `perf/benchmark-opencl-docker-ci` | Atualizar `benchmark.c` e `POST /alocacao/benchmark` para comparar Seq vs OpenMP vs OpenCL; remover clamping `> 14%` e `sub_amostras=2` em `run_benchmarks_ci.py` adicionando mediana/IQR/p95/outliers; habilitar `ocl-icd-opencl-dev`, `pocl-opencl-icd`, `MOTOR_LIB_PATH` e `docker-compose.gpu.yml` | `backend/motor_alocacao/benchmark.c` (+45), `backend/app/api/v1/endpoints/alocacao.py` (+25), `backend/scripts/run_benchmarks_ci.py` (+95) | `docker/backend/Dockerfile`, `backend/Dockerfile`, `docker/compose/docker-compose.local.yml`, `docker/compose/docker-compose.gpu.yml`, `.github/workflows/ci.yml`, `backend/tests/test_benchmark_estatistico.py` | **~165** | `perf(motor): remover clamping estatistico e habilitar opencl em docker e ci` | PR 4 | **Sim (Motor C + CI)** |
| **PR 6** | `docs/motor-opencl-relatorio` | Atualizar interface TS opcional em `AlocacaoService` (compatível com payloads antigos), consolidar `relatorio_benchmark_c.{json,md}` (Seq vs OpenMP vs OpenCL) e atualizar status da spec para `Implementado` | `frontend/src/app/services/alocacao.service.ts` (+20) *(ou `0` se delegar UI para M4)* | `docs/specs/spec-motor-opencl-cuda.md`, `docs/projeto-gestao-salas-escalas.md`, `backend/app/motor/relatorio_benchmark_c.json`, `backend/app/motor/relatorio_benchmark_c.md` | **0 a 20** | `docs(motor): atualizar relatorio comparativo opencl e documentacao tecnica` | PR 5 | **Sim (Merge Final M2)** |

---

## 6. Plano de Testes TDD (RED / GREEN / REFACTOR)

### 6.1 Fase RED — Testes Criados Antes do Código de Produção

Cada cenário Gherkin da Seção 3 deve gerar primeiro um teste que falha explicitamente (`AssertionError`, `AttributeError` de campo/símbolo novo ou HTTP `422`/`503`) antes de qualquer alteração no código de produção:

#### A. Motor C, Alinhamento ABI e OpenCL (`backend/tests/test_motor_c.py` e `backend/tests/test_motor_opencl.py`)
- [ ] `backend/tests/test_motor_c.py::test_alinhamento_structs_64bit`: verifica `ctypes.sizeof(SalaC) == 16`, `ctypes.sizeof(TurmaC) == 32`, `ctypes.sizeof(AlocacaoItemC) == 24`, `ctypes.sizeof(MetricasAlocacaoC) == 144` (`alignment == 8`) e `ctypes.sizeof(OpenCLDeviceInfoC) == 192`.
- [ ] `backend/tests/test_motor_c.py::test_conflito_horario_mesmo_professor`: garante que duas turmas com `professor_id == 42` no mesmo dia e faixa horária nunca são alocadas simultaneamente mesmo com múltiplas salas vazias.
- [ ] `backend/tests/test_motor_c.py::test_turmas_sem_professor_nao_geram_falso_conflito`: garante que duas turmas com `professor_id == 0` no mesmo horário são alocadas normalmente em salas distintas.
- [ ] `backend/tests/test_motor_opencl.py::test_descoberta_dispositivos_opencl`: executa sob `faulthandler.enable()` validando `obter_status_opencl` e `obter_dispositivos_opencl` sem vazamentos ou segfaults.
- [ ] `backend/tests/test_motor_opencl.py::test_execucao_opencl_consistente_e_deterministica`: compara resultado OpenCL vs OpenMP em carga fixa e valida `tempo_kernel_ms >= 0.0`, `tempo_transferencia_ms >= 0.0` e determinismo entre execuções repetidas.
- [ ] `backend/tests/test_motor_opencl.py::test_fallback_auditavel_sem_opencl`: valida que `MOTOR_BACKEND_AUTO` faz fallback para `MOTOR_BACKEND_OPENMP` com `fallback_ativado == 1` quando OpenCL está indisponível, enquanto `MOTOR_BACKEND_OPENCL` forçado retorna erro `-3`.

#### B. Ponte FFI e Contratos HTTP (`backend/tests/test_motor_service.py` e `backend/tests/test_api_motor.py`)
- [ ] `backend/tests/test_motor_service.py::test_motor_lib_path_prioritario`: garante que `MOTOR_LIB_PATH` tem precedência sobre o caminho padrão (evitando sombreamento de bind mount).
- [ ] `backend/tests/test_motor_service.py::test_execucao_sem_baseline_sequencial`: valida que `executar_baseline_sequencial=False` retorna `tempo_sequencial_ms == 0.0` sem rodar busca sequencial.
- [ ] `backend/tests/test_api_motor.py::test_status_motor_inclui_heuristica_e_opencl`: valida `GET /api/v1/motor/status` retornando `heuristica`, `openmp_ativo`, `opencl_disponivel` e `backends_suportados` sem perda na serialização de `MotorStatusResponse`.
- [ ] `backend/tests/test_api_motor.py::test_dispositivos_opencl_endpoint`: valida `GET /api/v1/motor/dispositivos` com controle de acesso por perfil autorizado e schema de dispositivo.

#### C. Persistência Não-Destrutiva, Migration e Distribuição (`backend/tests/test_api_alocacao.py` e `backend/tests/test_migrations.py`)
- [ ] `backend/tests/test_api_alocacao.py::test_otimizar_preservar_alocados_mantem_frequencia_e_sugestoes`: com `PRAGMA foreign_keys=ON` ativo na sessão de teste, confirma que re-otimizar com `salvar_no_banco=True` preserva `Horario.id`, `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento`.
- [ ] `backend/tests/test_api_alocacao.py::test_otimizar_arquivar_historico_desativa_sem_delete`: valida `Horario.ativo == False` e `substituido_em` preenchido nos registros anteriores e rastreabilidade em `LogAlocacao.snapshot_evento`.
- [ ] `backend/tests/test_api_alocacao.py::test_otimizar_atualizar_inplace_bloqueia_sugestao_pendente_409`: valida retorno HTTP `409 Conflict` quando existir `SugestaoRemanejamento` pendente.
- [ ] `backend/tests/test_api_alocacao.py::test_otimizar_distribui_horarios_mesmo_professor`: valida que duas turmas do mesmo docente no mesmo turno não sofrem colisão sintética de `idx % 5` e bloco único.
- [ ] `backend/tests/test_migrations.py::test_migration_004_upgrade_downgrade_ondelete_restrict`: valida `alembic upgrade head` -> tentativa de `DELETE FROM horario` com `Frequencia` vinculada lançando `IntegrityError` -> `alembic downgrade` reversível.

#### D. Benchmark Estatístico (`backend/tests/test_benchmark_estatistico.py`)
- [ ] `backend/tests/test_benchmark_estatistico.py::test_benchmark_nao_aplica_clamping_em_outliers`: injeta amostra `[10.0, 10.2, 10.1, 18.5, 9.9]` e verifica que `mu`, `sigma`, `cv_pct`, `mediana`, `iqr` e `outliers_iqr` refletem o valor bruto `18.5` sem truncamento em `1.12 * mediana`.
- [ ] `backend/tests/test_benchmark_estatistico.py::test_benchmark_comparativo_openmp_e_opencl`: valida geração do relatório comparativo Sequencial vs OpenMP vs OpenCL sem `NaN` ou `Inf`.

### 6.2 Critérios de Conclusão (Fases GREEN e REFACTOR)

- [ ] **Suíte Backend + Cobertura:** `cd backend && python -X faulthandler -m pytest tests -v --cov=app --cov-config=.coveragerc --cov-fail-under=85` aprovado com `>= 85%` de cobertura e zero segfaults.
- [ ] **Compilação C/OpenCL Rigorosa:** `cd backend/motor_alocacao && make clean && make USE_OPENCL=1` sem warnings (`-Wall -Wextra -Werror -pedantic -std=c11`).
- [ ] **Descoberta OpenCL no Ambiente:** `clinfo --list` validando plataforma `Portable Computing Language` (ou GPU instalada) no Docker e no CI.
- [ ] **Qualidade e Segurança Estática:** `ruff check backend/ scripts/` e `bandit -r backend/app -ll -ii` sem achados bloqueantes.
- [ ] **Limite de Diff:** `python scripts/check_pr_size.py origin/main 400` aprovado em todos os PRs da cadeia (`PR 1` a `PR 6`).

---

## 7. Decomposição ClickUp, Debate Adversarial e Portões (Gate 1 / Gate 2)

### 7.1 Decomposição de Tarefas para o ClickUp

- [ ] `[SDD]` Sincronizar especificação no ClickUp: `python scripts/clickup_sync.py sync-spec docs/specs/spec-motor-opencl-cuda.md`
- [ ] `[PR 1]` Conflito docente (`TurmaC.professor_id` 32B) e remoção de `realloc` no loop de tentativa
- [ ] `[PR 2a]` Infraestrutura OpenCL C11 (`motor_opencl.{h,c}`, `kernels/alocacao.cl`, `Makefile`)
- [ ] `[PR 2b]` Execução paralela OpenCL, redução `__local`, profiling `cl_event` e fallback OpenMP
- [ ] `[PR 3]` Ponte `ctypes` (`MetricasAlocacaoC` 144B, `MOTOR_LIB_PATH`, `atexit`) e endpoints `/motor/status` e `/motor/dispositivos`
- [ ] `[PR 4]` Migration Alembic `004` (`Horario.ativo`, `ondelete="RESTRICT"`), persistência não-destrutiva e distribuição multi-slot
- [ ] `[PR 5]` Remoção de clamping no `run_benchmarks_ci.py`, benchmark comparativo OpenCL e pacotes OpenCL em Docker/CI
- [ ] `[PR 6]` Atualização de contratos opcionais, relatório comparativo `relatorio_benchmark_c.{json,md}` e fechamento da spec

### 7.2 Governança de Portões (Gate 1, Debate Adversarial e Gate 2)

| Etapa | Pré-requisito | Responsável | Critério de Aprovação |
| :--- | :--- | :--- | :--- |
| **Gate 1 (Spec)** | Spec completa em `docs/specs/spec-motor-opencl-cuda.md` | Aprovação Humana (PO / Banca) | Aprovação formal antes da criação de qualquer branch ou código de produção (`AGENTS.md` §5). |
| **Debate Adversarial Pré-PR** | Código + testes RED/GREEN + `check_pr_size.py <= 400` | Comitê (`advocate-mapper`, `adversary-breaker`, `adversary-security`, `adversary-compliance`, `debate-arbiter`) | Consenso unânime (zero vetos). Qualquer veto exige correção e novo ciclo completo de Re-Review sobre `git diff origin/main...HEAD` (`AGENTS.md` §7.1). |
| **Gate 2 (Execução & Merge)** | Debate Adversarial unânime + CI verde + inspeção `gh pr view <PR> --comments` | Aprovação Humana Explícita | Obrigatório antes de aplicar migrations no PostgreSQL, alterar motor C/OpenCL, alterar endpoints de `Horario` e realizar `gh pr merge <PR> --squash --delete-branch` (`AGENTS.md` §5 e §6.3). |
