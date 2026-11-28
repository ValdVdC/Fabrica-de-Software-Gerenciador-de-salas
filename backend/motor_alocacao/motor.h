#ifndef MOTOR_ALOCACAO_H
// Algoritmo: Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel.
// Problema NP-dificil (Timetabling): busca solucoes viaveis em tempo polinomial O(T * S) sem garantia de otimo global.
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
} SalaC;

typedef struct {
    int32_t id;
    int32_t num_matriculados;
    int32_t tipo_exigido;
    int32_t turno;
    int32_t dia_semana_sugerido;
    int32_t hora_inicio_min;
    int32_t hora_fim_min;
    int32_t professor_id; // 0 = sem docente atribuido; >0 = id valido
} TurmaC;

typedef struct {
    int32_t turma_id;
    int32_t sala_id;
    int32_t dia_semana;
    int32_t hora_inicio_min;
    int32_t hora_fim_min;
    int32_t score_desperdicio;
} AlocacaoItemC;

typedef struct {
    double tempo_sequencial_ms;
    double tempo_paralelo_ms;
    double speedup;
    double eficiencia;
    double fracao_amdahl;
    double tempo_kernel_ms;
    double tempo_transferencia_ms;
    int32_t threads_utilizadas;
    int32_t total_alocado;
    int32_t total_pendente;
    int32_t backend_solicitado;
    int32_t backend_utilizado;
    int32_t fallback_ativado;
    char dispositivo_opencl[64];
} MetricasAlocacaoC;

typedef struct {
    char platform_name[64];
    char device_name[64];
    char device_type[16];
    char opencl_c_version[32];
    uint32_t compute_units;
    uint32_t global_mem_mb;
    uint64_t max_work_group_size;
} OpenCLDeviceInfoC;

#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(SalaC) == 16, "SalaC deve ter 16 bytes");
_Static_assert(sizeof(TurmaC) == 32, "TurmaC deve ter 32 bytes");
_Static_assert(sizeof(AlocacaoItemC) == 24, "AlocacaoItemC deve ter 24 bytes");
_Static_assert(sizeof(MetricasAlocacaoC) == 144, "MetricasAlocacaoC deve ter 144 bytes");
_Static_assert(sizeof(OpenCLDeviceInfoC) == 192, "OpenCLDeviceInfoC deve ter 192 bytes");
#endif

int otimizar_alocacao_salas_v2(const TurmaC* turmas, int32_t num_turmas, const SalaC* salas, int32_t num_salas, int32_t max_threads, int32_t backend_alvo, int32_t medir_baseline_seq, AlocacaoItemC* resultado_out, MetricasAlocacaoC* metricas_out);
int executar_benchmark_cenario_v2(int32_t num_turmas, int32_t num_salas, int32_t num_threads, int32_t backend_alvo, MetricasAlocacaoC* metricas_out);
int obter_status_opencl(int32_t* disponivel_out, char* dispositivo_out, int32_t buf_len);
int obter_dispositivos_opencl(OpenCLDeviceInfoC* dispositivos_out, int32_t max_dispositivos, int32_t* total_out);
void liberar_recursos_motor(void);

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
