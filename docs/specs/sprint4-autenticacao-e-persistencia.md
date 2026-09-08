# [SPEC-005] Autenticacao JWT, Gestao de Espacos e Operacoes Academicas Funcionais

- **Sprint:** Sprint 4
- **Autor / Agente:** Planner-SDD (Antigravity)
- **Status:** Em Revisao (Gate 1)
- **Data de Criacao:** 2026-09-07
- **ID ClickUp (Epico/Task):** 86e36p3ev

---

## 1. Contexto e Objetivos

A Sprint 4 tem como missao operacionalizar o acesso autenticado ao sistema e viabilizar as operacoes reais de cadastro e consulta sobre o PostgreSQL, consolidando o fluxo entre o backend FastAPI e o frontend Angular.

Para atender rigorosamente a regra de governanca de diff maximo de 300 a 400 linhas de codigo modificado por Pull Request (AGENTS.md), o escopo da Sprint 4 foi estruturado em quatro PRs verticais atomicos, funcionais e independentemente testaveis:

1. **PR 1**: `feat(auth): autenticacao jwt, hash bcrypt e formulario de login real com atalhos de demo`
2. **PR 2**: `feat(admin): crud de campi, salas e equipamentos com abas administrativas e multi-tenancy`
3. **PR 3**: `feat(secretaria): gestao de cursos, turmas, matriculas e integridade de contagem`
4. **PR 4**: `feat(portal): consulta de horarios atribuidos e grade semanal do professor e aluno`

---

## 2. Historias de Usuario e Criterios de Aceite (Gherkin)

### PR 1: Autenticacao JWT, Seguranca e Login Real
> **Como** Usuario do SIGAAS (Admin, Coordenador, Secretaria, Professor ou Aluno)  
> **Quero** realizar autenticacao com email e senha na interface web, receber um token JWT assinado e ter acesso contextualizado ao meu perfil  
> **Para que** minhas permissoes institucionais sejam respeitadas e minhas credenciais protegidas com hash criptografico.

#### Criterios de Aceite:
```gherkin
Cenario: Autenticacao com credenciais validas
  Dado que existe um usuario ativo com email "admin@sigaas.edu" e senha cadastrada
  Quando enviar uma requisicao POST para "/api/v1/auth/login" com o JSON contendo email e senha corretos
  Entao o sistema deve retornar codigo HTTP 200 OK
  E o corpo da resposta deve conter "access_token", "token_type" igual a "bearer" e o objeto de dados do usuario (id, nome, email, perfil, campus_id)

Cenario: Rejeicao de credenciais incorretas
  Dado que o usuario informa senha incompativel com o hash armazenado
  Quando enviar uma requisicao POST para "/api/v1/auth/login"
  Entao o sistema deve rejeitar a requisicao com codigo HTTP 401 Unauthorized
  E informar detalhe generico "Credenciais invalidas" sem expor se o email existe

Cenario: Consulta do usuario logado via token
  Dado um token JWT valido enviado no header "Authorization: Bearer <token>"
  Quando enviar uma requisicao GET para "/api/v1/auth/me"
  Entao o sistema deve retornar codigo HTTP 200 OK com os dados do usuario logado

Cenario: Login na interface Angular com atalhos de demonstracao
  Dado o usuario na pagina "/login"
  Quando clicar no atalho de demonstracao do perfil "Administrador"
  Entao os campos de email e senha devem ser preenchidos e submetidos via HTTP
  E o usuario deve ser autenticado, armazenar o token e ser redirecionado para "/admin"
```

---

### PR 2: Gestao Administrativa de Espacos (Admin)
> **Como** Administrador ou Coordenador Institucional  
> **Quero** gerenciar campi, salas e equipamentos com controle de capacidade, tipo e turnos  
> **Para que** a infraestrutura fisica esteja devidamente cadastrada para o motor de alocacao de horarios.

#### Criterios de Aceite:
```gherkin
Cenario: Cadastro de sala com turnos e associacao de equipamentos
  Dado um usuario autenticado com perfil "admin"
  Quando enviar uma requisicao POST para "/api/v1/salas" informando campus_id, bloco, numero, tipo, capacidade e turnos_disponiveis
  Entao a sala deve ser persistida com sucesso e retornar codigo HTTP 201 Created
  E respeitar a restricao de unicidade de bloco e numero por campus

Cenario: Bloqueio de usuario sem permissao administrativa
  Dado um usuario autenticado com perfil "aluno"
  Quando tentar enviar uma requisicao POST para "/api/v1/salas" ou "/api/v1/campi"
  Entao o sistema deve interceptar a requisicao
  E retornar codigo HTTP 403 Forbidden com a mensagem de privilegio insuficiente

Cenario: Navegacao por abas contextuais no Angular Admin
  Dado o administrador autenticado na rota "/admin"
  Quando alternar entre as abas "Salas e Espacos", "Campi" e "Equipamentos"
  Entao a tela deve exibir a listagem respectiva com acoes de cadastro rapido sem recarregar a pagina
```

---

### PR 3: Gestao Academica e Matriculas (Secretaria)
> **Como** Secretaria Academica ou Coordenacao  
> **Quero** cadastrar cursos, disciplinas, turmas e matricular alunos mantendo a contagem sincronizada  
> **Para que** a oferta semestral reflita com exatidao o numero de matriculados para dimensionamento de salas.

#### Criterios de Aceite:
```gherkin
Cenario: Cadastro de curso, disciplina e turma
  Dado um usuario autenticado com perfil "secretaria"
  Quando cadastrar um curso, uma disciplina vinculada e criar uma turma para o periodo letivo
  Entao os registros devem ser salvos no PostgreSQL com HTTP 201 Created
  E a turma deve ser inicializada com "num_matriculados" igual a 0

Cenario: Matricula de aluno e incremento automatico de inscritos
  Dado uma turma existente e um usuario autenticado com perfil "secretaria"
  Quando enviar uma requisicao POST para "/api/v1/matriculas" com "aluno_id" e "turma_id"
  Entao o vinculo de matricula deve ser persistido com data atual
  E o campo "num_matriculados" da respectiva turma deve ser incrementado automaticamente

Cenario: Prevencao de duplicidade de matricula do mesmo aluno na turma
  Dado que um aluno ja esta matriculado na turma
  Quando tentar submeter nova requisicao de matricula para o mesmo aluno e turma
  Entao o sistema deve rejeitar a operacao com codigo HTTP 409 Conflict ou 400 Bad Request
```

---

### PR 4: Portal do Professor e Aluno (Horarios e Turmas)
> **Como** Professor ou Aluno  
> **Quero** visualizar minhas turmas atribuidas e meus horarios em formato de grade semanal  
> **Para que** eu localize rapidamente o bloco, sala e horario de cada disciplina sem conflitos.

#### Criterios de Aceite:
```gherkin
Cenario: Professor consulta suas turmas e horarios atribuidos
  Dado um professor autenticado com token JWT valido
  Quando enviar uma requisicao GET para "/api/v1/horarios/meus"
  Entao o backend deve filtrar os horarios onde o professor esta vinculado a turma
  E retornar codigo HTTP 200 OK com detalhes da disciplina, campus, bloco e numero da sala

Cenario: Aluno consulta sua grade horaria semanal
  Dado um aluno autenticado com token JWT valido
  Quando enviar uma requisicao GET para "/api/v1/horarios/meus"
  Entao o backend deve buscar as turmas em que o aluno possui matricula ativa
  E retornar os horarios formatados por dia da semana e faixa horaria

Cenario: Renderizacao visual da grade semanal no Angular
  Dado o usuario autenticado acessando sua area ("/professor" ou "/aluno")
  Quando a tela carregar
  Entao a aplicacao deve exibir uma grade visual de segunda a sabado destacando as aulas alocadas
```

---

## 3. Arquitetura e Contratos Tecnicos

### 3.1 Endpoints FastAPI

#### Nucleo de Autenticacao (`/api/v1/auth`)
- `POST /api/v1/auth/login`:
  - Request: `{ "email": "string", "senha": "string" }`
  - Response (200): `{ "access_token": "string", "token_type": "bearer", "usuario": { "id": int, "nome": "string", "email": "string", "perfil": "string", "campus_id": int } }`
- `GET /api/v1/auth/me`:
  - Header: `Authorization: Bearer <token>`
  - Response (200): `UsuarioRead`

#### Nucleo Administrativo (`/api/v1/salas`, `/api/v1/campi`, `/api/v1/equipamentos`)
- `POST /api/v1/salas`: Criacao de sala com turnos e validacao de capacidade
- `GET /api/v1/equipamentos` e `POST /api/v1/equipamentos`: Gestao de itens de infraestrutura
- `POST /api/v1/salas/{sala_id}/equipamentos`: Vinculacao de equipamento e quantidade

#### Nucleo Academico (`/api/v1/cursos`, `/api/v1/disciplinas`, `/api/v1/matriculas`)
- `POST /api/v1/cursos`: Criacao de curso associado ao campus
- `POST /api/v1/disciplinas`: Criacao de disciplina vinculada a curso
- `POST /api/v1/turmas`: Criacao de turma (disciplina_id, professor_id, periodo_letivo, turno_preferido)
- `POST /api/v1/matriculas`: Criacao de matricula com atualizacao atomica de `num_matriculados`

#### Nucleo de Consulta Pessoal (`/api/v1/horarios`)
- `GET /api/v1/horarios/meus`: Retorna horarios contextuais do usuario autenticado (se professor -> turmas ministradas; se aluno -> turmas matriculadas).

### 3.2 Seguranca e Dependencias FastAPI (RBAC)
- Modulo `app.core.security`: funcoes `verificar_senha()`, `gerar_hash_senha()`, `criar_token_acesso()`.
- Modulo `app.api.deps`:
  - `get_current_user`: valida token JWT e extrai instancia de `Usuario` ativa do banco.
  - `exigir_perfis(*perfis)`: factory de dependencia garantindo autorizacao por perfil.

### 3.3 Script de Seed (`scripts/seed_data.py`)
- Provisiona 2 campi ficticios (Campus Central e Campus Norte).
- Provisiona equipamentos basicos (Projetor HD, Ar-condicionado, Computadores Core i7).
- Provisiona salas dos 4 tipos (regular, laboratorio, auditorio, reuniao).
- Provisiona 4 usuarios padrao com senha criptografada `sigaas123`:
  - `admin@sigaas.edu` (Perfil: admin)
  - `secretaria@sigaas.edu` (Perfil: secretaria)
  - `professor@sigaas.edu` (Perfil: professor)
  - `aluno@sigaas.edu` (Perfil: aluno)

### 3.4 Frontend Angular
- `AuthService`: gerenciamento reativo do token JWT com signals (`currentUser`, `currentRole`), login, logout e persistencia em `localStorage`.
- `AuthInterceptor`: interceptor funcional (`HttpInterceptorFn`) anexando token `Bearer` a todas as chamadas para `/api/v1/`.
- Componentes com Tailwind CSS e icones vetoriais SVG (zero emojis).

---

## 4. Plano de Testes TDD (Test-Driven Development)

### 4.1 Testes de Backend (Pytest)
- [ ] `tests/test_auth.py`: login com sucesso, login com senha incorreta, usuario inexistente, token expirado, endpoint `/auth/me`.
- [ ] `tests/test_admin_crud.py`: criacao de salas, restricao de perfil (403 para aluno), criacao de equipamentos e vinculacao.
- [ ] `tests/test_academico.py`: criacao de curso/disciplina/turma, matricula de aluno, contagem de matriculados e duplicidade.
- [ ] `tests/test_horarios_meus.py`: consulta de horarios atribuidos ao professor e grade do aluno logado.

### 4.2 Testes de Frontend (Jasmine/Karma)
- [ ] `auth.service.spec.ts`: armazenamento de token, signals de autenticacao e logout.
- [ ] `auth.interceptor.spec.ts`: inclusao do header Authorization em requisicoes protegidas.
- [ ] `login.component.spec.ts`: submissao de formulario e atalhos de preenchimento.
- [ ] `admin.component.spec.ts`: alternancia entre abas e renderizacao de listagens.
- [ ] `timetable.component.spec.ts`: renderizacao da matriz semanal de horarios.

---

## 5. Decomposicao de Tarefas para o ClickUp

- [ ] [PR1-TDD] Escrever testes falhos para autenticacao JWT, hash de senha e login
- [ ] [PR1-Back] Implementar modulo de seguranca (passlib/bcrypt/jose) e rotas /auth/login e /auth/me
- [ ] [PR1-Seed] Criar script scripts/seed_data.py com usuarios e infraestrutura basica
- [ ] [PR1-Front] Implementar formulario de login real, AuthService com signals e AuthInterceptor
- [ ] [PR1-Audit] Executar debate adversarial e submeter PR 1 (Diff <= 400 linhas)
- [ ] [PR2-TDD] Escrever testes falhos para endpoints administrativos de salas e equipamentos
- [ ] [PR2-Back] Implementar rotas protegidas de cadastro de salas, equipamentos e associacoes
- [ ] [PR2-Front] Desenvolver painel administrativo com abas contextuais e modais de cadastro
- [ ] [PR2-Audit] Executar debate adversarial e submeter PR 2 (Diff <= 400 linhas)
- [ ] [PR3-TDD] Escrever testes falhos para criacao de cursos, disciplinas, turmas e matriculas
- [ ] [PR3-Back] Implementar rotas academicas e logica de incremento atomico de matriculados
- [ ] [PR3-Front] Desenvolver tela da Secretaria com gestao de turmas e inscricao de alunos
- [ ] [PR3-Audit] Executar debate adversarial e submeter PR 3 (Diff <= 400 linhas)
- [ ] [PR4-TDD] Escrever testes falhos para o endpoint /horarios/meus (professor e aluno)
- [ ] [PR4-Back] Implementar resolucao de horarios contextuais via token do usuario autenticado
- [ ] [PR4-Front] Desenvolver visualizador de grade semanal em timetable grid para professor e aluno
- [ ] [PR4-Audit] Executar debate adversarial e submeter PR 4 (Diff <= 400 linhas)
