---
name: c-openmp-hpc
description: >-
  High-performance computing in C with OpenMP, compiler optimizations (-O3, -fopenmp),
  prevention of race conditions and false sharing, and scientific speedup benchmarking (Amdahl's law).
  Use when implementing, profiling, or debugging parallel allocation algorithms in C.
---

# C + OpenMP High-Performance Computing

Engineering guidelines for parallel combinatorial optimization, thread safety, and scientific performance benchmarking in the SIGAAS allocation engine.

## 1. Compiler Flags & Optimization Standards

Always compile the C engine with rigorous optimization and diagnostic flags:

```bash
gcc -O3 -fopenmp -fPIC -Wall -Wextra -pedantic -std=c11 -shared -o motor_alocacao.so src/motor.c
```

- `-O3`: Vectorization, loop unrolling, and aggressive instruction scheduling.
- `-fopenmp`: Enables OpenMP runtime semantics and thread pool orchestration.
- `-fPIC`: Position Independent Code required for dynamic shared libraries loaded via `ctypes`.

## 2. Thread Safety & Parallelization Patterns

### Data Scoping
Explicitly declare data scopes on every parallel region:

```c
#pragma omp parallel for default(none) \
    shared(salas, turmas, total_turmas, matriz_alocada) \
    private(i, j, melhor_sala) \
    schedule(dynamic, 16)
for (int i = 0; i < total_turmas; i++) {
    // Processamento de alocacao
}
```

### Critical Rules
- **No Shared State Mutation without Protection**: Use `#pragma omp critical` or `#pragma omp atomic` only when strictly required; prefer thread-local reduction accumulators.
- **Prevent False Sharing**: Ensure array elements accessed by adjacent threads reside on different CPU cache lines (pad structs or index by stride >= 64 bytes).
- **Pure Functions**: Allocation heuristic evaluators must be deterministic and free of global mutable state.

## 3. Scientific Benchmarking: Sequential vs Parallel (Amdahl)

The project requires formal speedup measurement for academic reporting:

```c
#include <omp.h>
#include <stdio.h>

double t_inicio_seq = omp_get_wtime();
executar_alocacao_sequencial(...);
double t_fim_seq = omp_get_wtime();
double tempo_sequencial = t_fim_seq - t_inicio_seq;

double t_inicio_par = omp_get_wtime();
executar_alocacao_paralela(...);
double t_fim_par = omp_get_wtime();
double tempo_paralelo = t_fim_par - t_inicio_par;

double speedup = tempo_sequencial / tempo_paralelo;
double eficiencia = speedup / omp_get_max_threads();
```

Log these metrics in standardized format:
`[BENCHMARK] Threads: %d | Seq: %.4fs | Par: %.4fs | Speedup: %.2fx | Effic: %.2f%%`
