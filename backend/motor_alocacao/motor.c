#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#include "motor.h"

typedef struct {
    int dia_semana;
    int inicio_min;
    int fim_min;
} IntervaloHorario;

typedef struct {
    int count;
    int capacidade;
    IntervaloHorario* intervalos;
} GradeOcupacaoSala;

static int verificar_sobreposicao(int ini1, int fim1, int ini2, int fim2) {
    return !(fim1 <= ini2 || ini1 >= fim2);
}

static int sala_tem_conflito(const GradeOcupacaoSala* grade, int dia_semana, int ini, int fim) {
    for (int k = 0; k < grade->count; k++) {
        if (grade->intervalos[k].dia_semana == dia_semana) {
            if (verificar_sobreposicao(ini, fim, grade->intervalos[k].inicio_min, grade->intervalos[k].fim_min)) {
                return 1;
            }
        }
    }
    return 0;
}

static void adicionar_reserva(GradeOcupacaoSala* grade, int dia_semana, int ini, int fim) {
    if (grade->count >= grade->capacidade) {
        int nova_cap = (grade->capacidade == 0) ? 16 : grade->capacidade * 2;
        IntervaloHorario* novo_ptr = (IntervaloHorario*)realloc(grade->intervalos, (size_t)nova_cap * sizeof(IntervaloHorario));
        if (!novo_ptr) return;
        grade->intervalos = novo_ptr;
        grade->capacidade = nova_cap;
    }
    grade->intervalos[grade->count].dia_semana = dia_semana;
    grade->intervalos[grade->count].inicio_min = ini;
    grade->intervalos[grade->count].fim_min = fim;
    grade->count++;
}

static int turno_compativel(int turma_turno, int sala_turnos_mask) {
    switch (turma_turno) {
        case TURNO_MATUTINO:
            return (sala_turnos_mask & TURNO_MASK_MATUTINO) != 0;
        case TURNO_VESPERTINO:
            return (sala_turnos_mask & TURNO_MASK_VESPERTINO) != 0;
        case TURNO_NOTURNO:
            return (sala_turnos_mask & TURNO_MASK_NOTURNO) != 0;
        case TURNO_INTEGRAL:
            return ((sala_turnos_mask & TURNO_MASK_INTEGRAL) != 0) ||
                   ((sala_turnos_mask & 7) == 7);
        default:
            return 1;
    }
}

static int tipo_compativel(int tipo_exigido, int sala_tipo) {
    if (tipo_exigido == TIPO_SALA_LABORATORIO) {
        return sala_tipo == TIPO_SALA_LABORATORIO;
    }
    return 1;
}

static unsigned int prng_next(unsigned int* seed) {
    *seed = (*seed * 1103515245U + 12345U) & 0x7fffffffU;
    return *seed;
}

static void gerar_ordem_turmas(int* ordem, int num_turmas, const TurmaC* turmas, int iteracao) {
    for (int i = 0; i < num_turmas; i++) {
        ordem[i] = i;
    }

    if (iteracao == 0) {
        // Ordenacao deterministica Best-Fit Decreasing:
        // Laboratorios primeiro, depois turmas com mais alunos
        for (int i = 0; i < num_turmas - 1; i++) {
            for (int j = i + 1; j < num_turmas; j++) {
                int ti = ordem[i];
                int tj = ordem[j];
                int lab_i = (turmas[ti].tipo_exigido == TIPO_SALA_LABORATORIO);
                int lab_j = (turmas[tj].tipo_exigido == TIPO_SALA_LABORATORIO);
                if (lab_j > lab_i || (lab_j == lab_i && turmas[tj].num_matriculados > turmas[ti].num_matriculados)) {
                    int tmp = ordem[i];
                    ordem[i] = ordem[j];
                    ordem[j] = tmp;
                }
            }
        }
    } else {
        // Perturbacao deterministica baseada na iteracao
        unsigned int seed = (unsigned int)iteracao * 2654435761U + 13U;
        for (int i = num_turmas - 1; i > 0; i--) {
            int j = (int)(prng_next(&seed) % (unsigned int)(i + 1));
            int tmp = ordem[i];
            ordem[i] = ordem[j];
            ordem[j] = tmp;
        }
    }
}

static void executar_tentativa(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    const int* ordem,
    AlocacaoItemC* resultado_local,
    GradeOcupacaoSala* grades_salas,
    int* total_alocado_out,
    int* total_pendente_out,
    long long* total_desperdicio_out
) {
    for (int j = 0; j < num_salas; j++) {
        grades_salas[j].count = 0;
    }

    int alocados = 0;
    int pendentes = 0;
    long long desperdicio = 0;

    for (int idx = 0; idx < num_turmas; idx++) {
        int i = ordem[idx];
        const TurmaC* t = &turmas[i];

        int melhor_sala_idx = -1;
        int menor_desperdicio = 10000000;

        for (int j = 0; j < num_salas; j++) {
            const SalaC* s = &salas[j];

            if (s->capacidade < t->num_matriculados) continue;
            if (!tipo_compativel(t->tipo_exigido, s->tipo)) continue;
            if (!turno_compativel(t->turno, s->turnos_mask)) continue;

            if (sala_tem_conflito(&grades_salas[j], t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min)) {
                continue;
            }

            int desp = s->capacidade - t->num_matriculados;
            if (t->tipo_exigido == TIPO_SALA_REGULAR && s->tipo == TIPO_SALA_LABORATORIO) {
                desp += 500;
            }

            if (desp < menor_desperdicio) {
                menor_desperdicio = desp;
                melhor_sala_idx = j;
            }
        }

        resultado_local[i].turma_id = t->id;
        resultado_local[i].dia_semana = t->dia_semana_sugerido;
        resultado_local[i].hora_inicio_min = t->hora_inicio_min;
        resultado_local[i].hora_fim_min = t->hora_fim_min;

        if (melhor_sala_idx >= 0) {
            const SalaC* s = &salas[melhor_sala_idx];
            resultado_local[i].sala_id = s->id;
            resultado_local[i].score_desperdicio = s->capacidade - t->num_matriculados;
            adicionar_reserva(&grades_salas[melhor_sala_idx], t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min);
            alocados++;
            desperdicio += resultado_local[i].score_desperdicio;
        } else {
            resultado_local[i].sala_id = -1;
            resultado_local[i].score_desperdicio = -1;
            pendentes++;
        }
    }

    *total_alocado_out = alocados;
    *total_pendente_out = pendentes;
    *total_desperdicio_out = desperdicio;
}

static void executar_busca_combinatoria(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    int num_threads,
    int num_iteracoes,
    AlocacaoItemC* melhor_resultado,
    int* total_alocado_out,
    int* total_pendente_out
) {
    if (num_threads < 1) num_threads = 1;

    long long melhor_score_global = -9223372036854775807LL;
    int global_alocados = 0;
    int global_pendentes = num_turmas;

    #pragma omp parallel num_threads(num_threads) default(none) \
        shared(turmas, num_turmas, salas, num_salas, num_iteracoes, melhor_resultado, \
               melhor_score_global, global_alocados, global_pendentes)
    {
        int* ordem_local = (int*)malloc((size_t)num_turmas * sizeof(int));
        AlocacaoItemC* res_local = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
        AlocacaoItemC* res_melhor_thread = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
        GradeOcupacaoSala* grades_local = (GradeOcupacaoSala*)malloc((size_t)num_salas * sizeof(GradeOcupacaoSala));

        for (int j = 0; j < num_salas; j++) {
            grades_local[j].count = 0;
            grades_local[j].capacidade = 16;
            grades_local[j].intervalos = (IntervaloHorario*)malloc(16 * sizeof(IntervaloHorario));
        }

        long long melhor_score_thread = -9223372036854775807LL;
        int thread_alocados = 0;
        int thread_pendentes = num_turmas;

        #pragma omp for schedule(dynamic, 16)
        for (int iter = 0; iter < num_iteracoes; iter++) {
            gerar_ordem_turmas(ordem_local, num_turmas, turmas, iter);

            int t_alocados = 0;
            int t_pendentes = 0;
            long long t_desperdicio = 0;

            executar_tentativa(
                turmas, num_turmas, salas, num_salas, ordem_local,
                res_local, grades_local, &t_alocados, &t_pendentes, &t_desperdicio
            );

            long long score = (long long)t_alocados * 1000000000LL - t_desperdicio;
            if (score > melhor_score_thread) {
                melhor_score_thread = score;
                thread_alocados = t_alocados;
                thread_pendentes = t_pendentes;
                memcpy(res_melhor_thread, res_local, (size_t)num_turmas * sizeof(AlocacaoItemC));
            }
        }

        #pragma omp critical
        {
            if (melhor_score_thread > melhor_score_global) {
                melhor_score_global = melhor_score_thread;
                global_alocados = thread_alocados;
                global_pendentes = thread_pendentes;
                memcpy(melhor_resultado, res_melhor_thread, (size_t)num_turmas * sizeof(AlocacaoItemC));
            }
        }

        for (int j = 0; j < num_salas; j++) {
            free(grades_local[j].intervalos);
        }
        free(grades_local);
        free(res_melhor_thread);
        free(res_local);
        free(ordem_local);
    }

    *total_alocado_out = global_alocados;
    *total_pendente_out = global_pendentes;
}

int otimizar_alocacao_salas(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    int max_threads,
    AlocacaoItemC* resultado_out,
    MetricasAlocacaoC* metricas_out
) {
    if (num_turmas <= 0 || num_salas <= 0 || !turmas || !salas || !resultado_out) {
        return -1;
    }

    int threads_alvo = max_threads;
    int max_disponivel = omp_get_num_procs();
    if (threads_alvo <= 0 || threads_alvo > max_disponivel) {
        threads_alvo = max_disponivel;
    }

    int num_iteracoes = 800;
    if (num_turmas <= 20) {
        num_iteracoes = 2500;
    } else if (num_turmas >= 100) {
        num_iteracoes = 1200;
    }

    AlocacaoItemC* res_seq = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
    int seq_alocado = 0, seq_pendente = 0;

    double t0_seq = omp_get_wtime();
    executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, 1, num_iteracoes, res_seq, &seq_alocado, &seq_pendente);
    double t1_seq = omp_get_wtime();
    double t_seq_ms = (t1_seq - t0_seq) * 1000.0;

    int par_alocado = 0, par_pendente = 0;
    double t0_par = omp_get_wtime();
    executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, threads_alvo, num_iteracoes, resultado_out, &par_alocado, &par_pendente);
    double t1_par = omp_get_wtime();
    double t_par_ms = (t1_par - t0_par) * 1000.0;

    free(res_seq);

    if (metricas_out) {
        if (t_seq_ms < 0.01) t_seq_ms = 0.01;
        if (t_par_ms < 0.01) t_par_ms = 0.01;

        metricas_out->tempo_sequencial_ms = t_seq_ms;
        metricas_out->tempo_paralelo_ms = t_par_ms;
        metricas_out->speedup = t_seq_ms / t_par_ms;
        metricas_out->eficiencia = (metricas_out->speedup / (double)threads_alvo) * 100.0;
        metricas_out->threads_utilizadas = threads_alvo;
        metricas_out->total_alocado = par_alocado;
        metricas_out->total_pendente = par_pendente;

        if (threads_alvo > 1 && metricas_out->speedup > 0.0) {
            double k = (double)threads_alvo;
            double s = metricas_out->speedup;
            double f = (k * (s - 1.0)) / (s * (k - 1.0));
            if (f < 0.0) f = 0.0;
            if (f > 1.0) f = 1.0;
            metricas_out->fracao_amdahl = f;
        } else {
            metricas_out->fracao_amdahl = 1.0;
        }
        metricas_out->padding = 0;
    }

    return 0;
}

int executar_benchmark_cenario(
    int num_turmas,
    int num_salas,
    int num_threads,
    MetricasAlocacaoC* metricas_out
) {
    if (num_turmas <= 0 || num_salas <= 0 || !metricas_out) {
        return -1;
    }

    TurmaC* turmas = (TurmaC*)malloc((size_t)num_turmas * sizeof(TurmaC));
    SalaC* salas = (SalaC*)malloc((size_t)num_salas * sizeof(SalaC));
    AlocacaoItemC* resultados = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));

    for (int j = 0; j < num_salas; j++) {
        salas[j].id = j + 1;
        salas[j].capacidade = 30 + (j % 8) * 10;
        salas[j].tipo = (j % 5 == 0) ? TIPO_SALA_LABORATORIO : TIPO_SALA_REGULAR;
        salas[j].turnos_mask = TURNO_MASK_MATUTINO | TURNO_MASK_VESPERTINO | TURNO_MASK_NOTURNO;
    }

    for (int i = 0; i < num_turmas; i++) {
        turmas[i].id = i + 1;
        turmas[i].num_matriculados = 25 + (i % 6) * 10;
        turmas[i].tipo_exigido = (i % 5 == 0) ? TIPO_SALA_LABORATORIO : TIPO_SALA_REGULAR;
        turmas[i].turno = i % 3;
        turmas[i].dia_semana_sugerido = i % 5;
        if (turmas[i].turno == TURNO_MATUTINO) {
            turmas[i].hora_inicio_min = 480;  // 08:00
            turmas[i].hora_fim_min = 600;     // 10:00
        } else if (turmas[i].turno == TURNO_VESPERTINO) {
            turmas[i].hora_inicio_min = 840;  // 14:00
            turmas[i].hora_fim_min = 960;     // 16:00
        } else {
            turmas[i].hora_inicio_min = 1140; // 19:00
            turmas[i].hora_fim_min = 1260;    // 21:00
        }
    }

    int rc = otimizar_alocacao_salas(turmas, num_turmas, salas, num_salas, num_threads, resultados, metricas_out);

    free(resultados);
    free(salas);
    free(turmas);

    return rc;
}

const char* obter_versao_motor(void) {
    return "SIGAAS Motor de Alocacao v0.2.0 (OpenMP Parallel Best-Fit)";
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
