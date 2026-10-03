CC = gcc
CFLAGS = -Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp
LDFLAGS = -shared -fopenmp

TARGET_SO = motor_alocacao.so
TARGET_DLL = motor_alocacao.dll
BENCHMARK_BIN = benchmark

all: $(TARGET_SO) $(TARGET_DLL) $(BENCHMARK_BIN)

$(TARGET_SO): motor.c motor.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ motor.c

$(TARGET_DLL): motor.c motor.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ motor.c

$(BENCHMARK_BIN): benchmark.c motor.c motor.h
	$(CC) $(CFLAGS) -fopenmp -o $@ benchmark.c motor.c

clean:
	rm -f *.o *.so *.dll $(BENCHMARK_BIN) $(BENCHMARK_BIN).exe

.PHONY: all clean
