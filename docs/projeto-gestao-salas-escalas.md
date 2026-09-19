# Sistema de Gestão de Salas e Escalas com IA
### Documento de partida — Fábrica de Software + Tópicos Avançados

---

## 1. Visão geral do projeto

Sistema multi-campus de gestão acadêmica focado em **alocação inteligente de salas e horários**, com múltiplos níveis de acesso e dois componentes computacionais obrigatórios:

- **Motor de otimização/alocação** (C, paralelizado com OpenMP) — aloca turmas em salas respeitando capacidade, tipo de sala, equipamentos e conflitos de horário.
- **Modelo de previsão de falta** (Python/scikit-learn) — prevê probabilidade de baixa frequência em uma aula e sugere remanejamento de sala, submetido à aprovação humana.

## 2. Arquitetura definida

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| Frontend | Angular | Interfaces por perfil de acesso |
| Backend / API | FastAPI (Python) | Autenticação, multi-tenant, CRUD, regras de negócio, orquestração, docs automáticas (OpenAPI) |
| Motor de otimização | C + OpenMP, compilado como `.so`, chamado via `ctypes` | Busca paralela de alocação sala×horário×turma |
| IA preditiva | Python (scikit-learn) | Previsão de falta por turma/horário |
| Banco de dados | PostgreSQL | Persistência |
| Versionamento | Git + GitHub | Obrigatório, atualizado a cada orientação semanal |

**Escala do projeto:** 2 campi fictícios, 4 perfis de acesso (Admin/Coordenação, Professor, Aluno, Secretaria), 4 tipos de espaço (sala regular, laboratório, auditório, sala de reunião).

**Fluxo de remanejamento:** o modelo de IA gera uma **sugestão**; nunca troca a sala sozinho. Fica pendente até um Admin/Coordenação aprovar ou rejeitar.

### 2.1 Componentes do sistema

- **Angular (cliente)** — SPA consumida no navegador; nenhuma lógica de negócio ou cálculo pesado vive aqui, só apresentação por perfil de acesso.
- **FastAPI (servidor da aplicação)** — único ponto de entrada HTTP. Cuida de autenticação/JWT, isolamento por campus (multi-tenant), CRUD e regras de negócio simples. Também chama o motor de alocação e serve as sugestões geradas pelo job de IA.
- **Motor de alocação (C + OpenMP)** — compilado como biblioteca `motor_alocacao.so`, carregada e chamada em processo pelo FastAPI via `ctypes`. Recebe turmas/salas/restrições, devolve uma alocação válida; a busca é paralelizada entre threads.
- **Job de previsão de falta (Python/scikit-learn)** — não fica no caminho de nenhuma requisição HTTP. Roda periodicamente (via `APScheduler` embutido no processo do FastAPI, ou um cron simples chamando um script) lendo o histórico de `Frequencia`, gerando `PrevisaoFalta` e, quando o risco justificar, uma `SugestaoRemanejamento` pendente.
- **PostgreSQL** — única fonte de verdade; FastAPI e o job de previsão leem/escrevem nele. O motor em C não acessa o banco diretamente — recebe dados já carregados pelo FastAPI e devolve o resultado, mantendo o C livre de dependências externas (mais fácil de testar isoladamente).

### 2.2 Fluxos principais

- **Aluno consulta seus horários:** Angular → FastAPI (`GET /turmas/minhas`) → PostgreSQL → resposta.
- **Admin gera alocação automática:** Angular → FastAPI (`POST /alocacao/gerar`) → FastAPI monta os dados em memória → chama o `.so` via `ctypes` → motor C roda em paralelo e devolve a alocação → FastAPI grava em `Horario` + `LogAlocacao`.
- **Job de IA sugere remanejamento:** roda sozinho, fora do ciclo de requisição → lê `Frequencia` → calcula probabilidade de falta → grava `SugestaoRemanejamento` (status `pendente`).
- **Admin aprova/rejeita sugestão:** Angular → FastAPI (`PATCH /sugestoes/{id}`) → atualiza `SugestaoRemanejamento` e, se aprovado, atualiza `Horario` + registra em `LogAlocacao`.

### 2.3 Implantação (escopo de semestre)

Para não introduzir infraestrutura desnecessária (fila de mensagens, orquestração de containers), a recomendação é manter tudo simples:

- FastAPI e o `.so` do motor C **rodam no mesmo processo/servidor** — o `ctypes` exige que a biblioteca esteja no filesystem local, então não faz sentido separá-los em serviços distintos por enquanto.
- O job de previsão roda **dentro do mesmo processo** do FastAPI via `APScheduler`, evitando a complexidade de um Celery + Redis separado.
- PostgreSQL pode rodar em container à parte (Docker Compose com dois serviços: `app` e `db` já é suficiente).

---

## 3. Modelo de dados

| Entidade | Atributos principais | Relacionamentos |
|---|---|---|
| **Campus** | id, nome, cidade, endereço | 1—N Usuario, 1—N Sala, 1—N Curso |
| **Usuario** | id, nome, email, senha_hash, perfil (admin/coordenador/professor/aluno/secretaria), campus_id | N—1 Campus |
| **Sala** | id, campus_id, bloco, nome/número, tipo (regular/laboratório/auditório/reunião), capacidade, turnos_disponiveis | N—1 Campus; N—N Equipamento; 1—N Horario |
| **Equipamento** | id, nome (projetor, ar-condicionado, etc.) | N—N Sala (via Sala_Equipamento) |
| **Curso** | id, nome, campus_id | N—1 Campus; 1—N Disciplina |
| **Disciplina** | id, nome, curso_id, carga_horaria | N—1 Curso; 1—N Turma |
| **Turma** | id, disciplina_id, professor_id, periodo_letivo, num_matriculados, turno_preferido | N—1 Disciplina; N—1 Usuario(professor); N—N Usuario(aluno) via Matricula; 1—N Horario |
| **Matricula** | aluno_id, turma_id, data_matricula | N—1 Usuario(aluno); N—1 Turma |
| **Horario** | id, turma_id, sala_id, dia_semana, hora_inicio, hora_fim | N—1 Turma; N—1 Sala |
| **Frequencia** | id, matricula_id, horario_id, data, presente (bool) | N—1 Matricula; N—1 Horario — **alimenta o treino do modelo de IA** |
| **PrevisaoFalta** | id, turma_id, horario_id, data_prevista, prob_ausencia, versao_modelo, criado_em | N—1 Turma; N—1 Horario |
| **SugestaoRemanejamento** | id, horario_id, sala_atual_id, sala_sugerida_id, motivo, status (pendente/aprovado/rejeitado), aprovado_por, criado_em | N—1 Horario; N—1 Sala (atual/sugerida); N—1 Usuario (aprovador) |
| **LogAlocacao** | id, horario_id, tipo_evento, usuario_responsavel, timestamp | N—1 Horario; N—1 Usuario — trilha de auditoria |

---

## 4. Cronograma Oficial e Backlog por Sprint

O cronograma a seguir foi consolidado a partir das orientações e prazos oficiais da disciplina de Fábrica de Software (com integração a Tópicos Avançados):

| Sprint | Data-Limite | Marco Avaliativo | Escopo Principal no SIGAAS |
| :--- | :---: | :--- | :--- |
| **Sprint 01** | Concluída | Planejamento Inicial | Tema, requisitos funcionais, formação de equipe e repositório GitHub. |
| **Sprint 02** | 19/09 | Arquitetura e Modelagem | Arquitetura do sistema, Diagrama de Classes, MER conceitual, Modelo Relacional, protótipo navegável e schema do banco criado via Alembic. |
| **Sprint 03** | 19/09 | Estrutura Inicial Funcional | Conexão com PostgreSQL, login com autenticação, cadastro de usuários, controle de perfis (RBAC), CRUD principal e deploy local via Docker. |
| **Sprint 04** | 26/09 | Primeiro Módulo Completo | Módulo operacional de ponta a ponta: gestão de salas/espaços, cursos, turmas, matrículas com contagem atômica e grade horária semanal integrada aos painéis. |
| **Sprint 05** | 03/10 | Segundo Módulo Funcional | Implementação do algoritmo de alocação de salas/horários em C com paralelismo OpenMP, medições de Speedup e integração via `ctypes`. |
| **Sprint 06** | 17/10 | Aprimoramento e IA | Ajustes da Pré-Banca, modelo preditivo de absenteísmo com scikit-learn (`SugestaoRemanejamento`), integração de módulos e refinamento de interface. |
| **Sprint 07** | 24/10 | Sistema Quase Completo | Dashboard de indicadores em tempo real, relatórios gerenciais, filtros avançados, pesquisas e trilha de auditoria (`LogAlocacao`). |
| **Sprint 08** | 31/10 | Sistema Praticamente Concluído | Todas as funcionalidades concluídas, revisão geral do controle de permissões (RBAC) e regras de negócio multi-campus consolidadas. |
| **Sprint 09** | 07/11 | Testes Completos | Testes funcionais, testes de validação/navegação, cobertura de código >= 85%, correção de bugs e atualização da documentação técnica. |
| **Sprint 10** | 14/11 | Release Candidate | Sistema estabilizado, interface final, schema final do PostgreSQL, documentação interativa de APIs (OpenAPI/Swagger) e README técnico completo. |
| **Sprint 11** | 21/11 | Preparação para Entrega | Manual do Usuário, Manual Técnico da solução, revisão geral de código e saneamento de repositório. |
| **Sprint 12** | 28/11 | Versão Final e Vídeos | Congelamento de código (Code Freeze), ensaio geral da apresentação e produção dos dois vídeos (horizontal 16:9 para YouTube e vertical 9:16 para Instagram marcando @pryscillabgoncalves e @antenorparnaiba). |
| **Entrega Final** | 05/12 | Envio Definitivo no Teams | Submissão do PDF único com links funcionais (GitHub, YouTube e Instagram), sem possibilidade de prorrogação. |

---

### 4.1 Métricas Científicas de Benchmark: Sequencial vs. OpenMP

Para atender ao critério de rigor científico da disciplina de Tópicos Avançados (solicitado na devolutiva da Sprint 01), o motor de alocação em C será avaliado experimentalmente pelas seguintes métricas formais:

1. **Tempo de Execução ($T$)**:
   - $T_s$: Tempo de execução da versão sequencial pura (execução em thread única, sem overhead de sincronização).
   - $T_p(k)$: Tempo de execução da versão paralela utilizando $k$ threads OpenMP, com $k \in \{1, 2, 4, 8\}$.
   - Medição através de `omp_get_wtime()` com precisão de microsegundos, calculando a média e desvio padrão sobre 10 repetições independentes por cenário.

2. **Speedup Experimental ($S_k$)**:
   $$S_k = \frac{T_s}{T_p(k)}$$
   Indica o fator de aceleração computacional obtido pelo paralelismo em relação à linha de base sequencial.

3. **Eficiência Paralela ($E_k$)**:
   $$E_k = \frac{S_k}{k} \times 100\%$$
   Avalia a fração do poder computacional dos $k$ núcleos que foi efetivamente convertida em ganho de desempenho, quantificando o impacto de sincronizações, escalonamento e falsas dependências de cache.

4. **Fração Paralelizável e Limite Teórico (Lei de Amdahl)**:
   $$S_{\max} = \frac{1}{(1 - f) + \frac{f}{k}}$$
   Onde $f$ representa a fração do algoritmo de busca de alocação que é paralelizada entre as threads. A modelagem teórica permitirá comparar o speedup medido contra o teto assintótico da máquina.

5. **Cenários de Carga para Benchmarking**:
   - **Cenário Sintético 1 (Pequeno)**: 20 turmas $\times$ 10 salas (validação de corretude e casos de borda).
   - **Cenário Sintético 2 (Médio - Típico de Campus)**: 100 turmas $\times$ 40 salas, com restrições mistas de laboratórios e equipamentos.
   - **Cenário Sintético 3 (Stress / Escala)**: 500 turmas $\times$ 150 salas, com alta densidade de conflitos horários, projetado para evidenciar a escalabilidade do OpenMP.

---

## 5. Riscos a monitorar
- **Escopo:** com 2 campi + 4 tipos de sala + 4 perfis + motor em C + IA, o projeto é robusto — cuidado para não deixar a Sprint 5/6 apertada; comecem o módulo C cedo.
- **Dado de treino da IA:** decisão de usar dado real + público + sintético ainda está em aberto — definir isso até a Sprint 5 o mais tardar, para não travar o treino do modelo.
- **Integração FastAPI↔C:** validem o `ctypes` funcionando com um exemplo simples antes de implementar o algoritmo completo (é o maior risco técnico do projeto).
- **Job de IA sem infraestrutura extra:** se o `APScheduler` embutido se mostrar limitado mais pra frente, a saída é rodar o script de previsão via cron do sistema operacional — evitem migrar pra Celery/Redis a menos que seja estritamente necessário.
