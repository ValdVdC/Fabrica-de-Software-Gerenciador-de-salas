#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#include "motor.h"
#include "motor_opencl.h"

// Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel.
// Complexidade O(T * S) por tentativa em paralelo via OpenMP (problema NP-dificil sem garantia de otimo global).

// Pool de ocupacao com slots empacotados em uint32_t sem realloc no loop paralelo.
typedef struct {
    int32_t* head;
    uint32_t* slots;
    int32_t* next;
    int32_t num_entidades;
    int32_t capacidade_slots;
    int32_t used;
} PoolOcupacao;

typedef struct {
    int32_t professor_id;
    int32_t turma_idx;
} ProfTurmaPair;

static uint32_t empacotar_slot(int32_t dia, int32_t ini, int32_t fim) {
    return (((uint32_t)(dia & 0x7)) << 22) |
           (((uint32_t)(ini & 0x7FF)) << 11) |
           ((uint32_t)(fim & 0x7FF));
}

static int slot_valido(int32_t dia, int32_t ini, int32_t fim) {
    return (dia >= 0 && dia <= 6 && ini >= 0 && fim <= 1440 && ini < fim);
}

static int verificar_sobreposicao(int32_t ini1, int32_t fim1, int32_t ini2, int32_t fim2) {
    if (ini1 >= fim1 || ini2 >= fim2) return 0;
    return !(fim1 <= ini2 || ini1 >= fim2);
}

static void pool_reset(PoolOcupacao* pool) {
    for (int32_t i = 0; i < pool->num_entidades; i++) {
        pool->head[i] = -1;
    }
    pool->used = 0;
}

static int pool_tem_conflito(const PoolOcupacao* pool, int32_t ent_idx, int32_t dia, int32_t ini, int32_t fim) {
    if (ent_idx < 0 || ent_idx >= pool->num_entidades) return 0;
    for (int32_t cur = pool->head[ent_idx]; cur != -1; cur = pool->next[cur]) {
        uint32_t packed = pool->slots[cur];
        if ((int32_t)((packed >> 22) & 0x7U) == dia) {
            int32_t s_ini = (int32_t)((packed >> 11) & 0x7FFU);
            int32_t s_fim = (int32_t)(packed & 0x7FFU);
            if (verificar_sobreposicao(ini, fim, s_ini, s_fim)) return 1;
        }
    }
    return 0;
}

static void pool_adicionar(PoolOcupacao* pool, int32_t ent_idx, int32_t dia, int32_t ini, int32_t fim) {
    if (ent_idx < 0 || ent_idx >= pool->num_entidades || pool->used >= pool->capacidade_slots) return;
    int32_t idx = pool->used++;
    pool->slots[idx] = empacotar_slot(dia, ini, fim);
    pool->next[idx] = pool->head[ent_idx];
    pool->head[ent_idx] = idx;
}

static int comparar_prof_pair(const void* a, const void* b) {
    const ProfTurmaPair* pa = (const ProfTurmaPair*)a;
    const ProfTurmaPair* pb = (const ProfTurmaPair*)b;
    if (pa->professor_id != pb->professor_id) return (pa->professor_id < pb->professor_id) ? -1 : 1;
    return (pa->turma_idx < pb->turma_idx) ? -1 : (pa->turma_idx > pb->turma_idx);
}

static int mapear_professores(const TurmaC* turmas, int num_turmas, int32_t* prof_idx_out, int32_t* num_profs_out) {
    for (int i = 0; i < num_turmas; i++) prof_idx_out[i] = -1;
    ProfTurmaPair* pares = (ProfTurmaPair*)malloc((size_t)num_turmas * sizeof(ProfTurmaPair));
    if (!pares) return -1;

    int count = 0;
    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].professor_id > 0) {
            pares[count].professor_id = turmas[i].professor_id;
            pares[count].turma_idx = i;
            count++;
        }
    }

    int32_t num_profs = 0;
    if (count > 0) {
        qsort(pares, (size_t)count, sizeof(ProfTurmaPair), comparar_prof_pair);
        int32_t ultimo_id = pares[0].professor_id;
        prof_idx_out[pares[0].turma_idx] = 0;
        num_profs = 1;
        for (int k = 1; k < count; k++) {
            if (pares[k].professor_id != ultimo_id) {
                ultimo_id = pares[k].professor_id;
                num_profs++;
            }
            prof_idx_out[pares[k].turma_idx] = num_profs - 1;
        }
    }

    free(pares);
    *num_profs_out = num_profs;
    return 0;
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

static void ordenar_turmas_bfd(int* ordem, int num_turmas, const TurmaC* turmas) {
    for (int i = 0; i < num_turmas; i++) {
        ordem[i] = i;
    }
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
}

static void gerar_ordem_turmas(int* ordem, int num_turmas, const int* ordem_base_bfd, int iteracao) {
    memcpy(ordem, ordem_base_bfd, (size_t)num_turmas * sizeof(int));

    if (iteracao > 0 && num_turmas > 1) {
        unsigned int seed = (unsigned int)iteracao * 2654435761U + 13U;
        // Perturbacoes locais sobre a base Best-Fit Decreasing
        int num_trocas = 1 + (int)(prng_next(&seed) % (unsigned int)(num_turmas > 10 ? 5 : 2));
        for (int k = 0; k < num_trocas; k++) {
            int p1 = (int)(prng_next(&seed) % (unsigned int)num_turmas);
            int p2 = (int)(prng_next(&seed) % (unsigned int)num_turmas);
            int tmp = ordem[p1];
            ordem[p1] = ordem[p2];
            ordem[p2] = tmp;
        }
    }
}

static void executar_tentativa(
    const TurmaC* turmas,
    int num_turmas,
    const SalaC* salas,
    int num_salas,
    const int* ordem,
    const int32_t* prof_idx,
    AlocacaoItemC* resultado_local,
    PoolOcupacao* pool_salas,
    PoolOcupacao* pool_profs,
    int* total_alocado_out,
    int* total_pendente_out,
    long long* total_desperdicio_out
) {
    pool_reset(pool_salas);
    pool_reset(pool_profs);

    int alocados = 0;
    int pendentes = 0;
    long long desperdicio = 0;

    for (int idx = 0; idx < num_turmas; idx++) {
        int i = ordem[idx];
        const TurmaC* t = &turmas[i];
        int32_t p_idx = prof_idx[i];

        int melhor_sala_idx = -1;
        long long menor_desperdicio = 9223372036854775807LL;
        int desperdicio_real_melhor = 0;

        int horario_ok = (t->num_matriculados >= 0) &&
                         slot_valido(t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min);
        int prof_livre = horario_ok &&
                         (p_idx < 0 || !pool_tem_conflito(
                             pool_profs, p_idx,
                             t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min
                         ));

        if (prof_livre) {
            for (int j = 0; j < num_salas; j++) {
                const SalaC* s = &salas[j];

                if (s->capacidade < t->num_matriculados) continue;
                if (!tipo_compativel(t->tipo_exigido, s->tipo)) continue;
                if (!turno_compativel(t->turno, s->turnos_mask)) continue;

                if (pool_tem_conflito(pool_salas, j, t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min)) {
                    continue;
                }

                int desp = s->capacidade - t->num_matriculados;
                long long desp_ajustado = (long long)desp;

                // Penalidades para preservar espacos nobres
                if (t->tipo_exigido == TIPO_SALA_REGULAR && s->tipo == TIPO_SALA_LABORATORIO) {
                    desp_ajustado += 500LL;
                } else if (t->tipo_exigido == TIPO_SALA_REGULAR && (s->tipo == TIPO_SALA_AUDITORIO || s->tipo == TIPO_SALA_REUNIAO)) {
                    desp_ajustado += 300LL;
                }

                if (desp_ajustado < menor_desperdicio) {
                    menor_desperdicio = desp_ajustado;
                    desperdicio_real_melhor = desp;
                    melhor_sala_idx = j;
                }
            }
        }

        resultado_local[i].turma_id = t->id;
        resultado_local[i].dia_semana = t->dia_semana_sugerido;
        resultado_local[i].hora_inicio_min = t->hora_inicio_min;
        resultado_local[i].hora_fim_min = t->hora_fim_min;

        if (melhor_sala_idx >= 0) {
            const SalaC* s = &salas[melhor_sala_idx];
            resultado_local[i].sala_id = s->id;
            resultado_local[i].score_desperdicio = desperdicio_real_melhor;
            pool_adicionar(pool_salas, melhor_sala_idx, t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min);
            if (p_idx >= 0) {
                pool_adicionar(pool_profs, p_idx, t->dia_semana_sugerido, t->hora_inicio_min, t->hora_fim_min);
            }
            alocados++;
            desperdicio += menor_desperdicio;
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

static int executar_busca_combinatoria(
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

    int* ordem_base_bfd = (int*)malloc((size_t)num_turmas * sizeof(int));
    int32_t* prof_idx = (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t));
    int32_t num_profs = 0;

    if (!ordem_base_bfd || !prof_idx || mapear_professores(turmas, num_turmas, prof_idx, &num_profs) != 0) {
        free(ordem_base_bfd);
        free(prof_idx);
        *total_alocado_out = 0;
        *total_pendente_out = num_turmas;
        return -2;
    }
    ordenar_turmas_bfd(ordem_base_bfd, num_turmas, turmas);

    long long melhor_score_global = -9223372036854775807LL;
    int melhor_iter_global = num_iteracoes + 1;
    int global_alocados = 0;
    int global_pendentes = num_turmas;
    int alocacao_falhou = 0;

    #pragma omp parallel num_threads(num_threads) default(none) \
        shared(turmas, num_turmas, salas, num_salas, num_iteracoes, ordem_base_bfd, \
               prof_idx, num_profs, melhor_resultado, melhor_score_global, \
               melhor_iter_global, global_alocados, global_pendentes, alocacao_falhou)
    {
        int* ordem_local = (int*)malloc((size_t)num_turmas * sizeof(int));
        AlocacaoItemC* res_local = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
        AlocacaoItemC* res_melhor_thread = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));

        int32_t* sala_head = (int32_t*)malloc((size_t)num_salas * sizeof(int32_t));
        uint32_t* sala_slots = (uint32_t*)malloc((size_t)num_turmas * sizeof(uint32_t));
        int32_t* sala_next = (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t));

        int32_t* prof_head = (num_profs > 0) ? (int32_t*)malloc((size_t)num_profs * sizeof(int32_t)) : NULL;
        uint32_t* prof_slots = (num_profs > 0) ? (uint32_t*)malloc((size_t)num_turmas * sizeof(uint32_t)) : NULL;
        int32_t* prof_next = (num_profs > 0) ? (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t)) : NULL;

        int buffers_ok = ordem_local && res_local && res_melhor_thread &&
                         sala_head && sala_slots && sala_next &&
                         (num_profs == 0 || (prof_head && prof_slots && prof_next));

        if (!buffers_ok) {
            #pragma omp atomic write
            alocacao_falhou = 1;
        }
        // Barreira garante entrada uniforme no #pragma omp for (evita deadlock em OOM parcial)
        #pragma omp barrier

        if (!alocacao_falhou) {
            PoolOcupacao pool_salas = {sala_head, sala_slots, sala_next, num_salas, num_turmas, 0};
            PoolOcupacao pool_profs = {prof_head, prof_slots, prof_next, num_profs, num_turmas, 0};

            long long melhor_score_thread = -9223372036854775807LL;
            int melhor_iter_thread = num_iteracoes + 1;
            int thread_alocados = 0;
            int thread_pendentes = num_turmas;

            #pragma omp for schedule(dynamic, 16)
            for (int iter = 0; iter < num_iteracoes; iter++) {
                gerar_ordem_turmas(ordem_local, num_turmas, ordem_base_bfd, iter);

                int t_alocados = 0;
                int t_pendentes = 0;
                long long t_desperdicio = 0;

                executar_tentativa(
                    turmas, num_turmas, salas, num_salas, ordem_local, prof_idx,
                    res_local, &pool_salas, &pool_profs,
                    &t_alocados, &t_pendentes, &t_desperdicio
                );

                long long score = (long long)t_alocados * 1000000000LL - t_desperdicio;
                if (score > melhor_score_thread || (score == melhor_score_thread && iter < melhor_iter_thread)) {
                    melhor_score_thread = score;
                    melhor_iter_thread = iter;
                    thread_alocados = t_alocados;
                    thread_pendentes = t_pendentes;
                    memcpy(res_melhor_thread, res_local, (size_t)num_turmas * sizeof(AlocacaoItemC));
                }
            }

            #pragma omp critical
            {
                if (melhor_score_thread > melhor_score_global ||
                    (melhor_score_thread == melhor_score_global && melhor_iter_thread < melhor_iter_global)) {
                    melhor_score_global = melhor_score_thread;
                    melhor_iter_global = melhor_iter_thread;
                    global_alocados = thread_alocados;
                    global_pendentes = thread_pendentes;
                    memcpy(melhor_resultado, res_melhor_thread, (size_t)num_turmas * sizeof(AlocacaoItemC));
                }
            }
        }

        free(prof_next);
        free(prof_slots);
        free(prof_head);
        free(sala_next);
        free(sala_slots);
        free(sala_head);
        free(res_melhor_thread);
        free(res_local);
        free(ordem_local);
    }

    free(prof_idx);
    free(ordem_base_bfd);
    *total_alocado_out = global_alocados;
    *total_pendente_out = global_pendentes;
    return alocacao_falhou ? -2 : 0;
}

static int executar_replay_iteracao(
    const TurmaC* turmas, int32_t num_turmas, const SalaC* salas, int32_t num_salas,
    const int32_t* ordem_base_bfd, const int32_t* prof_idx, int32_t num_profs, int32_t iteracao,
    AlocacaoItemC* resultado_out, int* total_alocado_out, int* total_pendente_out
) {
    int* ordem = (int*)malloc((size_t)num_turmas * sizeof(int));
    int32_t* s_head = (int32_t*)malloc((size_t)num_salas * sizeof(int32_t));
    uint32_t* s_slots = (uint32_t*)malloc((size_t)num_turmas * sizeof(uint32_t));
    int32_t* s_next = (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t));
    int32_t* p_head = (num_profs > 0) ? (int32_t*)malloc((size_t)num_profs * sizeof(int32_t)) : NULL;
    uint32_t* p_slots = (num_profs > 0) ? (uint32_t*)malloc((size_t)num_turmas * sizeof(uint32_t)) : NULL;
    int32_t* p_next = (num_profs > 0) ? (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t)) : NULL;
    int ok = ordem && s_head && s_slots && s_next && (num_profs == 0 || (p_head && p_slots && p_next));
    if (ok) {
        PoolOcupacao ps = {s_head, s_slots, s_next, num_salas, num_turmas, 0};
        PoolOcupacao pp = {p_head, p_slots, p_next, num_profs, num_turmas, 0};
        long long desp = 0;
        gerar_ordem_turmas(ordem, num_turmas, ordem_base_bfd, iteracao);
        executar_tentativa(turmas, num_turmas, salas, num_salas, ordem, prof_idx, resultado_out, &ps, &pp, total_alocado_out, total_pendente_out, &desp);
    }
    free(p_next); free(p_slots); free(p_head); free(s_next); free(s_slots); free(s_head); free(ordem);
    return ok ? 0 : -2;
}

int otimizar_alocacao_salas_v2(const TurmaC* turmas, int32_t num_turmas, const SalaC* salas, int32_t num_salas, int32_t max_threads, int32_t backend_alvo, int32_t medir_baseline_seq, AlocacaoItemC* resultado_out, MetricasAlocacaoC* metricas_out) {
    if (num_turmas <= 0 || num_salas <= 0 || !turmas || !salas || !resultado_out || backend_alvo < MOTOR_BACKEND_AUTO || backend_alvo > MOTOR_BACKEND_OPENCL) return -1;
    int threads_alvo = (max_threads > 0) ? max_threads : omp_get_num_procs();
    if (threads_alvo < 1) threads_alvo = 1;
    int num_iteracoes = (num_turmas <= 20) ? ((num_turmas <= 15) ? 6000 : 2500) : ((num_turmas >= 100) ? 1200 : 800);
    double t_seq_ms = 0.0, t_par_ms = 0.0, t_kernel_ms = 0.0, t_transf_ms = 0.0;
    int par_alocado = 0, par_pendente = 0;
    int32_t backend_usado = backend_alvo, fallback = 0;
    char dev_nome[64] = {0};

    if (medir_baseline_seq != 0 && backend_alvo != MOTOR_BACKEND_CPU_SEQUENCIAL) {
        AlocacaoItemC* res_seq = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
        if (!res_seq) return -2;
        int seq_a = 0, seq_p = 0;
        double t0 = omp_get_wtime();
        int rc_seq = executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, 1, num_iteracoes, res_seq, &seq_a, &seq_p);
        t_seq_ms = (omp_get_wtime() - t0) * 1000.0;
        free(res_seq);
        if (rc_seq != 0) return rc_seq;
    }

    int rc = 0;
    if (backend_alvo == MOTOR_BACKEND_OPENCL || backend_alvo == MOTOR_BACKEND_AUTO) {
        int32_t* ordem_base = (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t));
        int32_t* prof_idx = (int32_t*)malloc((size_t)num_turmas * sizeof(int32_t));
        int32_t num_profs = 0, best_iter = 0;
        if (!ordem_base || !prof_idx || mapear_professores(turmas, num_turmas, prof_idx, &num_profs) != 0) { free(ordem_base); free(prof_idx); return -2; }
        ordenar_turmas_bfd(ordem_base, num_turmas, turmas);
        double t0 = omp_get_wtime();
        rc = motor_opencl_executar_busca(turmas, num_turmas, salas, num_salas, ordem_base, prof_idx, num_profs, num_iteracoes, &best_iter, &t_kernel_ms, &t_transf_ms, dev_nome, sizeof(dev_nome));
        if (rc == 0) {
            rc = executar_replay_iteracao(turmas, num_turmas, salas, num_salas, ordem_base, prof_idx, num_profs, best_iter, resultado_out, &par_alocado, &par_pendente);
            t_par_ms = (omp_get_wtime() - t0) * 1000.0;
            backend_usado = MOTOR_BACKEND_OPENCL;
        }
        free(ordem_base); free(prof_idx);
        if (rc != 0) {
            if (backend_alvo == MOTOR_BACKEND_OPENCL) return (rc == -2) ? -2 : -3;
            fallback = 1; t_kernel_ms = 0.0; t_transf_ms = 0.0; dev_nome[0] = '\0';
        }
    }

    if (backend_alvo == MOTOR_BACKEND_CPU_SEQUENCIAL || backend_alvo == MOTOR_BACKEND_OPENMP || fallback) {
        int th = (backend_alvo == MOTOR_BACKEND_CPU_SEQUENCIAL) ? 1 : threads_alvo;
        double t0 = omp_get_wtime();
        rc = executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, th, num_iteracoes, resultado_out, &par_alocado, &par_pendente);
        t_par_ms = (omp_get_wtime() - t0) * 1000.0;
        if (rc != 0) return rc;
        if (backend_alvo == MOTOR_BACKEND_CPU_SEQUENCIAL) { threads_alvo = 1; backend_usado = MOTOR_BACKEND_CPU_SEQUENCIAL; if (medir_baseline_seq != 0) t_seq_ms = t_par_ms; }
        else backend_usado = MOTOR_BACKEND_OPENMP;
    }

    if (metricas_out) {
        memset(metricas_out, 0, sizeof(*metricas_out));
        metricas_out->tempo_sequencial_ms = (medir_baseline_seq != 0) ? t_seq_ms : 0.0;
        metricas_out->tempo_paralelo_ms = t_par_ms;
        metricas_out->tempo_kernel_ms = t_kernel_ms;
        metricas_out->tempo_transferencia_ms = t_transf_ms;
        metricas_out->threads_utilizadas = (backend_usado == MOTOR_BACKEND_OPENCL) ? 1 : threads_alvo;
        metricas_out->total_alocado = par_alocado;
        metricas_out->total_pendente = par_pendente;
        metricas_out->backend_solicitado = backend_alvo;
        metricas_out->backend_utilizado = backend_usado;
        metricas_out->fallback_ativado = fallback;
        memcpy(metricas_out->dispositivo_opencl, dev_nome, sizeof(metricas_out->dispositivo_opencl));
        if (medir_baseline_seq != 0 && t_seq_ms > 0.0 && t_par_ms > 0.0) {
            metricas_out->speedup = t_seq_ms / t_par_ms;
            int32_t k_eff = metricas_out->threads_utilizadas;
            double k = (double)k_eff;
            metricas_out->eficiencia = (metricas_out->speedup / k) * 100.0;
            if (k_eff > 1) {
                double f = (k * (metricas_out->speedup - 1.0)) / (metricas_out->speedup * (k - 1.0));
                metricas_out->fracao_amdahl = (f < 0.0) ? 0.0 : ((f > 1.0) ? 1.0 : f);
            } else metricas_out->fracao_amdahl = 1.0;
        }
    }
    return 0;
}

int otimizar_alocacao_salas(const TurmaC* turmas, int num_turmas, const SalaC* salas, int num_salas, int max_threads, AlocacaoItemC* resultado_out, MetricasAlocacaoC* metricas_out) {
    return otimizar_alocacao_salas_v2(turmas, (int32_t)num_turmas, salas, (int32_t)num_salas, (int32_t)max_threads, MOTOR_BACKEND_OPENMP, 1, resultado_out, metricas_out);
}

int executar_benchmark_cenario_v2(int32_t num_turmas, int32_t num_salas, int32_t num_threads, int32_t backend_alvo, MetricasAlocacaoC* metricas_out) {
    if (num_turmas <= 0 || num_salas <= 0 || !metricas_out) return -1;
    TurmaC* turmas = (TurmaC*)malloc((size_t)num_turmas * sizeof(TurmaC));
    SalaC* salas = (SalaC*)malloc((size_t)num_salas * sizeof(SalaC));
    AlocacaoItemC* resultados = (AlocacaoItemC*)malloc((size_t)num_turmas * sizeof(AlocacaoItemC));
    if (!turmas || !salas || !resultados) { free(turmas); free(salas); free(resultados); return -2; }
    for (int j = 0; j < num_salas; j++) {
        salas[j].id = j + 1; salas[j].capacidade = 30 + (j % 8) * 10;
        salas[j].tipo = (j % 5 == 0) ? TIPO_SALA_LABORATORIO : TIPO_SALA_REGULAR;
        salas[j].turnos_mask = TURNO_MASK_MATUTINO | TURNO_MASK_VESPERTINO | TURNO_MASK_NOTURNO;
    }
    for (int i = 0; i < num_turmas; i++) {
        turmas[i].id = i + 1; turmas[i].num_matriculados = 25 + (i % 6) * 10;
        turmas[i].tipo_exigido = (i % 5 == 0) ? TIPO_SALA_LABORATORIO : TIPO_SALA_REGULAR;
        turmas[i].turno = i % 3; turmas[i].dia_semana_sugerido = i % 5; turmas[i].professor_id = 0;
        turmas[i].hora_inicio_min = (turmas[i].turno == TURNO_MATUTINO) ? 480 : ((turmas[i].turno == TURNO_VESPERTINO) ? 840 : 1140);
        turmas[i].hora_fim_min = turmas[i].hora_inicio_min + 120;
    }
    int rc = otimizar_alocacao_salas_v2(turmas, num_turmas, salas, num_salas, num_threads, backend_alvo, 1, resultados, metricas_out);
    free(resultados); free(salas); free(turmas);
    return rc;
}

int executar_benchmark_cenario(int num_turmas, int num_salas, int num_threads, MetricasAlocacaoC* metricas_out) {
    return executar_benchmark_cenario_v2((int32_t)num_turmas, (int32_t)num_salas, (int32_t)num_threads, MOTOR_BACKEND_OPENMP, metricas_out);
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
