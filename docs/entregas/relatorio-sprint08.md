# Relatório Técnico: Sprint 08

## Sistema Inteligente de Gestão Acadêmica e Alocação de Salas (SIGAAS)

**Disciplina:** Fábrica de Software & Tópicos Avançados em Computação  
**Turma:** 8MB - CC  
**Equipe:** Grupo 31 — SIGAAS  
**Entrega:** Sprint 08 - Sistema Praticamente Concluído (Revisão de Permissões RBAC, Isolamento Multi-Campus e Consolidação de Regras)  
**Data-Limite de Entrega:** 31 de Outubro de 2026 às 23:59  
**Repositório Oficial no GitHub:** [https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas)

---

### 1. Identificação da Equipe e Distribuição de Papéis

| Integrante | Matrícula | Papel no Squad | Responsabilidade Técnica Principal |
| :--- | :---: | :--- | :--- |
| **Ewerton Thyago Tavares da Silva** | 01573977 | Scrum Master (Líder) | Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams |
| **Wesclei Batista Da Cruz Júnior** | 01606772 | Product Owner | Levantamento de requisitos, regras de negócio e validação dos critérios de aceite |
| **Osvaldo Vasconcelos de Carvalho** | 01614171 | Dev Backend / Sistemas | Arquitetura de API, integração FFI C/OpenMP (`ctypes`), endpoints e migrations |
| **Gabriel Porfírio dos Santos** | 01591399 | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| **Flávio Vecch de Brito Farias** | 01600988 | DBA & Documentação | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica |

---

# PARTE 8 - SPRINT 08: SISTEMA PRATICAMENTE CONCLUÍDO

## 8.1 Contexto e Objetivos

A conclusão funcional da Sprint 08 está condicionada ao merge dos PRs #96 e #97. Uma vez integrados, o ciclo de implementação funcional do SIGAAS estará encerrado. As Sprints 01 a 07 entregaram a base multi-campus, o motor de alocação em C/OpenMP, a IA preditiva de faltas, a auditoria, o dashboard e os relatórios. A Sprint 08 concentrou o esforço naquilo que sustenta a operação real do sistema em ambiente institucional: a **governança de permissões**, o **isolamento estrito entre campi** e a **consolidação do ciclo de vida das entidades acadêmicas**.

O objetivo central foi eliminar vetores de escalada de privilégio e de vazamento de dados entre tenants, alinhando a API aos riscos do OWASP API Security Top 10, com destaque para:

- **BFLA (Broken Function Level Authorization):** impedir que perfis inferiores concedam ou alterem perfis superiores.
- **BOLA/IDOR (Broken Object Level Authorization):** impedir acesso a recursos de outro campus por manipulação de identificadores.
- **TOCTOU (Time-of-Check to Time-of-Use):** impedir cancelamentos concorrentes de matrícula que gerem decremento duplo de vagas.

A especificação normativa da sprint está em `docs/specs/sprint8-rbac-multicampus.md` (`SPEC-008`), aprovada no Gate 1 em 24 de Outubro de 2026. O backend foi entregue nos PRs #94 e #95, ambos mesclados na `main`. O frontend correspondente está nos PRs #96 e #97, ainda **abertos e em revisão (Gate 2)**. Por esse motivo, o status desta entrega é **Praticamente Concluído**, condicionado à revisão e ao merge dos PRs #96 e #97.

### 8.1.1 Diagnóstico e Ações Corretivas

| Item diagnosticado | Ação executada | Situação |
| :--- | :--- | :--- |
| Criação de usuários permitia escalada de perfil | Validação hierárquica contra BFLA em `POST /usuarios` | Implementado no PR #94 (mesclado) |
| Ausência de ciclo de vida de usuários | `PATCH /usuarios/{id}` com RBAC, autoedição e auditoria | Implementado no PR #95 (mesclado) |
| Ausência de ciclo de vida de salas e turmas | `PATCH /salas/{id}` e `PATCH /turmas/{id}` com isolamento de campus | Implementado no PR #95 (mesclado) |
| Matrícula sem cancelamento e sem tratamento de concorrência | `DELETE /matriculas/{id}` com update atômico e rematrícula | Implementado no PR #95 (mesclado) |
| Consultas unitárias de cursos e disciplinas sem isolamento | `GET /cursos/{id}` e `GET /disciplinas/{id}` com `require_campus_access` | Implementado no PR #95 (mesclado) |
| Tratamento de HTTP 403 ausente no frontend | Interceptor e guards de perfil | Em revisão no PR #96 (aberto) |
| Navegação por perfil incompleta na UI | Menu e rotas condicionados ao perfil autenticado | Em revisão no PR #97 (aberto) |

---

## 8.2 Backend e Segurança

### 8.2.1 Dependência Centralizada `require_campus_access`

A função `require_campus_access(resource_campus_id, current_user)` foi adicionada em `backend/app/api/deps.py` e passou a ser o ponto único de validação de tenant da API.

- O perfil `ADMIN` possui autorização global e retorna imediatamente.
- Os demais perfis (`COORDENADOR`, `SECRETARIA`, `PROFESSOR`, `ALUNO`) exigem correspondência exata entre o campus do recurso e `current_user.campus_id`.
- Divergência de campus, campus nulo, tipo inválido, `bool` e identificador não positivo resultam em `HTTP 404 Not Found` com `detail="Recurso nao encontrado"`.
- O uso de 404 em vez de 403 é intencional e está documentado na docstring da função: evita que um atacante confirme a existência de entidades em outros campi.

### 8.2.2 Proteção contra BFLA em `POST /usuarios`

O endpoint de criação de usuários recebeu validação hierárquica antes de qualquer consulta ao banco:

- `SECRETARIA` não pode conceder `ADMIN`, `COORDENADOR` ou `SECRETARIA`; pode criar `PROFESSOR` e `ALUNO` no próprio campus.
- `COORDENADOR` não pode conceder `ADMIN` ou `COORDENADOR`; pode criar `SECRETARIA`, `PROFESSOR` e `ALUNO` no próprio campus.
- Tentativas de escalada retornam `HTTP 403 Forbidden` com `detail="Privilegio insuficiente para conceder este perfil"`.
- A validação de escopo de campus do solicitante ocorre antes de `db.get(Campus, payload.campus_id)`.
- O e-mail é normalizado com `str(payload.email).strip().lower()` antes da verificação de unicidade e da persistência.

### 8.2.3 Ciclo de Vida de Usuários (`PATCH /usuarios/{id}`)

O endpoint permite alteração de `nome`, `email`, `perfil` e `ativo`, com as seguintes regras:

- `require_campus_access` valida o campus do usuário alvo.
- `SECRETARIA` só altera `PROFESSOR` e `ALUNO` do próprio campus.
- `COORDENADOR` só altera `SECRETARIA`, `PROFESSOR` e `ALUNO` do próprio campus.
- É proibido conceder perfil superior ou igual ao do solicitante.
- Autoedição cadastral (nome e e-mail) é permitida ao próprio usuário; o bloqueio de auto-elevação de perfil e de autoinativação é explícito no código, e o teste `test_auto_edicao_coordenador_e_secretaria_sucesso` cobre Coordenador e Secretaria.
- Toda alteração gera evento em `LogAlocacao` com `TipoEventoLog.ALTERACAO`.
- Conflito de e-mail retorna `HTTP 409 Conflict`.

### 8.2.4 Ciclo de Vida de Salas e Turmas

- `PATCH /salas/{id}` foi adicionado e `PUT /salas/{id}` foi mantido no mesmo handler, restrito a `ADMIN` e `COORDENADOR`.
- O handler valida o campus com `require_campus_access`, verifica duplicidade de bloco e número no escopo do campus e registra auditoria com `TipoEventoLog.ALTERACAO`.
- `PATCH /turmas/{id}` permite alterar `professor_id` e `turno_preferido`, restrito a `ADMIN`, `COORDENADOR` e `SECRETARIA`.
- O desvínculo do professor é suportado explicitamente por `{"professor_id": null}`, usando `model_fields_set`.
- Para `ADMIN`, professor de campus divergente retorna `HTTP 400 Bad Request`; para os demais perfis, retorna `HTTP 404 Not Found`.
- Professor inexistente, com perfil diferente de `PROFESSOR` ou inativo é rejeitado.
- Toda alteração de turma gera evento em `LogAlocacao` com `TipoEventoLog.ALTERACAO`.

### 8.2.5 Cancelamento de Matrícula (`DELETE /matriculas/{id}`)

- `ALUNO` só pode cancelar a própria matrícula; tentativa de cancelar matrícula de terceiro retorna `HTTP 403 Forbidden`.
- `SECRETARIA`, `COORDENADOR` e `ADMIN` passam por `require_campus_access`.
- O cancelamento usa update condicional atômico (`Matricula.status != "cancelada"`), impedindo condição de corrida e decremento duplo de `Turma.num_matriculados`.
- O decremento de vagas é atômico e limitado a `num_matriculados > 0`.
- O `POST /matriculas` reativa matrícula cancelada, evitando bloqueio permanente pela `UniqueConstraint`.
- O cancelamento gera evento em `LogAlocacao` com `TipoEventoLog.CANCELAMENTO`.
- Conflito de integridade no cancelamento retorna `HTTP 409 Conflict`.

### 8.2.6 Consultas Unitárias Protegidas

`GET /cursos/{id}` e `GET /disciplinas/{id}` foram adicionados com `require_campus_access`. Tentativas de acesso cross-campus retornam `HTTP 404 Not Found`, em linha com o restante da API.

### 8.2.7 Matriz de Permissões (RBAC) Implementada

| Cenário | Admin | Coordenador | Secretaria | Professor | Aluno |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Consultar dados de qualquer campus | SIM | NAO | NAO | NAO | NAO |
| Consultar dados do próprio campus | SIM | SIM | SIM | SIM | SIM |
| Criar usuários `PROFESSOR` e `ALUNO` | SIM | SIM | SIM | NAO | NAO |
| Criar `SECRETARIA` | SIM | SIM | NAO | NAO | NAO |
| Criar `COORDENADOR` ou `ADMIN` | SIM | NAO | NAO | NAO | NAO |
| Criar salas (`POST /salas`) | SIM | SIM | NAO | NAO | NAO |
| Editar salas (`PATCH`/`PUT /salas/{id}`) | SIM | SIM | NAO | NAO | NAO |
| Criar turmas, cursos e disciplinas (`POST`) | SIM | SIM | SIM | NAO | NAO |
| Editar turmas (`PATCH /turmas/{id}`) | SIM | SIM | SIM | NAO | NAO |
| Cancelar matrícula de terceiros | SIM | SIM | SIM | NAO | NAO |
| Cancelar a própria matrícula | NAO | NAO | NAO | NAO | SIM |

---

## 8.3 Banco de Dados e Migrations

A Sprint 08 **não introduziu alterações de schema**. Os PRs #94 e #95 modificaram código de API, schemas Pydantic, testes e a especificação; não há novos arquivos em `alembic/versions/`.

Consequências:

- Nenhuma migration nova foi necessária.
- Nenhuma tabela, coluna, índice ou constraint foi criada ou removida.
- O modelo relacional da Sprint 07 permanece válido e é reutilizado integralmente.
- A trilha de auditoria continua usando a tabela `LogAlocacao` já existente.
- Os testes de integração usam SQLite em memória com o mesmo schema, sem impacto no PostgreSQL de produção.

---

## 8.4 Frontend

O frontend da Sprint 08 está dividido em dois PRs ainda abertos:

- **PR #96:** tratamento centralizado de `HTTP 403`, guards e interceptor de autorização.
- **PR #97:** navegação e componentes condicionados ao perfil autenticado.

Como ambos permanecem em revisão (Gate 2), esta seção registra o escopo planejado e **não** afirma que a camada visual da Sprint 08 está concluída na `main`.

O que já existe na `main`, herdado das sprints anteriores:

- SPA Angular 20 com rotas protegidas por `RoleGuard`.
- `authInterceptor` para inclusão do token JWT.
- Telas de administração, secretaria, professor e aluno.
- Dashboard, relatórios, filtros, busca textual e exportação CSV.

O que depende dos PRs #96 e #97:

- Redirecionamento e mensagem amigável em respostas `403`.
- Menu lateral e ações condicionados ao perfil.
- Ocultação de controles administrativos para perfis sem permissão.

Os 150 testes de frontend foram executados na `main` atual, **sem** os PRs #96 e #97. Após o merge, a suíte deve ser reexecutada.

`[PREENCHER: reexecutar testes do frontend apos o merge de #96 e #97]`

---

## 8.5 Evidências Visuais

As figuras abaixo devem ser capturadas da aplicação em execução, uma por perfil, demonstrando o isolamento de campus e as restrições de interface.

### 8.5.1 Administrador

Acesso global a todos os campi, gestão de usuários de qualquer perfil, edição de salas e turmas, aprovação de sugestões e consulta à auditoria.

![Figura 18 - Fluxo do Administrador](images/print_18_admin.png)

*Figura 18 - [PREENCHER: print do fluxo do Administrador].*

### 8.5.2 Coordenador

Acesso restrito ao próprio campus, gestão de secretarias, professores e alunos, edição de turmas e cancelamento de matrículas, sem permissão para conceder `ADMIN` ou `COORDENADOR`.

![Figura 19 - Fluxo do Coordenador](images/print_19_coordenador.png)

*Figura 19 - [PREENCHER: print do fluxo do Coordenador].*

### 8.5.3 Secretaria

Acesso restrito ao próprio campus, criação e edição de professores e alunos, cancelamento de matrículas, sem permissão para conceder perfis elevados nem editar salas.

![Figura 20 - Fluxo da Secretaria](images/print_20_secretaria.png)

*Figura 20 - [PREENCHER: print do fluxo da Secretaria].*

### 8.5.4 Professor

Consulta às próprias turmas e horários no campus, sem acesso a endpoints administrativos.

![Figura 21 - Fluxo do Professor](images/print_21_professor.png)

*Figura 21 - [PREENCHER: print do fluxo do Professor].*

### 8.5.5 Aluno

Consulta aos próprios dados e matrículas, com cancelamento exclusivo da própria matrícula e bloqueio de acesso a dados de terceiros.

![Figura 22 - Fluxo do Aluno](images/print_22_aluno.png)

*Figura 22 - [PREENCHER: print do fluxo do Aluno].*

---

## 8.6 Testes TDD e Métricas

Os comandos de backend foram executados a partir de `backend/`, com o interpretador do venv temporário `C:\Users\Usuario\AppData\Local\Temp\opencode\sigaas-venv\Scripts\python.exe`. O comando de frontend foi executado a partir de `frontend/`.

### 8.6.1 Backend (Pytest)

```bash
python -m pytest tests -v --cov=app --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=85
```

(trecho)

```text
================ 15 failed, 240 passed, 21 warnings in 57.41s =================
Required test coverage of 85% reached. Total coverage: 88.33%
```

As 15 falhas são exclusivamente de ambiente do motor C, que não foi compilado nesta máquina por ausência de compilador C e da biblioteca `motor_alocacao.so`:

| Arquivo | Falhas | Causa |
| :--- | :---: | :--- |
| `backend/tests/test_api_alocacao.py` | 4 | Biblioteca do motor C não carregada |
| `backend/tests/test_api_motor.py` | 2 | Biblioteca do motor C não carregada |
| `backend/tests/test_motor_c.py` | 7 | `RuntimeError: Biblioteca do motor C nao esta carregada` |
| `backend/tests/test_motor_service.py` | 2 | Biblioteca do motor C não carregada |

Não houve falha em testes de RBAC, isolamento multi-campus ou ciclo de vida de matrículas.

### 8.6.2 Testes Dedicados da Sprint 08

```bash
python -m pytest tests/test_rbac_security.py tests/test_multicampus_isolation.py tests/test_matriculas_lifecycle.py -q --no-cov
```

(trecho)

```text
53 passed, 1 warning in 17.30s
```

A execução com `-v` foi usada apenas para extrair os nomes reais das funções de teste apresentados na seção 8.6.4; a saída foi salva fora do repositório.

### 8.6.3 Frontend (Karma/Jasmine)

```bash
npx ng test --no-watch --browsers=ChromeHeadless
```

(trecho)

```text
Chrome Headless 156.0.0.0 (Windows 10): Executed 150 of 150 SUCCESS (0.553 secs / 0.48 secs)
TOTAL: 150 SUCCESS
```

A execução ocorreu na `main` atual, sem os PRs #96 e #97.

### 8.6.4 Matriz de Testes Executados

| Arquivo | Função de teste | Obtido |
| :--- | :--- | :---: |
| `test_rbac_security.py` | `test_require_campus_access_admin_autoriza_qualquer_campus` | PASSOU |
| `test_rbac_security.py` | `test_require_campus_access_mesmo_campus_autoriza` | PASSOU |
| `test_rbac_security.py` | `test_require_campus_access_outro_campus_retorna_404` | PASSOU |
| `test_rbac_security.py` | `test_require_campus_access_campus_nulo_ou_invalido_retorna_404` | PASSOU |
| `test_rbac_security.py` | `test_require_campus_access_usuario_sem_campus_gera_404` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_tenta_criar_admin_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_tenta_criar_coordenador_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_tenta_criar_secretaria_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_cria_professor_no_proprio_campus_retorna_201` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_cria_aluno_no_proprio_campus_retorna_201` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_tenta_criar_admin_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_tenta_criar_coordenador_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_cria_secretaria_no_proprio_campus_retorna_201` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_cria_professor_no_proprio_campus_retorna_201` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_cria_aluno_no_proprio_campus_retorna_201` | PASSOU |
| `test_rbac_security.py` | `test_coordenador_tenta_criar_usuario_em_outro_campus_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_secretaria_tenta_criar_usuario_em_outro_campus_retorna_403` | PASSOU |
| `test_rbac_security.py` | `test_nao_admin_tenta_criar_com_campus_inexistente_retorna_403_sem_oraculo` | PASSOU |
| `test_rbac_security.py` | `test_admin_tenta_criar_com_campus_inexistente_retorna_404` | PASSOU |
| `test_rbac_security.py` | `test_admin_pode_criar_qualquer_perfil_em_qualquer_campus` | PASSOU |
| `test_rbac_security.py` | `test_professor_e_aluno_nao_podem_criar_usuarios` | PASSOU |
| `test_multicampus_isolation.py` | `test_coordenador_patch_sala_proprio_campus_sucesso` | PASSOU |
| `test_multicampus_isolation.py` | `test_coordenador_patch_sala_outro_campus_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_sala_conflito_duplicidade` | PASSOU |
| `test_multicampus_isolation.py` | `test_secretaria_patch_sala_forbidden` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_turma_sucesso_mesmo_campus` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_turma_desassociar_professor_sucesso` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_turma_outro_campus_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_turma_professor_outro_campus_retorna_400` | PASSOU |
| `test_multicampus_isolation.py` | `test_patch_turma_professor_inativo_ou_invalido` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_curso_unitario_proprio_campus_sucesso` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_curso_unitario_outro_campus_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_curso_inexistente_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_disciplina_unitario_proprio_campus_sucesso` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_disciplina_unitario_outro_campus_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_get_disciplina_inexistente_retorna_404` | PASSOU |
| `test_multicampus_isolation.py` | `test_admin_acessa_qualquer_curso_e_disciplina` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_aluno_cancela_propria_matricula_sucesso` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_aluno_tenta_cancelar_matricula_de_outro_aluno_forbidden` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_secretaria_cancela_matricula_do_seu_campus` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_coordenador_cancela_matricula_do_seu_campus` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_admin_cancela_matricula_qualquer_campus` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_secretaria_outro_campus_retorna_404` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_professor_nao_pode_cancelar_matricula_forbidden` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_cancelar_matricula_ja_cancelada_bad_request` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_rematricula_apos_cancelamento_sucesso` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_cancelar_matricula_inexistente_retorna_404` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_patch_usuario_alternar_ativo_e_dados` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_auto_edicao_coordenador_e_secretaria_sucesso` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_patch_usuario_email_duplicado_retorna_409` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_patch_usuario_secretaria_tenta_alterar_coordenador_forbidden` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_patch_usuario_coordenador_tenta_alterar_usuario_outro_campus_not_found` | PASSOU |
| `test_matriculas_lifecycle.py` | `test_patch_usuario_coordenador_tenta_promover_para_admin_forbidden` | PASSOU |

### 8.6.5 Resultado Geral da Suíte

| Camada | Resultado real | Observação |
| :--- | :--- | :--- |
| Backend | 255 coletados, 240 aprovados, 15 falhas, cobertura 88,33% | Falhas exclusivas do motor C não compilado no Windows |
| Testes Sprint 08 | 53 aprovados | 21 RBAC + 16 multi-campus + 16 matrículas |
| Frontend | 150 de 150 aprovados | Executado sem os PRs #96 e #97 |
| CI | Workflow CI concluído com sucesso na main (execuções #158 e #160, merges de #94 e #95); PRs #96 e #97 com CI concluído nas branches, ainda sem merge | PR somente de documentação não dispara o CI (`paths-ignore`) |

---

## 8.7 Governança Ágil e Gestão de Tarefas

### 8.7.1 Fluxo SDD e ClickUp

- `SPEC-008` elaborada e aprovada no Gate 1 em 24 de Outubro de 2026.
- Tarefas sincronizadas no ClickUp via `scripts/clickup_sync.py`, script presente no repositório e utilizado nas sprints anteriores.
- IDs registrados: `#86e3vnk2u` (PR 1, RBAC), `#86e3vnk2v` (PR 2, ciclo de vida), `#86e3vnk2w` (PR 3, frontend guards e interceptor), `#86e3vnk2y` (PR 4, frontend por perfil) e `#86e3vnk2z` (PR 5, documentação).

### 8.7.2 Pull Requests da Sprint 08

| PR | Escopo | Situação |
| :---: | :--- | :--- |
| #94 | RBAC, BFLA e `require_campus_access` | Mesclado |
| #95 | Ciclo de vida de usuários, salas, turmas e matrículas | Mesclado |
| #96 | Frontend: guards, interceptor e tratamento de 403 | Aberto, CI concluído na branch, em revisão (Gate 2) |
| #97 | Frontend: navegação e UI por perfil | Aberto, CI concluído na branch, em revisão (Gate 2) |
| PR 5 | Documentação da Sprint 08 | Em elaboração |

### 8.7.3 CI e Limite de Diff

- Workflow CI concluído com sucesso na main (execuções #158 e #160, merges de #94 e #95); PRs #96 e #97 com CI concluído nas branches, ainda sem merge.
- O workflow `.github/workflows/ci.yml` possui `paths-ignore` para `docs/**` e `*.md`; PRs exclusivamente de documentação não disparam a esteira de código.
- O script `scripts/check_pr_size.py` ignora `^docs/` e `^.*\.md$`, portanto o relatório não é contabilizado no limite de diff de código.
- O limite de 400 linhas permanece aplicável aos PRs de código.

---

## 8.8 Conclusão e Próximos Passos

O backend da Sprint 08 está concluído e mesclado, com isolamento multi-campus centralizado, proteção contra BFLA e BOLA/IDOR, ciclo de vida completo de usuários, salas, turmas e matrículas, cancelamento concorrente seguro e auditoria persistida. O sistema encontra-se em status **Praticamente Concluído**, condicionado à revisão e ao merge dos PRs #96 e #97, que finalizam a experiência de navegação por perfil no frontend.

Próximos passos:

1. Concluir a revisão e o merge dos PRs #96 e #97.
2. Reexecutar a suíte de frontend após o merge.
3. Confirmar o resultado do CI na aba Actions.
4. Inserir os prints dos cinco perfis.
5. Publicar a tag `v0.8.0-sprint08` após o Gate 2 humano.
6. Gerar o PDF consolidado da entrega.
