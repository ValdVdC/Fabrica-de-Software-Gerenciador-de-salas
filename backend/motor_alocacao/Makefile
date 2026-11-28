CC = gcc
BASE_CFLAGS = -Wall -Wextra -Werror -pedantic -std=c11 -O3 -fPIC -fopenmp
BASE_LDFLAGS = -shared -fopenmp

# Deteccao automatica de suporte a OpenCL (Linux/Docker e Windows MSYS2 UCRT64)
ifndef USE_OPENCL
  ifneq ($(wildcard /usr/include/CL/cl.h /usr/local/include/CL/cl.h /ucrt64/include/CL/cl.h C:/msys64/ucrt64/include/CL/cl.h),)
    USE_OPENCL = 1
  else
    USE_OPENCL = 0
  endif
endif

ifeq ($(USE_OPENCL),1)
  OPENCL_CFLAGS = -DUSE_OPENCL
  OPENCL_LDFLAGS = -lOpenCL
else
  OPENCL_CFLAGS =
  OPENCL_LDFLAGS =
endif

CFLAGS = $(BASE_CFLAGS) $(OPENCL_CFLAGS)
LDFLAGS = $(BASE_LDFLAGS) $(OPENCL_LDFLAGS)

SOURCES = motor.c motor_opencl.c
HEADERS = motor.h motor_opencl.h

TARGET_SO = motor_alocacao.so
TARGET_DLL = motor_alocacao.dll
BENCHMARK_BIN = benchmark

all: $(TARGET_SO) $(TARGET_DLL) $(BENCHMARK_BIN)

$(TARGET_SO): $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -shared -o $@ $(SOURCES) -fopenmp $(OPENCL_LDFLAGS)

$(TARGET_DLL): $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -shared -o $@ $(SOURCES) -fopenmp $(OPENCL_LDFLAGS)

$(BENCHMARK_BIN): benchmark.c $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -o $@ benchmark.c $(SOURCES) -fopenmp $(OPENCL_LDFLAGS)

clean:
	rm -f *.o *.so *.dll $(BENCHMARK_BIN) $(BENCHMARK_BIN).exe

.PHONY: all clean
