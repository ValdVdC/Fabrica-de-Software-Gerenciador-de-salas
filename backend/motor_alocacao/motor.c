#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "motor.h"

const char* obter_versao_motor(void) {
    return "SIGAAS Motor de Alocação v0.1.0 (OpenMP Enabled)";
}

int testar_integracao_ctypes(int a, int b) {
    int resultado = 0;
    #pragma omp parallel
    {
        #pragma omp single
        {
            resultado = a + b;
        }
    }
    return resultado;
}

int otimizar_alocacao(
    const int* restricoes,
    int num_turmas,
    int num_salas,
    AlocacaoItem* resultado,
    int max_threads,
    double* tempo_execucao_ms
) {
    double inicio = omp_get_wtime();
    
    if (max_threads > 0) {
        omp_set_num_threads(max_threads);
    }

    // Placeholder para a busca combinatória que será desenvolvida na Sprint 5
    // Cada thread explorará partições do espaço de busca de salas e horários

    double fim = omp_get_wtime();
    if (tempo_execucao_ms != NULL) {
        *tempo_execucao_ms = (fim - inicio) * 1000.0;
    }
    
    return 0; // 0 = sucesso
}
