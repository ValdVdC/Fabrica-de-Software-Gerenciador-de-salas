# Relatorio de Benchmark Estatistico e Caracterizacao Teorica do Motor C/OpenMP

## 1. Caracterizacao Formal da Heuristica

- **Classificacao Algoritmica:** Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel
- **Classe de Complexidade:** NP-dificil
- **Complexidade Temporal por Tentativa:** `O(T * S)` (onde `T` = turmas e `S` = salas)
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
| Flags de Compilacao | `gcc -Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp -shared` |

## 3. Resultados Estatisticos (N=10 Repeticoes, 4 Threads OpenMP)

| Carga (Turmas x Salas) | Media Seq (ms) | Desvio Seq (ms) | CV Seq (%) | Media Par (ms) | Desvio Par (ms) | CV Par (%) | Speedup Real (S) | Eficiencia (%) | Estabilidade (CV < 15%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 10 x 5 | 0.97 | 0.05 | 4.98% | 0.75 | 0.08 | 10.54% | 1.29x | 32.2% | Aprovado |
| 50 x 20 | 2.91 | 0.20 | 6.96% | 0.99 | 0.03 | 3.19% | 2.94x | 73.5% | Aprovado |
| 100 x 40 | 15.40 | 0.98 | 6.33% | 4.12 | 0.19 | 4.69% | 3.74x | 93.5% | Aprovado |
| 500 x 150 | 259.00 | 4.88 | 1.88% | 84.59 | 7.89 | 9.33% | 3.06x | 76.5% | Aprovado |

## 4. Matriz de Rastreabilidade de Bugs e Testes de Regressao

| ID | Descricao Tecnica da Anomalia Corrigida | Commit / PR | Teste Automatizado de Regressao |
| :--- | :--- | :---: | :--- |
| `BUG-HPC-01` | Desalinhamento de 64-bit e ausencia de padding explicito na struct MetricasAlocacaoC via ctypes | `2d9d8c9 (#67)` | `tests/test_motor_c.py::test_speedup_concorrente` |
| `BUG-HPC-02` | Canibalizacao de laboratorios especializados por turmas regulares sem penalidade heuristica | `2d9d8c9 (#67)` | `tests/test_benchmark_estatistico.py::test_matriz_rastreabilidade_bugs_e_regressao` |
| `BUG-HPC-03` | Falso positivo de exigencia de laboratorio por correspondencia parcial de substring ('Elaboracao') | `2d9d8c9 (#67)` | `tests/test_api_alocacao.py::test_endpoint_otimizar_sucesso` |
| `BUG-HPC-04` | Omissao de turmas sem sala disponivel no retorno FFI quando todas as salas estao lotadas | `e06b008 / 2d9d8c9 (#67)` | `tests/test_api_alocacao.py::test_endpoint_retorna_turmas_sem_sala_com_sala_negativa` |
