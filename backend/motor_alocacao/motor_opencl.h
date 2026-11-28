#ifndef MOTOR_OPENCL_H
#define MOTOR_OPENCL_H
#include <stddef.h>
#include "motor.h"
#ifdef __cplusplus
extern "C" {
#endif
int motor_opencl_inicializar(void);
int motor_opencl_esta_disponivel(void);
int motor_opencl_compilar_kernel(const char* kernel_source, const char* kernel_name, char* build_log_out, size_t build_log_cap);
int motor_opencl_executar_busca(const TurmaC* turmas, int32_t num_turmas, const SalaC* salas, int32_t num_salas, const int32_t* ordem_base_bfd, const int32_t* prof_idx, int32_t num_profs, int32_t num_iteracoes, int32_t* best_iter_out, double* tempo_kernel_ms_out, double* tempo_transferencia_ms_out, char* device_name_out, size_t device_name_cap);
#ifdef __cplusplus
}
#endif
#endif // MOTOR_OPENCL_H
