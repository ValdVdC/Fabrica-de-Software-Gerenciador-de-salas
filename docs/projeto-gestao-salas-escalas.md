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

## 4. Backlog inicial por Sprint

### Sprint 1 — Formação da equipe, tema, requisitos *(já concluída com este documento)*
- ✅ Papéis definidos (SM, PO, Dev Back, Dev Front, Responsável BD/Documentação)
- ✅ Tema escolhido e validado contra os requisitos da disciplina
- ✅ Requisitos levantados (este documento)

### Sprint 2 — Casos de uso, banco, protótipo
- Como **PO**, quero documentar os casos de uso principais (matricular aluno, cadastrar sala, gerar horário, aprovar remanejamento) para orientar o desenvolvimento.
- Como **Responsável de BD**, quero criar o schema PostgreSQL a partir do modelo de dados acima, com as migrations iniciais.
- Como **Dev Frontend**, quero um protótipo navegável (wireframe) das telas por perfil (Admin, Professor, Aluno, Secretaria).
- Como **Scrum Master**, quero o board do projeto (GitHub Projects ou Trello) configurado com este backlog.

### Sprint 3 — Arquitetura, GitHub, ambiente
- Como **Dev Backend**, quero o projeto FastAPI inicial com routers separados (usuarios, campi, salas, turmas, horarios).
- Como **Dev Backend**, quero um "hello world" do módulo C compilado como `.so` e chamado via `ctypes` a partir do FastAPI, provando a integração antes de implementar a lógica real.
- Como **Dev Frontend**, quero o projeto Angular inicial com roteamento por perfil de acesso.
- Como **Scrum Master**, quero o repositório GitHub estruturado (branches, README, `.gitignore`) e atualizado semanalmente.

### Sprint 4 — Login, banco funcionando
- Como **usuário**, quero fazer login e ser redirecionado à interface do meu perfil (Admin/Professor/Aluno/Secretaria).
- Como **Admin**, quero cadastrar campi, salas e equipamentos.
- Como **Secretaria**, quero cadastrar cursos, disciplinas, turmas e matricular alunos.
- Como **Professor**, quero ver minhas turmas e horários atribuídos.

### Sprint 5 — Motor de otimização (C) e alocação
- Como **Dev Backend**, quero implementar o algoritmo de alocação em C: dado um conjunto de turmas e salas, encontrar uma alocação válida respeitando capacidade, tipo de sala, equipamentos e ausência de conflito de horário.
- Como **Dev Backend**, quero paralelizar a busca com OpenMP e medir o tempo de execução sequencial vs. paralelo (para o vídeo final).
- Como **Admin**, quero rodar a alocação automática e revisar o resultado antes de publicar os horários.

### Sprint 6 — IA de previsão de falta + remanejamento
- Como **Responsável de BD/Dev Backend**, quero gerar uma base de treino (dados reais coletados + dataset público + dados sintéticos complementares) para o modelo de previsão de falta.
- Como **Dev Backend**, quero treinar e servir um modelo scikit-learn que estima a probabilidade de baixa frequência por turma/horário.
- Como **sistema**, quero gerar uma `SugestaoRemanejamento` quando a previsão de ausência for alta o suficiente para justificar liberar uma sala maior.
- Como **Admin/Coordenação**, quero aprovar ou rejeitar cada sugestão de remanejamento, com o motivo registrado no log.

### Sprint Final — Testes, documentação, vídeos
- Como **equipe**, queremos testes cobrindo o motor de alocação, o modelo de IA e os fluxos de aprovação.
- Como **equipe**, queremos a documentação técnica finalizada (arquitetura, instruções de execução, decisões de design).
- Como **equipe**, queremos gravar o vídeo horizontal (problema → solução → arquitetura → tecnologias → demonstração → IA/paralelismo → resultados/speedup → considerações finais) e o vídeo vertical para Instagram, marcando @pryscillabgoncalves e @antenorparnaiba.

---

## 5. Riscos a monitorar
- **Escopo:** com 2 campi + 4 tipos de sala + 4 perfis + motor em C + IA, o projeto é robusto — cuidado para não deixar a Sprint 5/6 apertada; comecem o módulo C cedo.
- **Dado de treino da IA:** decisão de usar dado real + público + sintético ainda está em aberto — definir isso até a Sprint 5 o mais tardar, para não travar o treino do modelo.
- **Integração FastAPI↔C:** validem o `ctypes` funcionando com um exemplo simples antes de implementar o algoritmo completo (é o maior risco técnico do projeto).
- **Job de IA sem infraestrutura extra:** se o `APScheduler` embutido se mostrar limitado mais pra frente, a saída é rodar o script de previsão via cron do sistema operacional — evitem migrar pra Celery/Redis a menos que seja estritamente necessário.
