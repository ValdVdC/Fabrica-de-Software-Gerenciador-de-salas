# Relatorio de Benchmark Estatistico e Caracterizacao Teorica do Motor C/OpenMP

## 1. Caracterizacao Formal da Heuristica
- **Classificacao Algoritmica:** Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel
- **Classe de Complexidade:** NP-dificil
- **Complexidade Temporal por Tentativa:** `O(T * S)`
- **Garantia de Otimo Global:** Nao (Abordagem Heuristica Polinomial)
- **Fundamentacao Teorica:** Devido a natureza combinatorial NP-dificil do problema de Timetabling universitario, a busca exata e intratavel em escala real. O motor utiliza ordenacao Best-Fit Decreasing com multi-start perturbado deterministico em OpenMP, garantindo solucoes viaveis de alta qualidade em tempo polinomial O(T * S) por tentativa sem garantia de otimo global.

## 2. Ambiente de Execucao e Compilacao (Reprodutibilidade)
| Parametro de Ambiente | Especificacao Coletada |
| :--- | :--- |
| Modelo de CPU | AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD |
| Frequencia de Clock | 3901.0 MHz |
| Nucleos (Fisicos / Logicos) | 6 fisicos / 12 logicos |
| Memoria RAM Total | 13.89 GB |
| Sistema Operacional | Windows 11 (AMD64) |
| Compilador C | gcc (Rev8, Built by MSYS2 project) 15.2.0 |
| Flags de Compilacao | `gcc -Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp -shared -DUSE_OPENCL -lOpenCL` |
| Dispositivo OpenCL | AMD Radeon(TM) Graphics |

## 3. Resultados Estatisticos (N=10 Repeticoes, 4 Threads OpenMP)
| Carga (Turmas x Salas) | Media Seq (ms) | Desvio Seq (ms) | CV Seq (%) | Media Par (ms) | Desvio Par (ms) | CV Par (%) | Speedup Real (S) | Eficiencia (%) | Estabilidade (CV < 15%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 10 x 5 | 1.43 | 0.09 | 6.51% | 0.51 | 0.04 | 7.41% | 2.79x | 69.7% | Aprovado |
| 50 x 20 | 3.50 | 0.40 | 11.31% | 1.45 | 0.09 | 6.01% | 2.42x | 60.5% | Aprovado |
| 100 x 40 | 19.14 | 1.32 | 6.90% | 5.93 | 0.23 | 3.84% | 3.23x | 80.7% | Aprovado |
| 500 x 150 | 377.64 | 25.53 | 6.76% | 119.00 | 7.43 | 6.24% | 3.17x | 79.3% | Aprovado |

## 3.1 Comparativo Honesto: CPU Sequencial vs OpenMP CPU vs OpenCL GPU/PoCL (N=10)
| Carga (Turmas x Salas) | CPU Sequencial (ms) | OpenMP CPU (ms) | OpenCL Total (ms) | Speedup OpenMP | Speedup OpenCL | Kernel OpenCL (ms) | Transferencia H2D/D2H (ms) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 10 x 5 | 1.43 | 0.51 | 1.60 | 2.79x | 0.89x | 1.11 | 0.01 |
| 50 x 20 | 3.50 | 1.45 | 4.20 | 2.42x | 0.83x | 3.27 | 0.01 |
| 100 x 40 | 19.14 | 5.93 | 22.00 | 3.23x | 0.87x | 21.03 | 0.02 |
| 500 x 150 | 377.64 | 119.00 | 716.60 | 3.17x | 0.53x | 713.18 | 0.02 |

## 4. Matriz de Rastreabilidade de Bugs e Testes de Regressao
| ID | Descricao Tecnica da Anomalia Corrigida | Commit / PR | Teste Automatizado de Regressao |
| :--- | :--- | :---: | :--- |
| `BUG-HPC-01` | Desalinhamento de 64-bit e ausencia de padding explicito na struct MetricasAlocacaoC via ctypes | `2d9d8c9 (#67)` | `tests/test_motor_c.py::test_speedup_concorrente` |
| `BUG-HPC-02` | Canibalizacao de laboratorios especializados por turmas regulares sem penalidade heuristica | `2d9d8c9 (#67)` | `tests/test_benchmark_estatistico.py::test_matriz_rastreabilidade_bugs_e_regressao` |
| `BUG-HPC-03` | Falso positivo de exigencia de laboratorio por correspondencia parcial de substring ('Elaboracao') | `2d9d8c9 (#67)` | `tests/test_api_alocacao.py::test_endpoint_otimizar_sucesso` |
| `BUG-HPC-04` | Omissao de turmas sem sala disponivel no retorno FFI quando todas as salas estao lotadas | `e06b008 / 2d9d8c9 (#67)` | `tests/test_api_alocacao.py::test_endpoint_retorna_turmas_sem_sala_com_sala_negativa` |
