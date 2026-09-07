CC = gcc
CFLAGS = -Wall -Wextra -O3 -fPIC -fopenmp
LDFLAGS = -shared -fopenmp

TARGET = motor_alocacao.so
SRCS = motor.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c motor.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
