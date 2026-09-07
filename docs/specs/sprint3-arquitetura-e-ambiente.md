# [SPEC-004] Arquitetura de Servicos FastAPI, Integracao ctypes com Motor C e Setup Angular

- **Sprint:** Sprint 3
- **Autor / Agente:** Planner-SDD (Antigravity)
- **Status:** Em Revisao (Gate 1)
- **Data de Criacao:** 2026-09-07
- **ID ClickUp (Epico/Task):** 86e35cac7

---

## 1. Contexto e Objetivos

O projeto SIGAAS necessita estabelecer a fundacao arquitetural completa da aplicacao para viabilizar as entregas de negocio das sprints subsequentes. Nesta Sprint 3, estruturamos os servicos nucleares do FastAPI, validamos a integracao de computacao de alto desempenho entre Python e o motor C (OpenMP) via `ctypes`, e inicializamos a aplicacao Single Page Application (SPA) em Angular com roteamento por perfil de acesso.

Para cumprir a regra de governanca de diff maximo de 300 a 400 linhas de codigo por entrega, a Sprint 3 e dividida em tres Pull Requests incrementais e independentemente testaveis:
1. **PR 1**: `feat(api): routers estruturados e schemas pydantic v2 para entidades nucleares`
2. **PR 2**: `feat(engine): integracao ctypes do motor c openmp, endpoint de teste e dockerfile`
3. **PR 3**: `feat(web): inicializacao do projeto angular com layout shell e rotas por perfil`

---

## 2. Historias de Usuario e Criterios de Aceite (Gherkin)

### PR 1: Routers e Schemas FastAPI
> **Como** Desenvolvedor Backend  
> **Quero** uma estrutura modular de rotas no FastAPI com endpoints organizados sob `/api/v1/` e schemas Pydantic v2  
> **Para que** as interfaces e modulos possam consultar e manipular recursos com validacao estrita e injecao de conexao com banco.

#### Criterios de Aceite:
```gherkin
Cenario: Listagem de campi via router modular
  Dado que existem campi cadastrados no banco de dados
  Quando enviar uma requisicao GET para "/api/v1/campi"
  Entao o sistema deve retornar codigo HTTP 200 OK
  E o corpo da resposta deve ser uma lista serializada conforme o schema CampusRead

Cenario: Validacao de dados na criacao de campus
  Dado que o payload de criacao de campus contem campos invalidos ou ausentes
  Quando enviar uma requisicao POST para "/api/v1/campi"
  Entao o sistema deve rejeitar a requisicao
  E retornar codigo HTTP 422 Unprocessable Entity com detalhes dos erros de validacao

Cenario: Isolamento e modularizacao dos routers
  Dado o carregamento da aplicacao FastAPI
  Quando a arvore de rotas for inspecionada
  Entao devem existir sub-roteadores dedicados para "campi", "usuarios", "salas", "turmas" e "horarios" sob o prefixo "/api/v1"
```

---

### PR 2: Wrapper ctypes, Motor C (OpenMP), Endpoint de Validacao e Dockerfile
> **Como** Desenvolvedor de Sistemas e Backend  
> **Quero** um servico Python que carregue a biblioteca compilada do motor C e execute rotinas paralelizadas com OpenMP  
> **Para que** a viabilidade da comunicacao em memoria seja validada antes da implementacao do algoritmo combinatorio complexo.

#### Criterios de Aceite:
```gherkin
Cenario: Consulta de versao do motor C via endpoint de status
  Dado que a biblioteca compartilhada do motor C esta compilada
  Quando enviar uma requisicao GET para "/api/v1/motor/status"
  Entao o servico deve chamar obter_versao_motor() via ctypes
  E retornar codigo HTTP 200 OK com status "online" e string de versao informando OpenMP

Cenario: Teste de integracao e execucao paralela OpenMP via API
  Dado um payload de teste com dois operandos inteiros a=15 e b=27
  Quando enviar uma requisicao POST para "/api/v1/motor/teste-integracao"
  Entao o backend deve executar a funcao testar_integracao_ctypes() no motor C
  E retornar codigo HTTP 200 OK com o resultado 42 e metricas de integracao ctypes

Cenario: Build reprodutivel em container Docker
  Dado o Dockerfile do backend executado via Docker Compose
  Quando o container "sigaas_backend" for compilado
  Entao o ambiente deve instalar gcc e dependencias OpenMP, compilar o motor_alocacao.so e subir o servidor uvicorn
```

---

### PR 3: Setup do Frontend Angular com Roteamento por Perfil e CI
> **Como** Desenvolvedor Frontend e Usuario Final  
> **Quero** a aplicacao Angular inicializada com componentes standalone, layout shell profissional e rotas protegidas  
> **Para que** cada perfil de acesso (Admin, Secretaria, Professor, Aluno) visualize sua area exclusiva de operacao sem poluicao visual.

#### Criterios de Aceite:
```gherkin
Cenario: Navegacao para rotas por perfil de acesso
  Dado o usuario autenticado com perfil "admin"
  Quando navegar para a rota "/admin"
  Entao o Angular Router deve renderizar a visao correspondente dentro do shell comum
  E a barra de navegacao deve exibir apenas icones vetoriais SVG e tipografia profissional (zero emojis)

Cenario: Bloqueio de rota por perfil inadequado
  Dado que o usuario possui perfil "aluno"
  Quando tentar acessar diretamente a URL "/admin"
  Entao o guard de rota deve interceptar a navegacao
  E redirecionar para a area autorizada do aluno ou para a pagina de acesso negado

Cenario: Execucao e aprovacao no CI do GitHub Actions
  Dado o envio do PR de frontend
  Quando o workflow de CI executar
  Entao o job de build e testes do Angular deve ser executado com sucesso
```

---

## 3. Arquitetura e Contratos Tecnicos

### 3.1 PR 1: Arquitetura de Routers e Schemas Pydantic v2
- **Diretorio Raiz**: `backend/app/api/v1/`
- **Agregador de Rotas**: `backend/app/api/v1/api.py` incluindo os routers:
  - `endpoints/campi.py` (prefixo `/campi`, tags `["Campi"]`)
  - `endpoints/usuarios.py` (prefixo `/usuarios`, tags `["Usuarios"]`)
  - `endpoints/salas.py` (prefixo `/salas`, tags `["Salas"]`)
  - `endpoints/turmas.py` (prefixo `/turmas`, tags `["Turmas"]`)
  - `endpoints/horarios.py` (prefixo `/horarios`, tags `["Horarios"]`)
- **Schemas Pydantic v2**: `backend/app/schemas/`
  - `campus.py`: `CampusBase`, `CampusCreate`, `CampusRead`
  - `usuario.py`: `UsuarioBase`, `UsuarioCreate`, `UsuarioRead`
  - `sala.py`: `SalaBase`, `SalaCreate`, `SalaRead`
  - `turma.py`: `TurmaBase`, `TurmaCreate`, `TurmaRead`
  - `horario.py`: `HorarioBase`, `HorarioCreate`, `HorarioRead`
- **Injecao de Sessao**: Uso de `Depends(get_db)` de `app.db.session` garantindo escopo transacional por requisicao.

### 3.2 PR 2: Wrapper ctypes e Motor C (OpenMP)
- **Servico Python**: `backend/app/services/motor_service.py`
  - Busca dinamica da biblioteca compartilhada: `motor_alocacao.so` (Linux/Docker) ou `motor_alocacao.dll` (Windows).
  - Assinaturas `ctypes`:
    - `obter_versao_motor`: `restype = c_char_p`
    - `testar_integracao_ctypes`: `argtypes = [c_int, c_int]`, `restype = c_int`
    - Preparacao da struct `AlocacaoItem` para alinhamento de memoria com C na Sprint 5.
- **Router HTTP**: `backend/app/api/v1/endpoints/motor.py`
  - `GET /api/v1/motor/status`: Retorna status do servico, caminho do binario carregado e versao com OpenMP.
  - `POST /api/v1/motor/teste-integracao`: Recebe `{ "a": int, "b": int }` e retorna `{ "resultado": int, "ctypes_ok": bool }`.
- **Dockerfile**: `backend/Dockerfile`
  - Base `python:3.12-slim`.
  - Instalacao de pacotes de sistema: `gcc`, `make`, `libomp-dev`.
  - Compilacao automatica de `backend/motor_alocacao/motor_alocacao.so`.
  - Instalacao de `backend/requirements.txt`.
  - Comando de inicializacao: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### 3.3 PR 3: Setup do Frontend Angular
- **Estrutura SPA**: Angular 20 Standalone em `frontend/`
- **Layout Shell**: `frontend/src/app/shared/components/shell/` com barra de navegacao superior e menu lateral limpo. Uso exclusivo de icones vetoriais SVG (zero emojis).
- **Rotas e Guards**:
  - `/login`: Formulario inicial de login.
  - `/admin`: Dashboard e administracao de campi e salas.
  - `/secretaria`: Gestao academica, cursos e matriculas.
  - `/professor`: Consulta de turmas e salas atribuidas.
  - `/aluno`: Consulta de grade horaria individual.
  - `AuthGuard` e `RoleGuard`: Validacao de perfil ativo com armazenamento em estado local/servico reativo.
- **Pipeline CI**: Atualizacao de `.github/workflows/ci.yml` com job `frontend-ci` executando build e checagem de tipos (`npm ci && npm run build`).

---

## 4. Plano de Testes TDD (Fase RED)

### 4.1 Testes do PR 1 (FastAPI Routers e Schemas)
- [ ] `backend/tests/test_api_campi.py::test_listar_campi_retorna_200`: Valida listagem com schema correto.
- [ ] `backend/tests/test_api_campi.py::test_criar_campus_valido_e_invalido`: Valida persistencia e rejeicao 422 em schema incorreto.
- [ ] `backend/tests/test_api_routers_structure.py::test_todos_os_routers_registrados`: Garante integracao de todos os sub-roteadores sob `/api/v1`.

### 4.2 Testes do PR 2 (Motor C ctypes e OpenMP)
- [ ] `backend/tests/test_motor_service.py::test_carregar_biblioteca_motor`: Valida carregamento e resolucao de tipos do binario C.
- [ ] `backend/tests/test_motor_service.py::test_execucao_funcao_ctypes_openmp`: Valida soma paralelizada com OpenMP no motor C.
- [ ] `backend/tests/test_api_motor.py::test_endpoint_motor_status_e_teste`: Valida respostas HTTP dos endpoints `/api/v1/motor`.

### 4.3 Testes do PR 3 (Frontend Angular)
- [ ] `frontend/src/app/app.routes.spec.ts`: Valida configuracao de rotas principais e carregamento modular dos componentes por perfil.
- [ ] `frontend/src/app/guards/auth.guard.spec.ts`: Valida bloqueio de navegacao quando perfil nao corresponde a permissao requerida.

---

## 5. Decomposicao de Tarefas para o ClickUp

### PR 1: Routers e Schemas FastAPI
- [ ] [PR 1 - TDD] Escrever testes automatizados de integracao dos routers FastAPI (RED)
- [ ] [PR 1 - Backend] Implementar schemas Pydantic v2 para as entidades nucleares
- [ ] [PR 1 - Backend] Implementar routers v1 (campi, usuarios, salas, turmas, horarios) e injecao de sessao
- [ ] [PR 1 - Review] Executar comite de debate adversarial, auditoria de diff (<= 400) e submeter PR

### PR 2: Wrapper ctypes e Motor C
- [ ] [PR 2 - TDD] Escrever testes unitarios do wrapper ctypes e endpoints do motor C (RED)
- [ ] [PR 2 - Engine/Backend] Implementar app/services/motor_service.py e router /api/v1/motor
- [ ] [PR 2 - DevOps] Criar backend/Dockerfile com compilacao de C/OpenMP e testar docker-compose
- [ ] [PR 2 - Review] Executar comite de debate adversarial, auditoria de diff (<= 400) e submeter PR

### PR 3: Setup do Frontend Angular
- [ ] [PR 3 - TDD] Escrever testes de roteamento e auth guard no Angular (RED)
- [ ] [PR 3 - Frontend] Inicializar aplicacao Angular Standalone com SCSS e layout shell sem emojis
- [ ] [PR 3 - Frontend] Configurar rotas por perfil (/admin, /secretaria, /professor, /aluno)
- [ ] [PR 3 - DevOps] Adicionar job frontend-ci no GitHub Actions (.github/workflows/ci.yml)
- [ ] [PR 3 - Review] Executar comite de debate adversarial, auditoria de diff (<= 400) e submeter PR
