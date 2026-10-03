#ifndef MOTOR_ALOCACAO_H
#define MOTOR_ALOCACAO_H

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

typedef struct {
    int id;
    int capacidade;
    int tipo;
    int turnos_mask;
} SalaC;

typedef struct {
    int id;
    int num_matriculados;
    int tipo_exigido;
    int turno;
    int dia_semana_sugerido;
    int hora_inicio_min;
    int hora_fim_min;
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
    int padding;
} MetricasAlocacaoC;

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

#endif // MOTOR_ALOCACAO_H
