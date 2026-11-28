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

typedef struct {
    int id;
    int capacidade;
    int tipo;
    int turnos_mask;
} SalaCL;

typedef struct {
    int id;
    int num_matriculados;
    int tipo_exigido;
    int turno;
    int dia_semana_sugerido;
    int hora_inicio_min;
    int hora_fim_min;
    int professor_id;
} TurmaCL;

static inline uint empacotar_slot_cl(int dia, int ini, int fim) {
    return (((uint)(dia & 0x7)) << 22) |
           (((uint)(ini & 0x7FF)) << 11) |
           ((uint)(fim & 0x7FF));
}

static inline int slot_valido_cl(int dia, int ini, int fim) {
    return (dia >= 0 && dia <= 6 && ini >= 0 && fim <= 1440 && ini < fim);
}

static inline int verificar_sobreposicao_cl(int ini1, int fim1, int ini2, int fim2) {
    if (ini1 >= fim1 || ini2 >= fim2) return 0;
    return !(fim1 <= ini2 || ini1 >= fim2);
}

static inline int turno_compativel_cl(int turma_turno, int sala_turnos_mask) {
    if (turma_turno == TURNO_MATUTINO) return (sala_turnos_mask & TURNO_MASK_MATUTINO) != 0;
    if (turma_turno == TURNO_VESPERTINO) return (sala_turnos_mask & TURNO_MASK_VESPERTINO) != 0;
    if (turma_turno == TURNO_NOTURNO) return (sala_turnos_mask & TURNO_MASK_NOTURNO) != 0;
    if (turma_turno == TURNO_INTEGRAL) {
        return ((sala_turnos_mask & TURNO_MASK_INTEGRAL) != 0) || ((sala_turnos_mask & 7) == 7);
    }
    return 1;
}

static inline int tipo_compativel_cl(int tipo_exigido, int sala_tipo) {
    if (tipo_exigido == TIPO_SALA_LABORATORIO) {
        return sala_tipo == TIPO_SALA_LABORATORIO;
    }
    return 1;
}

static inline uint prng_next_cl(uint* seed) {
    *seed = (*seed * 1103515245U + 12345U) & 0x7fffffffU;
    return *seed;
}

static inline int pool_tem_conflito_cl(
    __global const int* head,
    __global const uint* slots,
    __global const int* next,
    int ent_idx,
    int num_ent,
    int dia,
    int ini,
    int fim
) {
    if (ent_idx < 0 || ent_idx >= num_ent) return 0;
    for (int cur = head[ent_idx]; cur != -1; cur = next[cur]) {
        uint packed = slots[cur];
        if ((int)((packed >> 22) & 0x7U) == dia) {
            int s_ini = (int)((packed >> 11) & 0x7FFU);
            int s_fim = (int)(packed & 0x7FFU);
            if (verificar_sobreposicao_cl(ini, fim, s_ini, s_fim)) return 1;
        }
    }
    return 0;
}

static inline void pool_adicionar_cl(
    __global int* head,
    __global uint* slots,
    __global int* next,
    int* used,
    int cap,
    int ent_idx,
    int num_ent,
    int dia,
    int ini,
    int fim
) {
    if (ent_idx < 0 || ent_idx >= num_ent || *used >= cap) return;
    int idx = (*used)++;
    slots[idx] = empacotar_slot_cl(dia, ini, fim);
    next[idx] = head[ent_idx];
    head[ent_idx] = idx;
}

__kernel void avaliar_alocacoes_multistart(
    __global const TurmaCL* turmas,
    const int num_turmas,
    __global const SalaCL* salas,
    const int num_salas,
    __global const int* ordem_base_bfd,
    __global const int* prof_idx,
    const int num_profs,
    const int num_iteracoes,
    __global int* scratch_ordem,
    __global int* scratch_sala_head,
    __global uint* scratch_sala_slots,
    __global int* scratch_sala_next,
    __global int* scratch_prof_head,
    __global uint* scratch_prof_slots,
    __global int* scratch_prof_next,
    __global long* wg_scores,
    __global int* wg_iters,
    __local long* local_scores,
    __local int* local_iters
) {
    const int gid = (int)get_global_id(0);
    const int gsize = (int)get_global_size(0);
    const uint lid = (uint)get_local_id(0);
    const uint lsize = (uint)get_local_size(0);
    const int group_id = (int)get_group_id(0);

    const size_t wi = (size_t)gid;
    const size_t t_stride = (size_t)num_turmas;
    const size_t s_stride = (size_t)num_salas;
    const size_t p_stride = (size_t)((num_profs > 0) ? num_profs : 1);

    __global int* ordem = scratch_ordem + wi * t_stride;
    __global int* s_head = scratch_sala_head + wi * s_stride;
    __global uint* s_slots = scratch_sala_slots + wi * t_stride;
    __global int* s_next = scratch_sala_next + wi * t_stride;
    __global int* p_head = scratch_prof_head + wi * p_stride;
    __global uint* p_slots = scratch_prof_slots + wi * t_stride;
    __global int* p_next = scratch_prof_next + wi * t_stride;

    long best_score = -9223372036854775807L;
    int best_iter = num_iteracoes;

    for (int iter = gid; iter < num_iteracoes; iter += gsize) {
        for (int k = 0; k < num_turmas; k++) {
            ordem[k] = ordem_base_bfd[k];
        }
        if (iter > 0 && num_turmas > 1) {
            uint seed = (uint)iter * 2654435761U + 13U;
            int num_trocas = 1 + (int)(prng_next_cl(&seed) % (uint)(num_turmas > 10 ? 5 : 2));
            for (int k = 0; k < num_trocas; k++) {
                int p1 = (int)(prng_next_cl(&seed) % (uint)num_turmas);
                int p2 = (int)(prng_next_cl(&seed) % (uint)num_turmas);
                int tmp = ordem[p1];
                ordem[p1] = ordem[p2];
                ordem[p2] = tmp;
            }
        }

        for (int s = 0; s < num_salas; s++) s_head[s] = -1;
        for (int p = 0; p < num_profs; p++) p_head[p] = -1;
        int s_used = 0;
        int p_used = 0;

        int alocados = 0;
        long desperdicio = 0;

        for (int idx = 0; idx < num_turmas; idx++) {
            int i = ordem[idx];
            TurmaCL t = turmas[i];
            int p_i = prof_idx[i];

            int melhor_sala_idx = -1;
            long menor_desperdicio = 9223372036854775807L;

            int horario_ok = (t.num_matriculados >= 0) &&
                             slot_valido_cl(t.dia_semana_sugerido, t.hora_inicio_min, t.hora_fim_min);
            int prof_livre = horario_ok &&
                             (p_i < 0 || !pool_tem_conflito_cl(
                                 p_head, p_slots, p_next, p_i, num_profs,
                                 t.dia_semana_sugerido, t.hora_inicio_min, t.hora_fim_min
                             ));

            if (prof_livre) {
                for (int j = 0; j < num_salas; j++) {
                    SalaCL s = salas[j];
                    if (s.capacidade < t.num_matriculados) continue;
                    if (!tipo_compativel_cl(t.tipo_exigido, s.tipo)) continue;
                    if (!turno_compativel_cl(t.turno, s.turnos_mask)) continue;
                    if (pool_tem_conflito_cl(
                            s_head, s_slots, s_next, j, num_salas,
                            t.dia_semana_sugerido, t.hora_inicio_min, t.hora_fim_min
                        )) {
                        continue;
                    }

                    long desp_ajustado = (long)(s.capacidade - t.num_matriculados);
                    if (t.tipo_exigido == TIPO_SALA_REGULAR && s.tipo == TIPO_SALA_LABORATORIO) {
                        desp_ajustado += 500L;
                    } else if (t.tipo_exigido == TIPO_SALA_REGULAR &&
                               (s.tipo == TIPO_SALA_AUDITORIO || s.tipo == TIPO_SALA_REUNIAO)) {
                        desp_ajustado += 300L;
                    }

                    if (desp_ajustado < menor_desperdicio) {
                        menor_desperdicio = desp_ajustado;
                        melhor_sala_idx = j;
                    }
                }
            }

            if (melhor_sala_idx >= 0) {
                pool_adicionar_cl(
                    s_head, s_slots, s_next, &s_used, num_turmas, melhor_sala_idx, num_salas,
                    t.dia_semana_sugerido, t.hora_inicio_min, t.hora_fim_min
                );
                if (p_i >= 0) {
                    pool_adicionar_cl(
                        p_head, p_slots, p_next, &p_used, num_turmas, p_i, num_profs,
                        t.dia_semana_sugerido, t.hora_inicio_min, t.hora_fim_min
                    );
                }
                alocados++;
                desperdicio += menor_desperdicio;
            }
        }

        long score = (long)alocados * 1000000000L - desperdicio;
        if (score > best_score || (score == best_score && iter < best_iter)) {
            best_score = score;
            best_iter = iter;
        }
    }

    // Reducao deterministica em arvore na memoria __local (lsize potencia de 2)
    local_scores[lid] = best_score;
    local_iters[lid] = best_iter;
    barrier(CLK_LOCAL_MEM_FENCE);

    for (uint stride = lsize >> 1; stride > 0; stride >>= 1) {
        if (lid < stride) {
            long sc_other = local_scores[lid + stride];
            int it_other = local_iters[lid + stride];
            long sc_self = local_scores[lid];
            int it_self = local_iters[lid];
            if (sc_other > sc_self || (sc_other == sc_self && it_other < it_self)) {
                local_scores[lid] = sc_other;
                local_iters[lid] = it_other;
            }
        }
        barrier(CLK_LOCAL_MEM_FENCE);
    }

    if (lid == 0) {
        wg_scores[group_id] = local_scores[0];
        wg_iters[group_id] = local_iters[0];
    }
}
