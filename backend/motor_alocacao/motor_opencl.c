#include "motor_opencl.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

#ifdef USE_OPENCL
#define CL_TARGET_OPENCL_VERSION 120
#include <CL/cl.h>
#ifndef CL_DEVICE_BOARD_NAME_AMD
#define CL_DEVICE_BOARD_NAME_AMD 0x4038
#endif
#define MAX_CL_STR_BYTES (1024U * 1024U)

typedef struct {
    cl_platform_id platform;
    cl_device_id device;
    cl_context context;
    cl_command_queue queue;
    cl_program program;
    cl_kernel kernel;
    int inicializado;
    char device_name[64];
} MotorOpenCLState;

static MotorOpenCLState g_ocl;

static void copiar_str_segura(char* dst, size_t cap, const char* src) {
    if (!dst || cap == 0) return;
    if (!src) { dst[0] = '\0'; return; }
    size_t len = strlen(src);
    while (len > 0 && (src[len - 1] == ' ' || src[len - 1] == '\t' || src[len - 1] == '\n' || src[len - 1] == '\r')) len--;
    if (len >= cap) len = cap - 1;
    memcpy(dst, src, len);
    dst[len] = '\0';
}

static int ler_dev_str(cl_device_id dev, cl_device_info param, char* dst, size_t cap) {
    if (!dst || cap == 0) return 0;
    size_t sz = 0;
    if (clGetDeviceInfo(dev, param, 0, NULL, &sz) != CL_SUCCESS || sz == 0 || sz > MAX_CL_STR_BYTES) return 0;
    char* tmp = (char*)malloc(sz + 1);
    if (!tmp) return 0;
    int ok = (clGetDeviceInfo(dev, param, sz, tmp, NULL) == CL_SUCCESS);
    if (ok) { tmp[sz] = '\0'; copiar_str_segura(dst, cap, tmp); }
    free(tmp);
    return ok && dst[0] != '\0';
}

static void ler_plat_str(cl_platform_id plat, cl_platform_info param, char* dst, size_t cap) {
    if (!dst || cap == 0) return;
    size_t sz = 0;
    if (clGetPlatformInfo(plat, param, 0, NULL, &sz) != CL_SUCCESS || sz == 0 || sz > MAX_CL_STR_BYTES) return;
    char* tmp = (char*)malloc(sz + 1);
    if (!tmp) return;
    if (clGetPlatformInfo(plat, param, sz, tmp, NULL) == CL_SUCCESS) { tmp[sz] = '\0'; copiar_str_segura(dst, cap, tmp); }
    free(tmp);
}

static void obter_nome_dispositivo(cl_device_id dev, char* dst, size_t cap) {
    // Prioriza nome comercial da placa em GPUs AMD (fallback para CL_DEVICE_NAME).
    if (ler_dev_str(dev, CL_DEVICE_BOARD_NAME_AMD, dst, cap) || ler_dev_str(dev, CL_DEVICE_NAME, dst, cap)) return;
    copiar_str_segura(dst, cap, "Unknown OpenCL Device");
}

static void preencher_device_info(cl_platform_id plat, cl_device_id dev, OpenCLDeviceInfoC* info) {
    memset(info, 0, sizeof(*info));
    size_t wg = 0;
    cl_device_type dtype = 0;
    cl_uint cu = 0;
    cl_ulong gmem = 0;
    ler_plat_str(plat, CL_PLATFORM_NAME, info->platform_name, sizeof(info->platform_name));
    obter_nome_dispositivo(dev, info->device_name, sizeof(info->device_name));
    if (clGetDeviceInfo(dev, CL_DEVICE_TYPE, sizeof(dtype), &dtype, NULL) == CL_SUCCESS) {
        const char* label = (dtype & CL_DEVICE_TYPE_GPU) ? "GPU" : ((dtype & CL_DEVICE_TYPE_ACCELERATOR) ? "ACCELERATOR" : "CPU");
        copiar_str_segura(info->device_type, sizeof(info->device_type), label);
    }
    ler_dev_str(dev, CL_DEVICE_OPENCL_C_VERSION, info->opencl_c_version, sizeof(info->opencl_c_version));
    if (clGetDeviceInfo(dev, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cu), &cu, NULL) == CL_SUCCESS) info->compute_units = (uint32_t)cu;
    if (clGetDeviceInfo(dev, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(gmem), &gmem, NULL) == CL_SUCCESS) {
        cl_ulong mb = gmem / (1024ULL * 1024ULL);
        info->global_mem_mb = (mb > UINT32_MAX) ? UINT32_MAX : (uint32_t)mb;
    }
    if (clGetDeviceInfo(dev, CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(wg), &wg, NULL) == CL_SUCCESS) info->max_work_group_size = (uint64_t)wg;
}

static int enumerar_dispositivos(OpenCLDeviceInfoC* info_out, int32_t max_itens, int32_t* total_out, cl_platform_id* first_plat, cl_device_id* first_dev) {
    cl_uint n_plats = 0;
    if (clGetPlatformIDs(0, NULL, &n_plats) != CL_SUCCESS || n_plats == 0) return -3;
    cl_platform_id* plats = (cl_platform_id*)malloc((size_t)n_plats * sizeof(cl_platform_id));
    if (!plats) return -2;
    if (clGetPlatformIDs(n_plats, plats, NULL) != CL_SUCCESS) { free(plats); return -3; }

    const cl_device_type prio[3] = { CL_DEVICE_TYPE_GPU, CL_DEVICE_TYPE_ACCELERATOR, CL_DEVICE_TYPE_CPU };
    int32_t count = 0;
    int achou = 0;
    for (int p = 0; p < 3 && !(first_dev && achou && !info_out); p++) {
        for (cl_uint i = 0; i < n_plats && !(first_dev && achou && !info_out); i++) {
            cl_uint n_devs = 0;
            if (clGetDeviceIDs(plats[i], prio[p], 0, NULL, &n_devs) != CL_SUCCESS || n_devs == 0) continue;
            cl_device_id* devs = (cl_device_id*)malloc((size_t)n_devs * sizeof(cl_device_id));
            if (!devs) { free(plats); return -2; }
            if (clGetDeviceIDs(plats[i], prio[p], n_devs, devs, NULL) == CL_SUCCESS) {
                for (cl_uint d = 0; d < n_devs; d++) {
                    cl_bool avail = CL_FALSE;
                    if (clGetDeviceInfo(devs[d], CL_DEVICE_AVAILABLE, sizeof(avail), &avail, NULL) != CL_SUCCESS || avail != CL_TRUE) continue;
                    if (!achou && first_plat && first_dev) { *first_plat = plats[i]; *first_dev = devs[d]; achou = 1; }
                    if (info_out && count < max_itens) preencher_device_info(plats[i], devs[d], &info_out[count++]);
                }
            }
            free(devs);
        }
    }
    free(plats);
    if (total_out) *total_out = count;
    return (achou || count > 0) ? 0 : -3;
}

static int inicializar_locked(void) {
    if (g_ocl.inicializado) return 0;
    cl_platform_id plat = NULL;
    cl_device_id dev = NULL;
    int rc = enumerar_dispositivos(NULL, 0, NULL, &plat, &dev);
    if (rc != 0) return rc;
    cl_int err = CL_SUCCESS;
    cl_context ctx = clCreateContext(NULL, 1, &dev, NULL, NULL, &err);
    if (err != CL_SUCCESS || !ctx) return -3;
    cl_command_queue queue = clCreateCommandQueue(ctx, dev, CL_QUEUE_PROFILING_ENABLE, &err);
    if (err != CL_SUCCESS || !queue) { clReleaseContext(ctx); return -3; }
    g_ocl.platform = plat;
    g_ocl.device = dev;
    g_ocl.context = ctx;
    g_ocl.queue = queue;
    obter_nome_dispositivo(dev, g_ocl.device_name, sizeof(g_ocl.device_name));
    g_ocl.inicializado = 1;
    return 0;
}

int motor_opencl_inicializar(void) {
    int rc = -3;
    #pragma omp critical(motor_opencl_state)
    { rc = inicializar_locked(); }
    return rc;
}

int motor_opencl_esta_disponivel(void) { return motor_opencl_inicializar() == 0 ? 1 : 0; }

int motor_opencl_compilar_kernel(const char* kernel_source, const char* kernel_name, char* build_log_out, size_t build_log_cap) {
    if (build_log_out && build_log_cap > 0) build_log_out[0] = '\0';
    if (!kernel_source || !kernel_name || kernel_source[0] == '\0' || kernel_name[0] == '\0') return -1;
    int rc = -3;
    #pragma omp critical(motor_opencl_state)
    {
        cl_int err = CL_SUCCESS;
        size_t src_len = strlen(kernel_source);
        cl_program prog = (inicializar_locked() == 0) ? clCreateProgramWithSource(g_ocl.context, 1, &kernel_source, &src_len, &err) : NULL;
        if (err == CL_SUCCESS && prog) {
            if (clBuildProgram(prog, 1, &g_ocl.device, NULL, NULL, NULL) != CL_SUCCESS) {
                size_t log_sz = 0;
                if (build_log_out && build_log_cap > 1 && clGetProgramBuildInfo(prog, g_ocl.device, CL_PROGRAM_BUILD_LOG, 0, NULL, &log_sz) == CL_SUCCESS && log_sz > 0 && log_sz <= MAX_CL_STR_BYTES) {
                    char* tmp = (char*)malloc(log_sz + 1);
                    if (tmp) {
                        if (clGetProgramBuildInfo(prog, g_ocl.device, CL_PROGRAM_BUILD_LOG, log_sz, tmp, NULL) == CL_SUCCESS) {
                            tmp[log_sz] = '\0';
                            copiar_str_segura(build_log_out, build_log_cap, tmp);
                        }
                        free(tmp);
                    }
                }
                clReleaseProgram(prog);
            } else {
                cl_kernel kern = clCreateKernel(prog, kernel_name, &err);
                if (err != CL_SUCCESS || !kern) { clReleaseProgram(prog); }
                else {
                    if (g_ocl.kernel) clReleaseKernel(g_ocl.kernel);
                    if (g_ocl.program) clReleaseProgram(g_ocl.program);
                    g_ocl.program = prog;
                    g_ocl.kernel = kern;
                    rc = 0;
                }
            }
        }
    }
    return rc;
}

int obter_status_opencl(int32_t* disponivel_out, char* dispositivo_out, int32_t buf_len) {
    if (!disponivel_out || (dispositivo_out && buf_len <= 0)) return -1;
    #pragma omp critical(motor_opencl_state)
    {
        if (inicializar_locked() == 0) {
            *disponivel_out = 1;
            if (dispositivo_out) copiar_str_segura(dispositivo_out, (size_t)buf_len, g_ocl.device_name);
        } else {
            *disponivel_out = 0;
            if (dispositivo_out) dispositivo_out[0] = '\0';
        }
    }
    return 0;
}

int obter_dispositivos_opencl(OpenCLDeviceInfoC* dispositivos_out, int32_t max_dispositivos, int32_t* total_out) {
    if (!total_out || max_dispositivos < 0 || (max_dispositivos > 0 && !dispositivos_out)) return -1;
    *total_out = 0;
    if (max_dispositivos == 0) return 0;
    return (enumerar_dispositivos(dispositivos_out, max_dispositivos, total_out, NULL, NULL) == -2) ? -2 : 0;
}

void liberar_recursos_motor(void) {
    #pragma omp critical(motor_opencl_state)
    {
        if (g_ocl.kernel) clReleaseKernel(g_ocl.kernel);
        if (g_ocl.program) clReleaseProgram(g_ocl.program);
        if (g_ocl.queue) clReleaseCommandQueue(g_ocl.queue);
        if (g_ocl.context) clReleaseContext(g_ocl.context);
        memset(&g_ocl, 0, sizeof(g_ocl));
    }
}
#else
int motor_opencl_inicializar(void) { return -3; }
int motor_opencl_esta_disponivel(void) { return 0; }
int motor_opencl_compilar_kernel(const char* s, const char* n, char* log_out, size_t cap) {
    if (log_out && cap > 0) log_out[0] = '\0';
    return (!s || !n || s[0] == '\0' || n[0] == '\0') ? -1 : -3;
}
int obter_status_opencl(int32_t* disp, char* dev, int32_t len) {
    if (!disp || (dev && len <= 0)) return -1;
    *disp = 0;
    if (dev) dev[0] = '\0';
    return 0;
}
int obter_dispositivos_opencl(OpenCLDeviceInfoC* out, int32_t max_d, int32_t* tot) {
    if (!tot || max_d < 0 || (max_d > 0 && !out)) return -1;
    *tot = 0;
    return 0;
}
void liberar_recursos_motor(void) {}
#endif
