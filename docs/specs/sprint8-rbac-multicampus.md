# [SPEC-008] Revisao Geral de Permissoes (RBAC), Isolamento Multi-Campus e Consolidacao de Regras de Negocio

- **Sprint:** Sprint 08 - Sistema Praticamente Concluido
- **Autor / Agente:** Planner-SDD & Squad SIGAAS
- **Status:** Aprovado (Gate 1 em 2026-10-24)
- **Data de Criacao:** 2026-10-24
- **Prazo de Entrega Academica:** 2026-10-31 23:59
- **IDs ClickUp (Tasks da Sprint 08):**
  - PR 1 (Backend Security & RBAC): `#86e3vnk2u`
  - PR 2 (Backend CRUD Lifecycle): `#86e3vnk2v`
  - PR 3 (Frontend Guards & Interceptors): `#86e3vnk2w`
  - PR 4 (Frontend UI Role-Based): `#86e3vnk2y`
  - PR 5 (Pacote Academico & Release): `#86e3vnk2z`

---

## 1. Contexto e Objetivos

Com a conclusao da Sprint 07, o SIGAAS alcancou o status de Sistema Quase Completo, dispondo de Dashboard institucional, exportacao em streaming CSV, relatorios de ocupacao, trilha de auditoria em `LogAlocacao`, motor de alocacao em C/OpenMP e modelo preditivo de absenteismo com scikit-learn.

Para atingir o marco avaliativo da Sprint 08 (**Sistema Praticamente Concluido**), e mandatorio realizar uma auditoria de ponta a ponta nas regras de autorizacao (RBAC), no isolamento de dados entre campi (multi-tenancy) e na consistencia dos fluxos operacionais, assegurando aderencia aos padroes OWASP API Security Top 10 (especialmente mitigacao de BOLA/IDOR e BFLA).

### 1.1 Diagnostico de Estado Atual (Auditoria de 2026-10-24)

| Componente | Estado Atual | Ponto de Atencao / Vulnerabilidade Identificada | Acao Necessaria na Sprint 08 |
| :--- | :--- | :--- | :--- |
| **Criacao de Usuarios** | `POST /usuarios` acessivel por Admin, Coordenador e Secretaria | Secretaria ou Coordenador podem instanciar usuarios com perfil `admin` (Broken Function Level Authorization / BFLA) | Bloquear criacao de perfil superior ou igual ao do criador (somente Admin cria Admin; Coordenador/Secretaria criam Professor/Aluno) |
| **Ciclo de Vida de Usuarios** | Apenas `GET` e `POST` | Nao ha endpoint para inativar, reativar ou atualizar cadastro de usuarios | Implementar `PATCH /usuarios/{id}` para ativacao/desativacao e atualizacao cadastral com checagem de permissao |
| **Ciclo de Vida de Salas/Turmas** | `POST` disponivel, sem `PATCH`/`DELETE` | Coordenador/Secretaria nao conseguem desativar sala ou cancelar turma sem intervencao direta no banco | Implementar `PATCH /salas/{id}` e `PATCH /turmas/{id}` com verificacao de campus e registro de log |
| **Cancelamento de Matricula** | `POST /matriculas` existe, mas sem cancelamento | Aluno nao consegue trancar/cancelar matricula; contagem `num_matriculados` fica congelada | Implementar `DELETE /matriculas/{id}` com decremento atomico de vagas e validacao de posse |
| **Isolamento de Entidades Academicas** | `GET /cursos/{id}` e `GET /disciplinas/{id}` ausentes | Consultas pontuais necessitam de listagens completas; falta validacao de posse por ID | Adicionar endpoints unitarios com retorno `404 Not Found` em caso de recurso de outro campus |
| **Tratamento de 403 no Frontend** | `authInterceptor` trata apenas 401 | Erro 403 (Forbidden) nao possui feedback visual amigavel nem redirecionamento limpo | Capturar 403 no interceptor, exibir toast de permissao negada e proteger rotas via `RoleGuard` |
| **Navegacao por Perfil na UI** | Menus visiveis com filtragem parcial | Alguns botoes de acao (ex.: cadastros) aparecem para perfis que nao possuem permissao de escrita | Ocultar acoes e abas administrativas para perfis estritamente operacionais ou de consulta |

---

## 2. Matriz Geral de Permissoes (RBAC) e Isolamento de Campus

### 2.1 Matriz de Acesso aos Endpoints REST

| Recurso / Rota | Metodo | Admin | Coordenador | Secretaria | Professor | Aluno | Regra de Escopo / Campus |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `/api/v1/auth/login`, `/auth/me` | POST / GET | Sim | Sim | Sim | Sim | Sim | Publico (login) / Proprio usuario (me) |
| `/api/v1/campi` | GET | Sim | Sim | Sim | Sim | Sim | Leitura global de campi |
| `/api/v1/campi` | POST / PATCH | Sim | Nao | Nao | Nao | Nao | Exclusivo superadmin |
| `/api/v1/usuarios` | GET | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Admin ve todos; outros veem apenas seu campus |
| `/api/v1/usuarios` | POST | Sim | Sim (Campus)* | Sim (Campus)* | Nao | Nao | *Nao podem criar perfil Admin ou Coordenador |
| `/api/v1/usuarios/{id}` | PATCH | Sim | Sim (Campus)* | Sim (Campus)* | Nao | Nao | *Apenas ativar/desativar alunos e professores |
| `/api/v1/salas` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Campus) | Sim (Campus) | Leitura de salas ativas do campus |
| `/api/v1/salas` | POST / PATCH | Sim | Sim (Campus) | Nao | Nao | Nao | Gestao de espacos fisicos |
| `/api/v1/cursos`, `/disciplinas` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Campus) | Sim (Campus) | Consulta curricular |
| `/api/v1/cursos`, `/disciplinas` | POST / PATCH | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Gestao de grade curricular |
| `/api/v1/turmas` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Campus) | Sim (Campus) | Consulta de turmas abertas |
| `/api/v1/turmas` | POST / PATCH | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Oferta de turmas por periodo |
| `/api/v1/matriculas` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Turmas prof) | Sim (Proprias) | Visao contextual por perfil |
| `/api/v1/matriculas` | POST | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Matricula de alunos em turmas |
| `/api/v1/matriculas/{id}` | DELETE | Sim | Sim (Campus) | Sim (Campus) | Nao | Sim (Propria)* | *Aluno so pode cancelar matricula propria |
| `/api/v1/horarios/meus` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Proprios) | Sim (Proprios) | Grade semanal contextualizada |
| `/api/v1/horarios` | GET | Sim | Sim (Campus) | Sim (Campus) | Sim (Campus) | Sim (Campus) | Consulta geral com filtros |
| `/api/v1/alocacao/otimizar` | POST | Sim | Sim (Campus) | Nao | Nao | Nao | Disparo do algoritmo combinatorio C |
| `/api/v1/sugestoes` | GET | Sim | Sim (Campus) | Nao | Nao | Nao | Fila de remanejamentos com IA |
| `/api/v1/sugestoes/{id}` | PATCH | Sim | Sim (Campus) | Nao | Nao | Nao | Aprovacao/Rejeicao human-in-the-loop |
| `/api/v1/dashboard/*` | GET | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Indicadores gerenciais e graficos SVG |
| `/api/v1/relatorios/*` | GET | Sim | Sim (Campus) | Sim (Campus) | Nao | Nao | Relatorios tabulares e exportacao CSV |
| `/api/v1/logs` | GET | Sim | Sim (Campus) | Nao | Nao | Nao | Trilha de auditoria (somente leitura) |

---

## 3. Historias de Usuario e Criterios de Aceite (Gherkin)

### Historia 1: Protecao contra Escalacao de Privilegios (BFLA)
> **Como** Administrador do Sistema **quero** que secretarias e coordenadores nao possam criar ou elevar usuarios para cargos administrativos superiores **para** preservar a integridade da governanca de acessos.

```gherkin
Cenario: Secretaria tenta criar usuario Administrador
  Dado que um usuario com perfil "secretaria" do Campus 1 esta autenticado
  Quando enviar uma requisicao POST /api/v1/usuarios com perfil "admin"
  Entao a API deve responder com status 403 Forbidden
  E o corpo da resposta deve informar "Privilegio insuficiente para conceder este perfil"

Cenario: Coordenador cria um Professor em seu campus
  Dado que um Coordenador do Campus 1 esta autenticado
  Quando enviar POST /api/v1/usuarios para cadastrar um "professor" com campus_id = 1
  Entao o status deve ser 201 Created
  E o usuario deve ser persistido como ativo

Cenario: Coordenador tenta criar Professor em outro campus
  Dado que um Coordenador do Campus 1 esta autenticado
  Quando enviar POST /api/v1/usuarios para cadastrar um "professor" com campus_id = 2
  Entao a API deve responder com status 403 Forbidden
```

### Historia 2: Isolamento Estrito Multi-Campus em Operacoes Academicas (BOLA/IDOR)
> **Como** Coordenador de Campus **quero** operar exclusivamente sobre os recursos do meu campus **para** impedir vazamento ou alteracao indevida de dados de outras unidades.

```gherkin
Cenario: Coordenador tenta alterar sala de outro campus
  Dado que o Coordenador do Campus 1 esta autenticado
  E existe uma Sala cadastrada com ID 88 pertencente ao Campus 2
  Quando enviar uma requisicao PATCH /api/v1/salas/88 com payload de atualizacao
  Entao a API deve retornar status 404 Not Found
  E nenhuma alteracao deve ocorrer no banco de dados

Cenario: Criacao de turma com recursos cruzados de campi distintos
  Dado que o Administrador tenta cadastrar uma turma com disciplina do Campus 1 e professor do Campus 2
  Quando enviar POST /api/v1/turmas com essa combinacao cruzada
  Entao a API deve responder com status 400 Bad Request
  E a mensagem deve indicar "Professor pertence a campus diferente da disciplina"
```

### Historia 3: Ciclo de Vida e Cancelamento de Matriculas
> **Como** Aluno ou Secretaria **quero** poder cancelar/desvincular uma matricula ativa **para** liberar a vaga atomicamente para outros discentes.

```gherkin
Cenario: Aluno cancela sua propria matricula
  Dado que um Aluno com ID 15 possui matricula ativa com ID 100 na Turma 5 (que possui 30 matriculados)
  Quando o Aluno autenticado enviar DELETE /api/v1/matriculas/100
  Entao o status deve ser 200 OK ou 204 No Content
  E o numero de matriculados da Turma 5 deve ser decrementado atomicamente para 29
  E o status da matricula deve transitar para "cancelada"

Cenario: Aluno tenta cancelar matricula de outro aluno
  Dado que o Aluno com ID 15 tenta enviar DELETE /api/v1/matriculas/101 (pertencente ao Aluno 20)
  Entao a API deve responder com status 403 Forbidden
```

### Historia 4: Experiencia e Blindagem no Frontend (Angular)
> **Como** usuario do sistema **quero** que a interface reflita com precisao meu perfil de acesso e trate restricoes com sobriedade **para** garantir uma experiencia sem falhas visuais.

```gherkin
Cenario: Tentativa de navegacao direta para rota nao autorizada via URL
  Dado que um usuario logado com perfil "aluno" digita a URL "/admin" no navegador
  Quando o roteador do Angular avaliar a rota
  Entao o RoleGuard deve interceptar a navegacao
  E redirecionar o usuario imediatamente para "/aluno" sem apresentar telas em branco

Cenario: Resposta HTTP 403 interceptada na SPA
  Dado que uma requisicao assincrona receba status 403 Forbidden
  Quando o AuthInterceptor processar a resposta
  Entao a interface nao deve deslogar o usuario
  E deve emitir uma notificacao informativa de acesso restrito
```

---

## 4. Design de Arquitetura

### 4.1 Backend (FastAPI)
- **Dependencia Centralizada de Seguranca (`app/api/deps.py`)**:
  - Criacao de `require_campus_access(resource_campus_id, current_user)` para encapsular a regra padrao: se `ADMIN`, permite; se outro perfil, exige `current_user.campus_id == resource_campus_id`, lancando `404 Not Found` (evitando reconhecimento de IDOR).
  - Validacao hierarquica em `usuarios.py`:
    - Admin: cria/edita qualquer perfil.
    - Coordenador: cria/edita apenas Secretaria, Professor e Aluno do seu campus.
    - Secretaria: cria/edita apenas Professor e Aluno do seu campus.
- **Novos Endpoints de Ciclo de Vida**:
  - `PATCH /api/v1/usuarios/{id}`: alternancia de `ativo` e atualizacao de dados basicos.
  - `PATCH /api/v1/salas/{id}`: atualizacao de capacidade, bloco, numero e status ativo.
  - `PATCH /api/v1/turmas/{id}`: alteracao de professor responsavel e turno preferido.
  - `DELETE /api/v1/matriculas/{id}`: cancelamento com decremento atomico de `num_matriculados` via `update(Turma)`.
  - `GET /api/v1/cursos/{id}` e `GET /api/v1/disciplinas/{id}`: leituras unitarias protegidas por campus.

### 4.2 Frontend (Angular SPA)
- **Guards e Roteamento**:
  - Manutencao de `RoleGuard` com checagem estrita contra a matriz RBAC.
  - Tratamento de rotas filhas no `ShellComponent`.
- **AuthInterceptor**:
  - Interceptacao de status 403: notificacao de privilegio insuficiente sem perda da sessao ativa.
  - Interceptacao de status 401: logout limpo e retorno a `/login`.
- **Design System Sobrio**:
  - Ocultacao estrita de botoes de acao (botoes de remanejamento, novo cadastro de sala, alocacao automatica) caso o perfil ativo nao possua o papel requerido.
  - Zero emojis, mantendo icones vetoriais SVG e padrao corporativo.

---

## 5. Fatiamento em PRs (Limite Rigoroso de 400 Linhas)

| PR | Escopo Tecnico | Conventional Commit | Dependencia | Responsavel |
| :---: | :--- | :--- | :---: | :--- |
| **PR 1** | **Backend Security & RBAC Core**: Dependencias centralizadas de autorizacao e protecao contra BFLA em `usuarios.py` | `feat(security): implementar protecao bfla e autorizacao hierarquica` | - | Osvaldo Vasconcelos |
| **PR 2** | **Backend CRUD Lifecycle**: Endpoints de `PATCH /salas`, `PATCH /turmas`, `DELETE /matriculas` e `GET /{id}` de cursos/disciplinas | `feat(academico): implementar ciclo de vida e cancelamento de matriculas` | PR 1 | Osvaldo Vasconcelos |
| **PR 3** | **Frontend Guards & Interceptors**: Interceptacao de 403 no `AuthInterceptor`, reforco de `RoleGuard` e fallback gracioso | `feat(frontend): aprimorar guards de perfil e interceptor de permissoes` | PR 1 | Gabriel Porfirio |
| **PR 4** | **Frontend Role-Based UI**: Ocultacao contextual de acoes, blindagem dos paineis Admin/Secretaria/Docente | `feat(frontend): consolidar visibilidade de acoes por perfil de acesso` | PR 2, 3 | Gabriel Porfirio |
| **PR 5** | **Pacote Academico**: Relatorio da Sprint 08, consolidado Sprints 01-08 e PDF oficial ABNT | `docs(academic): consolidar relatorio e pdf oficial da sprint 08` | PR 1 a 4 | Flavio Vecch / Equipe |

---

## 6. Plano de Testes TDD

### Backend (Pytest)
1. `tests/test_rbac_security.py`:
   - Tentativa de secretaria criar coordenador ou admin (espera 403).
   - Coordenador tentando cadastrar usuario em outro campus (espera 403).
   - Tentativa de aluno ou professor acessar endpoints de dashboard, relatorios ou auditoria (espera 403).
2. `tests/test_multicampus_isolation.py`:
   - Coordenador do Campus 1 tentando alterar sala do Campus 2 (espera 404).
   - Consulta de cursos/disciplinas de outro campus por ID direto (espera 404).
   - Validacao de erro 400 ao tentar associar turma com professor de outro campus.
3. `tests/test_matriculas_lifecycle.py`:
   - Cancelamento de matricula pelo proprio aluno e decremento atomico de vagas da turma.
   - Tentativa de aluno cancelar matricula de terceiro (espera 403).

### Frontend (Karma/Jasmine)
1. `role.guard.spec.ts`:
   - Testar bloqueio de rota e redirecionamento de acordo com o perfil atual.
2. `auth.interceptor.spec.ts`:
   - Validar que erro 403 nao invoca `authService.logout()`.
3. `shell.component.spec.ts`:
   - Validar que menus restritos nao sao renderizados no DOM para aluno e professor.

---

## 7. Portões de Decisão e Gestão de Riscos (Gates)

- **Gate 1 (Atual)**: Aprovacao formal desta especificacao pelo usuario/tech lead antes da abertura de branches ou codigo.
- **Gate 2**: Revisao de PRs pre-merge, com debate adversarial obrigatorio e sem auto-merge.
- **Riscos Identificados**:
  - *Risco de Regressao em Rotas Existentes:* A suite de 202 testes de backend e 150 testes de frontend deve permanecer 100% verde apos a introducao das validacoes adicionais.
  - *Risco de Tamanho de Diff:* O fatiamento em 5 PRs garante que cada entrega permaneca rigorosamente abaixo do teto de 400 linhas.
