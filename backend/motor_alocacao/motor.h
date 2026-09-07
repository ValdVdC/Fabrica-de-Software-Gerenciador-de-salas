#ifndef MOTOR_ALOCACAO_H
#define MOTOR_ALOCACAO_H

#ifdef __cplusplus
extern "C" {
#endif

// Retorna a versão do motor de alocação
const char* obter_versao_motor(void);

// Função de teste/hello world para validar a integração ctypes
int testar_integracao_ctypes(int a, int b);

// Estrutura básica para dados de alocação (Sprint 5)
typedef struct {
    int turma_id;
    int sala_id;
    int dia_semana;
    int hora_inicio;
    int hora_fim;
} AlocacaoItem;

// Protótipo para o algoritmo paralelo de busca de alocação (Sprint 5)
int otimizar_alocacao(
    const int* restricoes,
    int num_turmas,
    int num_salas,
    AlocacaoItem* resultado,
    int max_threads,
    double* tempo_execucao_ms
);

#ifdef __cplusplus
}
#endif

#endif // MOTOR_ALOCACAO_H
