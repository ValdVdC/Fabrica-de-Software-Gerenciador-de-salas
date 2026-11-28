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
#ifdef __cplusplus
}
#endif
#endif // MOTOR_OPENCL_H
