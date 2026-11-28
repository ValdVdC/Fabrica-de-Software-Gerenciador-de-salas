#include "motor_opencl.h"
#include <limits.h>
#include <stdio.h>
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
    int kernel_alocacao_pronto;
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
                    g_ocl.kernel_alocacao_pronto = 0;
                    rc = 0;
                }
            }
        }
    }
    return rc;
}

static char* ler_arquivo_kernel(const char* path) {
    FILE* f = path ? fopen(path, "rb") : NULL;
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long sz = ftell(f);
    if (sz <= 0 || (unsigned long)sz > MAX_CL_STR_BYTES) { fclose(f); return NULL; }
    rewind(f);
    char* buf = (char*)malloc((size_t)sz + 1);
    size_t lido = buf ? fread(buf, 1, (size_t)sz, f) : 0;
    fclose(f);
    if (!buf || lido != (size_t)sz) { free(buf); return NULL; }
    buf[sz] = '\0';
    return buf;
}

static int garantir_kernel_alocacao_locked(void) {
    if (g_ocl.kernel_alocacao_pronto && g_ocl.kernel) return 0;
    const char* env_path = getenv("MOTOR_KERNEL_PATH");
    char* src = NULL;
    if (env_path && env_path[0] != '\0') {
        src = ler_arquivo_kernel(env_path);
    } else {
        const char* cands[5] = {
            "kernels/alocacao.cl", "motor_alocacao/kernels/alocacao.cl", "backend/motor_alocacao/kernels/alocacao.cl",
            "/opt/sigaas/motor/alocacao.cl", "/opt/sigaas/motor/kernels/alocacao.cl"
        };
        for (int i = 0; i < 5 && !src; i++) src = ler_arquivo_kernel(cands[i]);
    }
    if (!src) return -3;
    cl_int err = CL_SUCCESS;
    size_t len = strlen(src);
    cl_program prog = clCreateProgramWithSource(g_ocl.context, 1, (const char**)&src, &len, &err);
    free(src);
    if (err != CL_SUCCESS || !prog) return -3;
    if (clBuildProgram(prog, 1, &g_ocl.device, NULL, NULL, NULL) != CL_SUCCESS) { clReleaseProgram(prog); return -3; }
    cl_kernel kern = clCreateKernel(prog, "avaliar_alocacoes_multistart", &err);
    if (err != CL_SUCCESS || !kern) { clReleaseProgram(prog); return -3; }
    if (g_ocl.kernel) clReleaseKernel(g_ocl.kernel);
    if (g_ocl.program) clReleaseProgram(g_ocl.program);
    g_ocl.program = prog; g_ocl.kernel = kern; g_ocl.kernel_alocacao_pronto = 1;
    return 0;
}

static double evento_duracao_ms(cl_event ev) {
    cl_ulong t0 = 0, t1 = 0;
    if (!ev || clGetEventProfilingInfo(ev, CL_PROFILING_COMMAND_START, sizeof(t0), &t0, NULL) != CL_SUCCESS ||
        clGetEventProfilingInfo(ev, CL_PROFILING_COMMAND_END, sizeof(t1), &t1, NULL) != CL_SUCCESS || t1 < t0) return 0.0;
    return (double)(t1 - t0) * 1e-6;
}

int motor_opencl_executar_busca(const TurmaC* turmas, int32_t num_turmas, const SalaC* salas, int32_t num_salas, const int32_t* ordem_base_bfd, const int32_t* prof_idx, int32_t num_profs, int32_t num_iteracoes, int32_t* best_iter_out, double* tempo_kernel_ms_out, double* tempo_transferencia_ms_out, char* device_name_out, size_t device_name_cap) {
    if (!turmas || !salas || !ordem_base_bfd || !prof_idx || !best_iter_out || num_turmas <= 0 || num_salas <= 0 || num_profs < 0 || num_iteracoes <= 0) return -1;
    int rc = -3;
    #pragma omp critical(motor_opencl_state)
    {
        cl_mem bufs[13] = {0};
        cl_event evs[7] = {0};
        cl_long* wg_scores = NULL;
        cl_int* wg_iters = NULL;
        if (inicializar_locked() == 0 && garantir_kernel_alocacao_locked() == 0) {
            size_t max_wg = 64, local_mem = 4096, lsize = 1;
            cl_uint cu = 1;
            cl_ulong max_alloc = 0, dev_local_mem = 0;
            if (clGetKernelWorkGroupInfo(g_ocl.kernel, g_ocl.device, CL_KERNEL_WORK_GROUP_SIZE, sizeof(max_wg), &max_wg, NULL) != CL_SUCCESS || max_wg == 0) max_wg = 1;
            if (clGetDeviceInfo(g_ocl.device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cu), &cu, NULL) != CL_SUCCESS || cu == 0) cu = 1;
            clGetDeviceInfo(g_ocl.device, CL_DEVICE_MAX_MEM_ALLOC_SIZE, sizeof(max_alloc), &max_alloc, NULL);
            if (clGetDeviceInfo(g_ocl.device, CL_DEVICE_LOCAL_MEM_SIZE, sizeof(dev_local_mem), &dev_local_mem, NULL) == CL_SUCCESS && dev_local_mem > 0) local_mem = (size_t)dev_local_mem;

            size_t lim = (max_wg < 64) ? max_wg : 64;
            while (lsize <= lim / 2) lsize <<= 1;
            while (lsize > 1 && lsize * (sizeof(cl_long) + sizeof(cl_int)) > local_mem) lsize >>= 1;
            size_t p_str = (size_t)(num_profs > 0 ? num_profs : 1), nt_u = (size_t)num_turmas, ns_u = (size_t)num_salas;
            size_t max_str = (nt_u > ns_u) ? nt_u : ns_u;
            if (p_str > max_str) max_str = p_str;
            size_t num_groups = (size_t)(cu * 2U);
            if (num_groups > 16) num_groups = 16;
            while (num_groups > 1 && num_groups * lsize > 1024) num_groups--;
            while (num_groups > 1 && max_alloc > 0 && (cl_ulong)(num_groups * lsize) * (cl_ulong)max_str * 4ULL > max_alloc / 2ULL) num_groups--;
            size_t gsize = num_groups * lsize;
            size_t sz[13] = {
                nt_u * sizeof(TurmaC), ns_u * sizeof(SalaC), nt_u * sizeof(int32_t), nt_u * sizeof(int32_t),
                gsize * nt_u * sizeof(cl_int), gsize * ns_u * sizeof(cl_int), gsize * nt_u * sizeof(cl_uint), gsize * nt_u * sizeof(cl_int),
                gsize * p_str * sizeof(cl_int), gsize * nt_u * sizeof(cl_uint), gsize * nt_u * sizeof(cl_int),
                num_groups * sizeof(cl_long), num_groups * sizeof(cl_int)
            };
            cl_int err = CL_SUCCESS;
            for (int i = 0; i < 13 && err == CL_SUCCESS; i++) {
                cl_mem_flags fl = (i < 4) ? CL_MEM_READ_ONLY : ((i >= 11) ? CL_MEM_WRITE_ONLY : CL_MEM_READ_WRITE);
                bufs[i] = clCreateBuffer(g_ocl.context, fl, sz[i], NULL, &err);
            }
            wg_scores = (cl_long*)malloc(sz[11]);
            wg_iters = (cl_int*)malloc(sz[12]);
            if (err == CL_SUCCESS && wg_scores && wg_iters) {
                const void* h2d[4] = { turmas, salas, ordem_base_bfd, prof_idx };
                for (int i = 0; i < 4 && err == CL_SUCCESS; i++) err = clEnqueueWriteBuffer(g_ocl.queue, bufs[i], CL_FALSE, 0, sz[i], h2d[i], 0, NULL, &evs[i]);
                cl_int nt = num_turmas, ns = num_salas, np = num_profs, ni = num_iteracoes;
                const void* ap[8] = { &bufs[0], &nt, &bufs[1], &ns, &bufs[2], &bufs[3], &np, &ni };
                const size_t as[8] = { sizeof(cl_mem), sizeof(cl_int), sizeof(cl_mem), sizeof(cl_int), sizeof(cl_mem), sizeof(cl_mem), sizeof(cl_int), sizeof(cl_int) };
                for (cl_uint a = 0; a < 8 && err == CL_SUCCESS; a++) err = clSetKernelArg(g_ocl.kernel, a, as[a], ap[a]);
                for (int i = 4; i < 13 && err == CL_SUCCESS; i++) err = clSetKernelArg(g_ocl.kernel, (cl_uint)(i + 4), sizeof(cl_mem), &bufs[i]);
                if (err == CL_SUCCESS) err = clSetKernelArg(g_ocl.kernel, 17, lsize * sizeof(cl_long), NULL);
                if (err == CL_SUCCESS) err = clSetKernelArg(g_ocl.kernel, 18, lsize * sizeof(cl_int), NULL);
                if (err == CL_SUCCESS) err = clEnqueueNDRangeKernel(g_ocl.queue, g_ocl.kernel, 1, NULL, &gsize, &lsize, 0, NULL, &evs[4]);
                if (err == CL_SUCCESS) err = clEnqueueReadBuffer(g_ocl.queue, bufs[11], CL_FALSE, 0, sz[11], wg_scores, 0, NULL, &evs[5]);
                if (err == CL_SUCCESS) err = clEnqueueReadBuffer(g_ocl.queue, bufs[12], CL_FALSE, 0, sz[12], wg_iters, 0, NULL, &evs[6]);
                if (err == CL_SUCCESS) err = clFinish(g_ocl.queue);
                if (err == CL_SUCCESS) {
                    cl_long best_sc = -9223372036854775807LL;
                    cl_int best_it = num_iteracoes;
                    for (size_t g = 0; g < num_groups; g++) {
                        if (wg_scores[g] > best_sc || (wg_scores[g] == best_sc && wg_iters[g] < best_it)) { best_sc = wg_scores[g]; best_it = wg_iters[g]; }
                    }
                    *best_iter_out = (best_it >= 0 && best_it < num_iteracoes) ? best_it : 0;
                    if (tempo_kernel_ms_out) *tempo_kernel_ms_out = evento_duracao_ms(evs[4]);
                    if (tempo_transferencia_ms_out) *tempo_transferencia_ms_out = evento_duracao_ms(evs[0]) + evento_duracao_ms(evs[1]) + evento_duracao_ms(evs[2]) + evento_duracao_ms(evs[3]) + evento_duracao_ms(evs[5]) + evento_duracao_ms(evs[6]);
                    if (device_name_out && device_name_cap > 0) copiar_str_segura(device_name_out, device_name_cap, g_ocl.device_name);
                    rc = 0;
                } else if (evs[0]) {
                    clFinish(g_ocl.queue);
                }
            }
        }
        free(wg_iters); free(wg_scores);
        for (int i = 0; i < 7; i++) if (evs[i]) clReleaseEvent(evs[i]);
        for (int i = 0; i < 13; i++) if (bufs[i]) clReleaseMemObject(bufs[i]);
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
int motor_opencl_executar_busca(
    const TurmaC* t, int32_t nt, const SalaC* s, int32_t ns,
    const int32_t* ord, const int32_t* pidx, int32_t np, int32_t ni,
    int32_t* best_it, double* tk, double* tt, char* dev, size_t cap
) {
    (void)tk; (void)tt; (void)dev; (void)cap;
    return (!t || !s || !ord || !pidx || !best_it || nt <= 0 || ns <= 0 || np < 0 || ni <= 0) ? -1 : -3;
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
