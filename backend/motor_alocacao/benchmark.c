#include <stdio.h>
#include <stdlib.h>
#include "motor.h"

static void testar_cenario(const char* nome, int turmas, int salas, const int* threads, int total_testes) {
    printf("\n========================================================================================\n");
    printf(" CENARIO: %s (%d turmas x %d salas)\n", nome, turmas, salas);
    printf("========================================================================================\n");
    printf("| Threads | T_Seq (ms) | T_Par (ms) | Speedup  | Eficiencia | Amdahl (f) | Aloc/Total |\n");
    printf("|---------|------------|------------|----------|------------|------------|------------|\n");

    for (int t = 0; t < total_testes; t++) {
        int k = threads[t];
        MetricasAlocacaoC m;
        int rc = executar_benchmark_cenario(turmas, salas, k, &m);
        if (rc != 0) {
            printf("| %7d | ERRO NA EXECUCAO                                                               |\n", k);
            continue;
        }

        printf("| %7d | %10.2f | %10.2f | %7.2fx | %9.1f%% | %9.4f  | %4d/%-5d |\n",
               m.threads_utilizadas,
               m.tempo_sequencial_ms,
               m.tempo_paralelo_ms,
               m.speedup,
               m.eficiencia,
               m.fracao_amdahl,
               m.total_alocado,
               m.total_alocado + m.total_pendente);
    }
}

int main(void) {
    printf("SIGAAS - BATERIA CIENTIFICA DE BENCHMARK OPENMP\n");
    printf("Versao do Motor: %s\n", obter_versao_motor());

    int lista_threads[] = {1, 2, 4, 8};
    int total_threads = 4;

    testar_cenario("Pequeno (Funcional)", 20, 10, lista_threads, total_threads);
    testar_cenario("Medio (Operacional)", 100, 40, lista_threads, total_threads);
    testar_cenario("Stress (Escala Computacional)", 500, 150, lista_threads, total_threads);

    printf("\nBateria de benchmark concluida com sucesso.\n");
    return 0;
}
