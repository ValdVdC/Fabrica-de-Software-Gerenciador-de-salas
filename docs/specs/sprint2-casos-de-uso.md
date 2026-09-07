# [SPEC-002] Casos de Uso Principais do Sistema SIGAAS

- **Sprint:** Sprint 2
- **Autor / Agente:** Planner-SDD (Antigravity)
- **Status:** Em Revisao
- **Data de Criacao:** 2026-09-07
- **ID ClickUp (Epico/Task):** 86e35a8kv

---

## 1. Contexto e Objetivos

O sistema SIGAAS gerencia alocacao de espacos fisicos e horarios academicos em ambiente multi-campus. Este documento especifica os quatro casos de uso nucleares que orientam as interfaces, regras de negocio e testes do sistema, complementados pela regra transversal de isolamento de campus e controle de acesso por perfil (Admin, Coordenador, Professor, Aluno, Secretaria).

---

## 2. Regra Transversal: Autenticacao, Autorizacao e Isolamento Multi-Campus

Toda operacao no SIGAAS e contextualizada pelo campus de lotacao do usuario autenticado (extraido do token JWT).
- **Perfis de Acesso**:
  - `admin`: Acesso irrestrito a configuracoes de campus, salas, equipamentos e auditoria.
  - `coordenador`: Gestao de horarios, avaliacao de sugestoes de remanejamento e visualizacao de turmas do campus.
  - `secretaria`: Gestao de cursos, disciplinas, turmas e matriculas de alunos.
  - `professor`: Consulta de turmas atribuidas, grade de horarios e lancamento de frequencia.
  - `aluno`: Consulta de turmas matriculadas e grade individual de horarios.
- **Isolamento de Campus**:
  - Requisicoes sao estritamente filtradas por `campus_id`. Usuarios de um campus nao podem ler ou alterar recursos de outro campus (HTTP 403 Forbidden).

---

## 3. Historias de Usuario e Criterios de Aceite (Gherkin)

### UC01: Cadastrar e Configurar Sala e Equipamentos
> **Como** Administrador do Campus  
> **Quero** cadastrar salas com bloco, numero, tipo, capacidade e vincular equipamentos  
> **Para que** o motor de alocacao e a coordenacao conhecam os recursos fisicos disponiveis.

#### Criterios de Aceite:
```gherkin
Cenario: Cadastro de sala com sucesso
  Dado que o usuario esta autenticado com perfil "admin" no campus 1
  Quando enviar uma requisicao POST para "/api/v1/salas" com bloco "A", numero "101", tipo "regular", capacidade 40 e turnos ["matutino", "noturno"]
  Entao o sistema deve persistir a sala com status ativo
  E retornar codigo HTTP 201 Created com os dados da sala criada

Cenario: Falha ao cadastrar sala duplicada no mesmo campus
  Dado que ja existe uma sala com bloco "A" e numero "101" no campus 1
  Quando o administrador tentar cadastrar outra sala com mesmo bloco e numero no campus 1
  Entao o sistema deve recusar o cadastro
  E retornar codigo HTTP 409 Conflict com mensagem "Sala ja cadastrada neste bloco e campus"

Cenario: Falha ao cadastrar sala com capacidade invalida
  Dado que o administrador submete capacidade igual a 0 ou negativa
  Quando enviar a requisicao de cadastro
  Entao o sistema deve retornar codigo HTTP 422 Unprocessable Entity
```

---

### UC02: Matricular Aluno em Turma
> **Como** Operador da Secretaria Academica  
> **Quero** matricular um aluno em uma turma ofertada no periodo letivo vigente  
> **Para que** o aluno componha a lista de matriculados utilizada no calculo de ocupacao da sala.

#### Regras de Negocio e Capacidade:
- **Determinacao da Capacidade**: A capacidade maxima da turma e definida pela capacidade fisica da sala vinculada a ela em `horario`. Caso a turma ainda nao possua sala alocada, adota-se o limite pedagogico configurado na criacao da turma.
- **Atomicidade e Concorrencia**: A verificacao de vagas disponiveis (`num_matriculados < capacidade`) e o incremento de `num_matriculados` devem ocorrer atomicamente dentro da mesma transacao no PostgreSQL (via bloqueio pessimista `SELECT ... FOR UPDATE` na linha da turma ou atualizacao condicional `UPDATE turma SET num_matriculados = num_matriculados + 1 WHERE id = :id AND num_matriculados < :capacidade`).

#### Criterios de Aceite:
```gherkin
Cenario: Matricula realizada com sucesso dentro da capacidade
  Dado que o operador da secretaria esta autenticado no campus 1
  E existe uma turma ofertada no campus 1 com capacidade para 40 alunos e 39 matriculados
  Quando enviar POST para "/api/v1/matriculas" com aluno_id (do campus 1) e turma_id
  Entao o sistema deve registrar a matricula com data atual
  E incrementar atomicamente o contador num_matriculados para 40
  E retornar codigo HTTP 201 Created

Cenario: Bloqueio de matricula por capacidade excedida
  Dado que o operador da secretaria esta autenticado no campus 1
  E a turma ofertada no campus 1 ja atingiu a capacidade maxima de matriculados
  Quando submeter solicitacao de matricula de novo aluno
  Entao o sistema deve rejeitar o registro em transacao atomica
  E retornar codigo HTTP 409 Conflict com mensagem "Capacidade maxima da turma atingida"

Cenario: Bloqueio de matricula duplicada
  Dado que o aluno ja esta matriculado na turma solicitada
  Quando a secretaria submeter a mesma solicitacao de matricula
  Entao o sistema deve rejeitar o registro
  E retornar codigo HTTP 409 Conflict com mensagem "Aluno ja matriculado nesta turma"

Cenario: Bloqueio de matricula em turma fora do campus autorizado
  Dado que o operador da secretaria esta autenticado no campus 1
  E a turma solicitada pertence ao campus 2
  Quando a secretaria tentar submeter a matricula
  Entao o sistema deve recusar a operacao
  E retornar codigo HTTP 403 Forbidden com mensagem "Acesso negado: turma fora do escopo do campus autorizado"
```

---

### UC03: Gerar Alocacao de Salas e Horarios
> **Como** Coordenador ou Administrador  
> **Quero** solicitar a geracao automatizada da grade de alocacao de salas e horarios para o periodo letivo  
> **Para que** o motor de alocacao em C processe as restricoes em paralelo e defina a distribuicao otimizada.

#### Criterios de Aceite:
```gherkin
Cenario: Disparo de alocacao com turmas e salas validas
  Dado que o usuario possui perfil "coordenador" ou "admin"
  E existem turmas sem alocacao e salas disponiveis cadastradas no campus
  Quando enviar POST para "/api/v1/alocacao/gerar" com o periodo_letivo vigente
  Entao o FastAPI monta a estrutura em memoria e invoca a biblioteca C via ctypes
  E persiste os horarios calculados na tabela "horario"
  E registra o evento na tabela "log_alocacao" com o id do usuario solicitante
  E retorna codigo HTTP 200 OK com o resumo de turmas alocadas e metricas de execucao

Cenario: Tentativa de geracao sem permissoes adequadas
  Dado que o usuario esta autenticado como "aluno" ou "professor"
  Quando tentar disparar o endpoint POST "/api/v1/alocacao/gerar"
  Entao o sistema deve bloquear o acesso
  E retornar codigo HTTP 403 Forbidden
```

---

### UC04: Avaliar e Aprovar/Rejeitar Sugestao de Remanejamento
> **Como** Coordenador ou Administrador  
> **Quero** avaliar uma sugestao de troca de sala gerada pelo job de previsao de baixa frequencia  
> **Para que** espacos superdimensionados sejam liberados sem intervençao automatica no quadro oficial.

#### Criterios de Aceite:
```gherkin
Cenario: Aprovacao de sugestao de remanejamento
  Dado que existe uma sugestao de remanejamento com status "pendente" para determinado horario
  E a nova sala sugerida esta desocupada no horario correspondente
  Quando o coordenador enviar PATCH para "/api/v1/sugestoes/{id}" com status "aprovado"
  Entao o sistema deve atualizar o horario transferindo-o para a sala_sugerida_id
  E atualizar o status da sugestao para "aprovado" com o id do aprovador
  E gerar um registro em "log_alocacao" do tipo "remanejamento"
  E retornar codigo HTTP 200 OK

Cenario: Rejeicao de sugestao de remanejamento
  Dado que existe uma sugestao com status "pendente"
  Quando o coordenador enviar PATCH para "/api/v1/sugestoes/{id}" com status "rejeitado" e motivo "Turma necessita de bancadas laboratoriais especificas"
  Entao o sistema deve manter a alocacao original do horario inalterada
  E atualizar o status da sugestao para "rejeitado" com justificativa
  E retornar codigo HTTP 200 OK
```

---

## 4. Contratos de API e Estruturas de Payload (Pydantic v2)

> **Regra de Seguranca de Multi-Tenancy**: Os endpoints nunca recebem `campus_id` no corpo da requisicao. O identificador do campus e obrigatoriamente extraido e validado pelo backend a partir das claims do token JWT (`sub` e `campus_id`). Qualquer tentativa de manipular recursos de outro campus e sumariamente rejeitada com HTTP 403 Forbidden.

### 4.1 UC01: Cadastro de Sala
- `POST /api/v1/salas`
```json
{
  "bloco": "Bloco B",
  "numero": "204",
  "tipo": "laboratorio",
  "capacidade": 35,
  "turnos_disponiveis": ["matutino", "vespertino"],
  "equipamento_ids": [1, 3]
}
```
*Nota*: `turnos_disponiveis` e informado como array de strings `list[str]` na API e validado pelo Pydantic contra os enums permitidos (`matutino`, `vespertino`, `noturno`, `integral`), sendo serializado como `JSONB` no PostgreSQL.

### 4.2 UC02: Matricula de Aluno
- `POST /api/v1/matriculas`
```json
{
  "aluno_id": 42,
  "turma_id": 10
}
```

### 4.3 UC03: Geracao de Alocacao
- `POST /api/v1/alocacao/gerar`
```json
{
  "periodo_letivo": "2026.1"
}
```
*Nota*: O campus de destino e obtido exclusivamente do token JWT do coordenador autenticado.

### 4.4 UC04: Avaliacao de Remanejamento
- `PATCH /api/v1/sugestoes/{id}`
```json
{
  "status": "aprovado",
  "justificativa": "Remanejamento deferido para otimizacao energetica"
}
```
*Nota*: O campo `motivo` contem a explicacao original gerada pelo job preditivo de IA e permanece imutavel. O campo `justificativa` e opcional, armazenando a observacao humana inserida no momento da aprovacao ou rejeicao.

---

## 5. Plano de Testes TDD (Fase RED)

### 5.1 Testes de Casos de Uso e Regras de Negocio
- [ ] `tests/test_usecases_sala.py::test_cadastrar_sala_valida`: Valida persistencia de sala regular e vinculo de equipamentos com campus derivado do JWT.
- [ ] `tests/test_usecases_sala.py::test_impedir_sala_duplicada`: Valida restricao de unicidade campus + bloco + numero.
- [ ] `tests/test_usecases_matricula.py::test_matricular_aluno_sucesso`: Valida criacao da matricula e contagem da turma.
- [ ] `tests/test_usecases_matricula.py::test_impedir_matricula_duplicada`: Valida integridade e codigo 409.
- [ ] `tests/test_usecases_matricula.py::test_matricula_concorrente_respeita_capacidade_maxima`: Valida que chamadas concorrentes simultaneas respeitam atomicamente o teto de capacidade da turma sem overflow.
- [ ] `tests/test_usecases_alocacao.py::test_alocacao_gera_horarios_e_auditoria`: Valida criacao de horario e entrada em log_alocacao.
- [ ] `tests/test_usecases_remanejamento.py::test_aprovar_remanejamento_atualiza_horario`: Valida transicao atomica de horario e registro de justificativa.
- [ ] `tests/test_usecases_remanejamento.py::test_rejeitar_remanejamento_mantem_horario`: Valida integridade do horario original e persistencia do status rejeitado.

---

## 6. Decomposicao de Tarefas para o ClickUp

- [ ] [SDD] Especificar formalmente os 4 Casos de Uso e regras transversais de acesso
- [ ] [TDD] Criar suíte de testes de integridade para os fluxos dos Casos de Uso
- [ ] [Backend] Implementar schemas Pydantic de entrada e saida dos casos de uso
- [ ] [Backend] Implementar servico de auditoria e registro de log_alocacao
- [ ] [Frontend] Modelar interfaces dos casos de uso para os perfis Admin, Coordenador e Secretaria
