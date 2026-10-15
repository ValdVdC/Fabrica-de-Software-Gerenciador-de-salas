# [SPEC-006] Inteligencia Artificial Preditiva de Absenteismo e Remanejamento Human-in-the-Loop

- **Sprint:** Sprint 06 - Terceiro Modulo Funcional
- **Autor / Agente:** Planner-SDD & Squad SIGAAS
- **Status:** Em Revisao (Aguardando Gate 1)
- **Data de Criacao:** 2026-10-14
- **ID ClickUp (Epico/Task):** #CU-SPRINT06-IA-PREDITIVA-REMANEJAMENTO

---

## 1. Contexto e Objetivos

O SIGAAS (Sistema Inteligente de Gestao Academica e Alocacao de Salas) alcancou na Sprint 05 a conclusao bem-sucedida do Segundo Modulo Funcional, implementando o Motor Combinatorial de Alocacao em C com OpenMP via ctypes e o Painel Angular de visualizacao cientifica.

A **Sprint 06** estabelece a entrega do **Terceiro Modulo Funcional**, focado no modulo de **Inteligencia Artificial Preditiva de Absenteismo Discente e Remanejamento Inteligente de Salas**.

O objetivo primordial e identificar turmas com alto risco de ociosidade fisica em salas superdimensionadas decorrente de absenteismo/evasao, sugerindo realocacoes proativas para salas menores livres, otimizando o consumo energetico, custos de manutencao e ocupacao fisica no campus.

### 1.1 Regra de Ouro Inviolavel da IA
O modelo de Machine Learning e o pipeline em lote **NUNCA alteram diretamente os dados de alocacao (`horario.sala_id`)**. Toda predicao e oportunidade de otimizacao e registrada na tabela `sugestao_remanejamento` com status `pendente`. A alteracao real do espaco fisico ocorre exclusivamente mediante analise e aprovacao formal de um Coordenador ou Administrador humano atraves do endpoint `PATCH /api/v1/sugestoes/{id}`.

### 1.2 Matriz de Correcoes e Devolutivas da Pre-Banca
Em atendimento as recomendacoes da banca examinadora e auditorias de qualidade:
1. **Padronizacao Formal ISO 8601 para Dias da Semana**:
   - Mapeamento estrito e documentado de dias da semana no intervalo `0` a `6` (`0 = Segunda-feira`, `1 = Terca-feira`, `2 = Quarta-feira`, `3 = Quinta-feira`, `4 = Sexta-feira`, `5 = Sabado`, `6 = Domingo`).
   - Bloqueio de qualquer indice fora da faixa via restricoes de schema Pydantic v2 e check constraints no banco de dados.
2. **Tratamento Resiliente e Amigavel de Erros HTTP**:
   - Tratamento universal de excecoes no backend com codigos de status semanticos (400, 401, 403, 404, 409, 422).
   - Mensagens claras de diagnostico estruturadas em JSON (`{"detail": "..."}`), impedindo quebras de integridade ou travamentos em interfaces consumidoras.
3. **Feedback Visual e Rastreabilidade Operacional**:
   - Registro detalhado de logs em `log_alocacao` contendo identificador do usuario responsavel, horario afetado e snapshot dos identificadores de salas antes e apos remanejamento.

---

## 2. Historias de Usuario e Criterios de Aceite (Gherkin)

### Historia 1: Analise Preditiva e Geracao de Sugestoes de Remanejamento
> **Como** Coordenador de Campus ou Administrador Geral  
> **Quero** acionar a rotina analitica de IA para inferir absenteismo em turmas semestrais  
> **Para que** o sistema identifique salas ociosas e gere sugestoes de remanejamento sem impactar a grade consolidada.

#### Criterios de Aceite:
```gherkin
Cenario: Disparo de analise preditiva por Administrador ou Coordenador
  Dado que existem turmas com horarios alocados no campus
  E o usuario autenticado possui perfil de Administrador ou Coordenador
  Quando submeter uma requisicao POST para /api/v1/ia/analisar
  Entao a resposta HTTP deve retornar status 200 OK
  E o corpo da resposta deve conter o total de turmas analisadas, total de sugestoes geradas e tempo de processamento
  E nenhuma sala alocada na tabela horario deve ser alterada durante este processo
  E as sugestoes geradas devem ser gravadas na tabela sugestao_remanejamento com status pendente

Cenario: Bloqueio de analise preditiva por perfil sem privilegio
  Dado que um usuario autenticado possui perfil de Docente ou Discente
  Quando submeter uma requisicao POST para /api/v1/ia/analisar
  Entao a API deve retornar HTTP 403 Forbidden com mensagem de privilegio insuficiente

Cenario: Idempotencia na deteccao de remanejamento
  Dado que ja existe uma sugestao com status pendente para um determinado horario
  Quando a rotina de inferencia da IA for executada novamente
  Entao o sistema nao deve criar sugestoes pendentes duplicadas para o mesmo horario
```

### Historia 2: Consulta e Filtragem de Sugestoes com Isolamento Multi-Campus
> **Como** Coordenador de Campus  
> **Quero** listar as sugestoes de remanejamento geradas para o meu campus  
> **Para que** eu possa avaliar as recomendacoes sem visualizar informacoes de outros campi.

#### Criterios de Aceite:
```gherkin
Cenario: Listagem com filtro por status e isolamento de campus
  Dado que existem sugestoes cadastradas para o Campus 1 e Campus 2
  E o usuario autenticado e Coordenador vinculado ao Campus 1
  Quando consultar o endpoint GET /api/v1/sugestoes?status=pendente
  Entao a resposta HTTP deve retornar status 200 OK
  E todos os registros retornados devem pertencer estritamente ao Campus 1
  E nenhum registro do Campus 2 deve ser exposto ao Coordenador

Cenario: Administrador visualiza sugestoes globais ou com filtro
  Dado que o usuario autenticado possui perfil de Administrador
  Quando consultar o endpoint GET /api/v1/sugestoes
  Entao a resposta deve retornar as sugestoes de todos os campi
```

### Historia 3: Aprovacao ou Rejeicao Humana (Human-in-the-Loop)
> **Como** Coordenador de Campus ou Administrador  
> **Quero** aprovar ou rejeitar uma sugestao de remanejamento  
> **Para que** a alteracao fisica da sala seja aplicada com seguranca ou descartada justificadamente.

#### Criterios de Aceite:
```gherkin
Cenario: Aprovacao bem-sucedida de remanejamento
  Dado uma sugestao com status pendente para um horario do campus do usuario
  E a sala sugerida encontra-se desocupada no dia e horario correspondentes
  Quando o Coordenador submeter PATCH /api/v1/sugestoes/{id} com status=aprovado
  Entao a resposta HTTP deve retornar status 200 OK
  E a sugestao deve ter seu status atualizado para aprovado e aprovado_por preenchido
  E a sala_id na tabela horario deve ser atualizada atomicamente para a sala sugerida
  E um registro de auditoria na tabela log_alocacao deve ser criado com tipo alteracao

Cenario: Rejeicao motivada de sugestao
  Dado uma sugestao com status pendente
  Quando o Coordenador submeter PATCH /api/v1/sugestoes/{id} com status=rejeitado e justificativa informada
  Entao a resposta HTTP deve retornar status 200 OK
  E o status da sugestao deve mudar para rejeitado
  E a sala_id na tabela horario deve permanecer inalterada
  E nenhuma alteracao na grade deve ser aplicada

Cenario: Conflito por ocupacao superveniente da sala sugerida
  Dado que entre a geracao da sugestao e o momento da aprovacao a sala sugerida foi ocupada por outra turma
  Quando o Coordenador tentar aprovar a sugestao via PATCH /api/v1/sugestoes/{id}
  Entao a API deve retornar HTTP 409 Conflict com mensagem explicativa
  E a transacao deve sofrer rollback sem alterar o horario

Cenario: Mitigacao de BOLA/IDOR na aprovacao
  Dado uma sugestao vinculada a um horario do Campus 2
  E o usuario autenticado e Coordenador do Campus 1
  Quando submeter PATCH /api/v1/sugestoes/{id}
  Entao a API deve retornar HTTP 404 Not Found impedindo adulteracao entre campi
```

---

## 3. Arquitetura de Machine Learning (scikit-learn)

### 3.1 Prevenção de Temporal Data Leakage
Dados de frequencia e presenca academica possuem dependencia temporal estrita:
- **Particao Temporal**: O particionamento para validacao e treinamento emprega `TimeSeriesSplit` ordenado cronologicamente pela data de registro (`frequencia.data`).
- **Vedacao de Divisao Aleatoria**: E proibido o uso de `train_test_split` com shuffle aleatorio, evitando que dados de presencas futuras vazem para o conjunto de treinamento passado.

### 3.2 Pipeline scikit-learn e Calibracao
O pipeline e composto por:
1. **Pre-processamento via `ColumnTransformer`**:
   - Atributos numericos: `dia_semana`, `hora_inicio_minutos`, `num_matriculados`, `capacidade_sala`, `razao_ocupacao_nominal` submetidos a normalizacao (`StandardScaler`).
   - Atributos categoricos: `turno` submetido a codificacao one-hot (`OneHotEncoder(handle_unknown='ignore')`).
2. **Classificador Supervisionado**:
   - `HistGradientBoostingClassifier` com suporte a interacoes nao-lineares e resistencia a desbalanceamento.
3. **Calibracao de Probabilidades**:
   - Envolvimento via `CalibratedClassifierCV(method='sigmoid', cv='prefit')` assegurando que a probabilidade prevista $P(\text{falta})$ corresponda confiavelmente a frequencia observada.
4. **Serializacao**:
   - O pipeline treinado e persistido em `backend/app/ml/modelo_absenteismo.joblib`.

### 3.3 Heuristica de Selecao de Sala para Remanejamento
1. A partir de $P(\text{falta})$, calcula-se o publico efetivo esperado:
   $$\text{presentes\_esperados} = \lceil \text{num\_matriculados} \times (1.0 - P(\text{falta})) \rceil$$
2. Calcula-se a ociosidade da sala atual:
   $$\text{taxa\_ociosidade} = \frac{\text{capacidade\_atual} - \text{presentes\_esperados}}{\text{capacidade\_atual}}$$
3. Caso $\text{taxa\_ociosidade} \ge \text{limiar\_ociosidade}$ (padrao: 0.40 ou 40%) e haja sobredimensionamento significativo ($\text{capacidade\_atual} - \text{presentes\_esperados} \ge 10$):
   - Localizam-se todas as salas ativas do mesmo campus compativeis com o tipo de disciplina (Regular para aulas teoricas, Laboratorio para disciplinas praticas).
   - Filtram-se apenas as salas desocupadas no mesmo `dia_semana` e faixa `[hora_inicio, hora_fim]`.
   - Dentre as salas desocupadas, seleciona-se a menor sala que comporte a turma com margem de seguranca ($\text{capacidade} \ge \text{presentes\_esperados}$ e $\text{capacidade} < \text{capacidade\_atual}$).
   - Registra-se a proposta em `sugestao_remanejamento` com status `pendente`.

---

## 4. Contratos OpenAPI REST

### 4.1 `GET /api/v1/sugestoes`
- **Descricao**: Lista sugestoes de remanejamento com paginacao e filtros, ordenadas por probabilidade de absenteismo decrescente.
- **Parametros**:
  - `status` (query, opcional): `pendente`, `aprovado`, `rejeitado`
  - `campus_id` (query, opcional, restrito a ADMIN): ID do campus
  - `skip` (query, opcional, padrao 0): Deslocamento de paginacao
  - `limit` (query, opcional, padrao 50, max 100): Quantidade maxima de itens
- **Respostas**:
  - `200 OK`: `List[SugestaoRemanejamentoRead]`
  - `401 Unauthorized`: Token ausente ou invalido
  - `403 Forbidden`: Privilegio insuficiente

### 4.2 `POST /api/v1/ia/analisar`
- **Descricao**: Executa inferencia preditiva e gera sugestoes pendentes.
- **Permissoes**: `ADMIN`, `COORDENADOR`
- **Corpo da Requisicao**: `AnaliseIARequest`
  - `campus_id` (opcional): ID do campus (se Coordenador, forçado para o campus do usuario)
  - `periodo_letivo` (opcional): Semestre letivo a analisar (ex: `2026.1`)
  - `limiar_ociosidade` (opcional, padrao 0.40): Taxa minima de ociosidade
- **Respostas**:
  - `200 OK`: `AnaliseIAResponse`
  - `401 Unauthorized`: Token ausente ou expirado
  - `403 Forbidden`: Privilegio insuficiente

### 4.3 `PATCH /api/v1/sugestoes/{id}`
- **Descricao**: Aprovacao ou rejeicao humana de sugestao de remanejamento.
- **Permissoes**: `ADMIN`, `COORDENADOR`
- **Corpo da Requisicao**: `SugestaoAprovacaoUpdate`
  - `status` (obrigatorio): `aprovado` ou `rejeitado`
  - `justificativa` (opcional): Motivo da decisao
- **Respostas**:
  - `200 OK`: `SugestaoRemanejamentoRead`
  - `400 Bad Request`: Sugestao ja processada ou status invalido
  - `404 Not Found`: Sugestao inexistente ou campus alheio (BOLA)
  - `409 Conflict`: Sala sugerida em conflito de ocupacao
  - `401 Unauthorized`: Nao autenticado
  - `403 Forbidden`: Nao autorizado

---

## 5. Plano de Testes TDD

1. `test_ia_service.py`:
   - Treinamento do pipeline com TimeSeriesSplit.
   - Serializacao e carregamento de `modelo_absenteismo.joblib`.
   - Inferencia de absenteismo para horarios em dias uteis.
   - Geracao idempotente de registros em `sugestao_remanejamento`.
   - Regra de ouro: garantia de que `horario.sala_id` permanece inalterado durante a analise.
2. `test_api_sugestoes.py`:
   - `GET /sugestoes`: Listagem, filtros e isolamento multi-campus (BOLA).
   - `POST /ia/analisar`: Execucao por Admin e Coordenador, bloqueio de Professor e Aluno.
   - `PATCH /sugestoes/{id}`:
     - Aprovacao: atualizacao da sala no horario e criacao de log em `log_alocacao`.
     - Rejeicao: manutencao da sala original e registro da justificativa.
     - Bloqueio de reprocessamento (idempotencia).
     - Bloqueio de conflito de horario (409 Conflict).
     - Isolamento entre campi (404 Not Found para coordenador de outro campus).
