# [SPEC-014] Blindagem de Segurança, Política de Senhas, MFA (TOTP) e Paridade RBAC Front/Back

- **Sprint:** Fase de Remediação e Consolidação (M3 — Segurança, MFA e RBAC)
- **Autor / Agente:** Planner-SDD & Squad SIGAAS (Grupo 31)
- **Status:** Draft - Aguardando Gate 1
- **Data de Criação:** 2026-11-27
- **ID ClickUp (Épico/Task):** [Pendente sync]
- **Identificação Acadêmica:** Disciplina: Fábrica de Software & Tópicos Avançados em Computação | Curso: Bacharelado em Ciência da Computação — Turma 8MB - CC | Equipe: Grupo 31 — SIGAAS

## Resumo Executivo e Plano de Entregas (PRs 1 a 5)

Esta especificação define a remediação integral das vulnerabilidades de autenticação, autorização (BFLA/BOLA), ciclo de vida de senhas, proteção de segredos, autenticação multifator (MFA TOTP RFC 6238 com códigos de recuperação) e paridade RBAC entre o backend FastAPI e o frontend Angular 20. A entrega é fatiada em **5 PRs incrementais** (`<= 300` linhas de código de produção por PR, detalhados na Seção 4):

- **PR 1 (`fix/security-endpoints-password-jwt`, ~180 LOC):** Proteção de `/campi`, `/equipamentos` e `/motor`, inclusão de `heuristica` em `MotorStatusResponse`, validação fail-fast de segredos em `config.py`, guarda UTF-8 <= 72 bytes em `security.py`, claims JWT (`iss`, `aud`, `jti`, `scope`), política de senha em `UsuarioCreate` e remoção de `passlib` não utilizado.
- **PR 2 (`feat/auth-password-lifecycle-and-schema`, ~210 LOC):** Migration reversível `004_seguranca_auth_mfa`, revogação de sessão via `token_version` (`ver`) e endpoints `/auth/alterar-senha`, `/auth/logout` e `/usuarios/{id}/redefinir-senha`.
- **PR 3 (`feat/mfa-totp-pyotp-recovery`, ~290 LOC):** Serviço MFA com `pyotp` (RFC 6238), cifra Fernet em repouso (`MFA_ENCRYPTION_KEY`), anti-replay (`ultimo_totp_step`), 8 códigos de recuperação com hash, login em 2 etapas, política obrigatória para `admin`/`coordenador`/`secretaria` e endpoints `/auth/mfa/*` e `/usuarios/{id}/mfa/reset`.
- **PR 4 (`fix/rbac-campus-parity-frontend-backend`, ~240 LOC):** `require_campus_access` em `excluir_sala`, filtro `campus_id` em `/horarios/meus` para `admin`, remoção de `AuthService.setRole()`, validação de `exp`/`scope` no `authGuard`, correção de `hasRole`, liberação de `/secretaria` e `/historico`, `homeRedirectGuard` e seletor dinâmico de campus.
- **PR 5 (`feat/frontend-mfa-and-password-ux`, ~300 LOC):** Fluxo Angular de login em 2 etapas e onboarding obrigatório no `LoginComponent`, além da nova rota `/seguranca` (`SegurancaComponent`) para gestão de TOTP, códigos de recuperação e troca de senha.

---

## 1. Contexto e Diagnóstico Atual

Auditoria técnica realizada diretamente sobre a base atual do SIGAAS identificou cinco grupos críticos de vulnerabilidades e divergências entre backend e frontend, detalhados com coordenadas verificadas abaixo.

### 1.1 Diagnóstico Técnico Verificado (Evidências `file:line`)

| Domínio | Arquivo / Símbolo (`file:line`) | Estado Atual Verificado | Vulnerabilidade / Gap (OWASP / Arquitetura) | Remediação Especificada |
| :--- | :--- | :--- | :--- | :--- |
| **Montagem de Rotas** | `backend/app/api/v1/api.py:28-44` (`api_router`) | Monta os 17 routers sem `dependencies=[Depends(...)]` global. | Segurança depende individualmente de cada endpoint; omissões expõem rotas públicas acidentalmente. | Blindar explicitamente todos os endpoints faltantes (`campi`, `equipamentos`, `motor`) e cobrir em `test_openapi_docs.py`. |
| **Endpoints de Campi** | `backend/app/api/v1/endpoints/campi.py:16-40` (`listar_campi`, `criar_campus`, `obter_campus`) | Zero `Depends(get_current_user)` ou `require_role`; `POST` usa `except Exception: db.rollback(); raise` (`:28-30`) e omite `LogAlocacao`. | **OWASP API1/API5 (BFLA/BOLA):** enumeração anônima de campi e inserção não autenticada de novos campi. | `GET /campi` com `get_current_user` (escopo por `campus_id` para não-admin); `POST /campi` restrito a `ADMIN` com `LogAlocacao`; `GET /campi/{id}` com `get_current_user` + `require_campus_access`. |
| **Endpoints de Equipamentos** | `backend/app/api/v1/endpoints/equipamentos.py:17-25` (`listar_equipamentos`) | `GET` sem `get_current_user` (`POST` `:28-46` já exige `ADMIN`/`COORDENADOR`). | **OWASP API5:** exposição pública do inventário institucional de equipamentos. | Exigir `Depends(get_current_user)` em `GET /api/v1/equipamentos`. |
| **Endpoints e Schema do Motor** | `backend/app/api/v1/endpoints/motor.py:21-60` (`MotorStatusResponse`, `obter_status_motor`, `executar_teste_motor`) | `GET /status` e `POST /teste-integracao` sem autenticação; `MotorStatusResponse` (`:21-25`) omite `"heuristica"` retornado por `motor_service.py:218`. | **OWASP API5 + Drift de Contrato:** invocação anônima de FFI C (`lib.testar_integracao_ctypes`) e ocultação do campo `heuristica` no OpenAPI. | Restringir `/motor/status` e `/motor/teste-integracao` a `ADMIN`/`COORDENADOR` e adicionar `heuristica: Optional[str] = None` em `MotorStatusResponse`. |
| **Hashing & Dependências** | `backend/app/core/security.py:4,14-28`, `backend/requirements.txt:15-16` | `verify_password` checa `len(raw_bytes) <= 72`, mas `get_password_hash` (`:25-28`) chama `bcrypt.hashpw` sem guarda de 72 bytes. `passlib[bcrypt]` (`requirements.txt:16`) está morto/não importado. `pyotp` ausente. | `bcrypt>=4.x` lança `ValueError` em senhas > 72 bytes UTF-8 (HTTP 500 no cadastro); dependência morta `passlib` aumenta superfície de ataque. | Validar `len(password.encode("utf-8")) <= 72` em `get_password_hash` (`ValueError` tratado com `422`), remover `passlib[bcrypt]` e adicionar `pyotp>=2.9.0` e `cryptography>=42.0.0`. |
| **Política & Ciclo de Senha** | `backend/app/schemas/usuario.py:16-17` (`UsuarioCreate`), `auth.py:16-80`, `usuarios.py:67-211`, `models/usuario.py:16-30` | `UsuarioCreate.senha` exige apenas `min_length=6`, sem `max_length=72`, sem limite de bytes UTF-8 e sem política mínima de composição. Inexistem `/auth/alterar-senha`, `/auth/logout` e `/usuarios/{id}/redefinir-senha`. | Senhas fracas aceitas, crash em > 72 bytes, ausência de troca obrigatória e impossibilidade de revogar JWTs emitidos. | Exigir `min_length=8`, `max_length=72`, <= 72 bytes UTF-8 e composição mínima (letras + dígitos, mínimo 3 classes ou regra explícita compatibilizada com `test_api_logs.py:468`), adicionar `token_version` e `deve_trocar_senha` em `Usuario` e implementar os 3 endpoints. |
| **Segredos e Config** | `backend/app/config.py:8-29`, `.env.example:8-16` | Defaults inseguros hardcoded (`SECRET_KEY = "super-secret-key-change-in-production-min-32-chars"`, `POSTGRES_PASSWORD = "changeme_local_only"`). Sem `ENVIRONMENT`, `JWT_ISSUER`, `JWT_AUDIENCE`, `MFA_ENCRYPTION_KEY`. | **OWASP API2:** risco de deploy em `staging`/`production` com chave JWT pública/padrão. | Introduzir `ENVIRONMENT` (`development|test|staging|production`), `JWT_ISSUER`, `JWT_AUDIENCE`, `MFA_ENCRYPTION_KEY` e validação `model_validator` fail-fast na inicialização em `staging`/`production`. |
| **Claims JWT & Revogação** | `backend/app/core/security.py:31-46`, `backend/app/api/deps.py:14-50` | `create_access_token` injeta apenas `exp` (`:37`); `get_current_user` não valida `iss`, `aud`, `jti`, `scope` nem `token_version`. | **OWASP API2:** um `challenge_token` temporário de MFA assinado com a mesma `SECRET_KEY` seria aceito em rotas comuns se `scope` não for validado. | Emitir e exigir `iss`, `aud`, `jti`, `iat`, `scope="access"` e `ver == user.token_version` em `get_current_user`. |
| **Auth Guard & `setRole` no Angular** | `auth.guard.ts:5-14`, `auth.service.ts:43-58,86-88,121-128`, `login.component.ts:87-92` | `isAuthenticated()` checa apenas `Boolean(token && role)` sem decodificar `exp` ou `scope`. `AuthService.setRole()` (`:121-128`) cria token sintético `session_${role}_token` em produção. `LoginComponent` não usa `getHomeRoute()`. | Sessões expiradas permanecem autenticadas na SPA e backdoor `setRole()` existe em código de produção (usado 32 vezes em 6 `.spec.ts`). | Remover `setRole()` de `AuthService`, validar payload JWT (`exp > now`, `scope === 'access'`) no guard/serviço e migrar testes para helper JWT válido. |
| **MFA (TOTP + Códigos)** | Todo `backend/` e `frontend/` | Zero implementação de `pyotp`, TOTP RFC 6238, códigos de recuperação, cifra em repouso ou UI de 2FA. | Contas privilegiadas (`admin`, `coordenador`, `secretaria`) protegidas apenas por fator único (senha). | Implementar MFA TOTP RFC 6238 completo, cifra Fernet, proteção anti-replay `ultimo_totp_step`, 8 códigos de recuperação com hash, login 2FA e rota `/seguranca`. |
| **Paridade RBAC & Campus** | `auth.service.ts:90-93`, `admin.component.ts:99,182,422-476`, `app.routes.ts:34-63`, `shell.component.ts:42,146-148`, `salas.py:214-252`, `horarios.py:43-45`, `dashboard.component.ts:48-52` | `hasRole('admin')` retorna `true` para `coordenador` (gerando 403 em `excluirSala` e `Benchmark`); `/secretaria` oculta de `admin`/`coordenador`; `/historico` oculta de `secretaria`; `/` redireciona para `/admin`; `excluir_sala` omite `require_campus_access`; `AdminComponent` trava `campusId`; `DashboardComponent` fixa campi `#1,#2,#3`; `/horarios/meus` ignora escopo global de `admin`. | Quebra de paridade Front/Back (erros 403 inesperados, bloqueios indevidos de menu, banner falso de acesso negado no root redirect e falha BOLA em `DELETE /salas/{id}`). | Corrigir `hasRole` estrito, separar `isAdminGlobal` de `podeGerenciar`, abrir `/secretaria` e `/historico` conforme backend, criar `homeRedirectGuard`, aplicar `require_campus_access` em `excluir_sala`, adicionar `campus_id` opcional em `/horarios/meus` e carregar `/api/v1/campi` dinamicamente. |

### 1.2 Decisões Arquiteturais Fundamentais

1. **Remoção de `passlib` e uso direto de `bcrypt`:** `passlib[bcrypt]` encontra-se sem manutenção ativa e incompatível com versões recentes de `bcrypt>=4.1`. Como `security.py` já utiliza `bcrypt` diretamente (`checkpw` / `hashpw`), a dependência morta `passlib[bcrypt]` é removida de `requirements.txt`, mantendo apenas `bcrypt>=4.1.2` e adicionando `pyotp>=2.9.0` e `cryptography>=42.0.0`.
2. **Separação estrita de escopos JWT (`scope`):** Tokens de desafio MFA (`mfa_challenge` e `mfa_setup`) jamais podem autenticar endpoints de negócio. `get_current_user` exige obrigatoriamente `scope == "access"`. Tokens `mfa_challenge`/`mfa_setup` são aceitos exclusivamente pelas dependências dedicadas de `/auth/mfa/setup` e `/auth/mfa/verify`.
3. **Revogação imediata sem tabela de blocklist com estado (`token_version`):** Cada `Usuario` possui `token_version` (iniciado em `1`). Operações de `/auth/logout`, `/auth/alterar-senha`, `/usuarios/{id}/redefinir-senha` e `/usuarios/{id}/mfa/reset` incrementam `token_version += 1` atomicamente no banco, invalidando instantaneamente todos os JWTs anteriores sem depender de Redis externo.
4. **Criptografia de segredo TOTP e hashing de códigos de recuperação:** O segredo base32 TOTP é cifrado em repouso com `Fernet(MFA_ENCRYPTION_KEY)` antes da persistência em `usuario.mfa_segredo_cifrado`. Em `staging`/`production`, `MFA_ENCRYPTION_KEY` deve ser uma chave Fernet independente e obrigatória no startup; em `development`/`test`, se omitida, deriva-se deterministicamente via HKDF-SHA256 sobre `SECRET_KEY`. Os 8 códigos de recuperação (`XXXX-XXXX`) são armazenados apenas como hash HMAC-SHA256 com `SECRET_KEY` (comparação em tempo constante via `hmac.compare_digest`), permitindo validação O(1) sem 8 verificações lentas de bcrypt por tentativa.
5. **Compatibilidade controlada de testes existentes:** A regra mínima de senha (`min_length=8`, `<= 72` bytes UTF-8, pelo menos 1 letra e 1 dígito — e validação opcional ou de 3 classes conforme especificado na Seção 3.2) e a obrigatoriedade de MFA para `admin`/`coordenador`/`secretaria` (`MFA_MANDATORY_FOR_PRIVILEGED=True` por padrão, configurável via `Settings` apenas se necessário para migração controlada de ambiente) exigem atualização explícita e documentada em lockstep nos testes listados na Seção 5.1. No caso de `test_api_logs.py:468` (`"senha_segura_123"`), se a política exigir letra maiúscula, o fixture será atualizado para `"SenhaSegura123"`.

---

## 2. Matriz RBAC, Histórias de Usuário e Critérios de Aceite (Gherkin)

### 2.1 Matriz RBAC Completa (Endpoints Endurecidos + Novos Endpoints)

| Recurso / Rota | Método | Admin | Coordenador | Secretaria | Professor | Aluno | Escopo / Regra de Segurança |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `/api/v1/auth/login` | POST | Público | Público | Público | Público | Público | Tempo constante; retorna `access_token` ou `challenge_token` (`mfa_required` / `mfa_setup_required`). |
| `/api/v1/auth/me` | GET | Sim | Sim | Sim | Sim | Sim | Exige JWT `scope="access"` e `ver == token_version`. |
| `/api/v1/auth/logout` | POST | Sim | Sim | Sim | Sim | Sim | Incrementa `token_version += 1` e registra `LogAlocacao`. |
| `/api/v1/auth/alterar-senha` | POST | Sim | Sim | Sim | Sim | Sim | Valida `senha_atual`, nova política <= 72B, limpa `deve_trocar_senha` e incrementa `token_version`. |
| `/api/v1/auth/mfa/setup` | POST | Sim* | Sim* | Sim* | Sim* | Sim* | *Aceita `scope="access"` OU `scope="mfa_setup"`. Gera segredo TOTP cifrado e `otpauth_uri`. |
| `/api/v1/auth/mfa/verify` | POST | Sim* | Sim* | Sim* | Sim* | Sim* | *Aceita `scope="mfa_challenge"` ou `mfa_setup`. Valida TOTP (`valid_window=1`, anti-replay) ou código de recuperação e emite `access_token`. |
| `/api/v1/auth/mfa/disable` | POST | Não (403) | Não (403) | Não (403) | Sim | Sim | Obrigatório para perfis privilegiados; `professor`/`aluno` desabilitam com `senha_atual` + `codigo_totp`. |
| `/api/v1/auth/mfa/recovery-codes/regenerate` | POST | Sim | Sim | Sim | Sim | Sim | Exige `scope="access"`, `mfa_habilitado=True`, `senha_atual` + `codigo_totp`; invalida códigos anteriores. |
| `/api/v1/usuarios/{id}/redefinir-senha` | POST | Sim | Sim (Campus)* | Sim (Campus)* | Não | Não | *Segue hierarquia de `atualizar_usuario`; define `deve_trocar_senha=True` e incrementa `token_version`. |
| `/api/v1/usuarios/{id}/mfa/reset` | POST | Sim | Não (403) | Não (403) | Não | Não | Exclusivo `ADMIN` para recuperação de conta bloqueada; incrementa `token_version`. |
| `/api/v1/campi` | GET | Sim | Sim (Próprio) | Sim (Próprio) | Sim (Próprio) | Sim (Próprio) | `ADMIN` lista todos; demais perfis recebem apenas `Campus.id == current_user.campus_id`. |
| `/api/v1/campi` | POST | Sim | Não (403) | Não (403) | Não (403) | Não (403) | Exclusivo `ADMIN`; grava `LogAlocacao` (`CRIACAO`). |
| `/api/v1/campi/{campus_id}` | GET | Sim | Sim (Próprio) | Sim (Próprio) | Sim (Próprio) | Sim (Próprio) | `require_campus_access` retorna `404` para outro campus. |
| `/api/v1/equipamentos` | GET | Sim | Sim | Sim | Sim | Sim | Exige `get_current_user` (`401` se anônimo). |
| `/api/v1/motor/status` | GET | Sim | Sim | Não (403) | Não (403) | Não (403) | Exige `ADMIN` ou `COORDENADOR`; inclui campo `heuristica`. |
| `/api/v1/motor/teste-integracao` | POST | Sim | Sim | Não (403) | Não (403) | Não (403) | Exige `ADMIN` ou `COORDENADOR`. |
| `/api/v1/salas/{sala_id}` | DELETE | Sim | Não (403) | Não (403) | Não (403) | Não (403) | `ADMIN` apenas + `require_campus_access` explícito. |
| `/api/v1/horarios/meus` | GET | Sim | Sim | Sim | Sim | Sim | Aceita `campus_id` opcional para `ADMIN` global; demais perfis filtrados pelo próprio campus/vínculo. |
| `/api/v1/logs` (Tela `/historico`) | GET | Sim | Sim (Campus) | Sim (Campus) | Não (403) | Não (403) | Paridade Front/Back: liberar `/historico` na SPA para `secretaria`. |
| Rota SPA `/secretaria` | UI | Sim | Sim | Sim | Não | Não | Paridade Front/Back: liberar `/secretaria` na SPA para `admin` e `coordenador`. |

### 2.2 Histórias de Usuário e Critérios de Aceite

#### História 1: Fechamento de Endpoints Expostos e Segredos Fail-Fast
> **Como** Administrador de Segurança do SIGAAS  
> **Quero** que os endpoints `/campi`, `/equipamentos` e `/motor/*` exijam autenticação e autorização adequadas e que a aplicação recuse iniciar em `staging`/`production` com chaves padrão inseguras  
> **Para que** nenhuma unidade acadêmica ou rotina nativa em C fique exposta a atacantes anônimos ou assinaturas previsíveis.

```gherkin
Cenário: Bloqueio de acesso anônimo em campi, equipamentos e motor C
  Dado que um cliente não possui token JWT válido no cabeçalho Authorization
  Quando enviar requisições para GET /api/v1/campi, POST /api/v1/campi, GET /api/v1/equipamentos, GET /api/v1/motor/status ou POST /api/v1/motor/teste-integracao
  Então a API deve responder com status 401 Unauthorized em todas as rotas

Cenário: Coordenador consulta campi e status do motor sem privilégio de criação de campus
  Dado que um usuário com perfil "coordenador" do Campus 1 está autenticado
  Quando enviar GET /api/v1/campi e GET /api/v1/motor/status
  Então GET /api/v1/campi deve retornar status 200 OK contendo apenas o Campus 1
  E GET /api/v1/motor/status deve retornar status 200 OK incluindo o campo "heuristica"
  E quando esse coordenador enviar POST /api/v1/campi, a API deve responder com status 403 Forbidden

Cenário: Falha imediata no startup em produção com SECRET_KEY padrão
  Dado que a variável ENVIRONMENT está configurada como "production"
  E SECRET_KEY mantém o valor padrão de desenvolvimento ou possui menos de 32 caracteres ou MFA_ENCRYPTION_KEY está ausente
  Quando o processo FastAPI carregar Settings
  Então a inicialização deve falhar imediatamente lançando ValueError explícito antes de aceitar tráfego
```

#### História 2: Política de Senhas (Limite 72 Bytes UTF-8), Troca e Revogação de Sessão
> **Como** usuário autenticado ou gestor de contas  
> **Quero** que senhas acima de 72 bytes sejam validadas sem erro interno, que existam fluxos seguros de alteração, logout e redefinição administrativa, e que JWTs antigos sejam invalidados  
> **Para que** tokens comprometidos ou credenciais redefinidas percam validade imediatamente.

```gherkin
Cenário: Rejeição controlada de senha com mais de 72 bytes UTF-8
  Dado que um administrador envia POST /api/v1/usuarios com senha contendo 73 bytes UTF-8 (incluindo caracteres acentuados)
  Quando o schema UsuarioCreate e o serviço de segurança validarem a entrada
  Então a API deve responder com status 422 Unprocessable Entity informando o limite máximo de 72 bytes em UTF-8
  E não deve ocorrer erro 500 por ValueError interno do bcrypt

Cenário: Logout e alteração de senha invalidam tokens JWT emitidos anteriormente
  Dado que um usuário está autenticado com um token JWT válido contendo ver = 1
  Quando o usuário enviar POST /api/v1/auth/logout (ou POST /api/v1/auth/alterar-senha com senha atual válida)
  Então a API deve incrementar token_version para 2 no banco e retornar status 200 OK
  E qualquer requisição subsequente utilizando o token antigo (ver = 1) em GET /api/v1/auth/me deve falhar com status 401 Unauthorized

Cenário: Redefinição administrativa força troca de senha
  Dado que o Admin solicita POST /api/v1/usuarios/{id}/redefinir-senha com nova senha temporária válida
  Quando o usuário afetado autenticar com a senha temporária
  Então a resposta deve sinalizar deve_trocar_senha = true
  E o token emitido anteriormente deve estar revogado
```

#### História 3: Autenticação Multifator (MFA TOTP RFC 6238 e Códigos de Recuperação)
> **Como** usuário com perfil privilegiado ou docente/discente optante  
> **Quero** configurar e validar um segundo fator TOTP via aplicativo autenticador e possuir códigos de recuperação de uso único  
> **Para que** o comprometimento isolado da minha senha não permita acesso à conta nem às operações acadêmicas.

```gherkin
Cenário: Onboarding obrigatório de MFA no primeiro login de Admin, Coordenador ou Secretaria
  Dado que um usuário com perfil "admin", "coordenador" ou "secretaria" possui mfa_habilitado = false
  Quando enviar POST /api/v1/auth/login com email e senha válidos
  Então a API deve responder com status 200 OK contendo mfa_required = true, mfa_setup_required = true e challenge_token com scope "mfa_setup"
  E o campo access_token deve ser nulo e o campo usuario deve ser nulo
  E usar esse challenge_token em GET /api/v1/salas deve retornar status 401 Unauthorized

Cenário: Ativação de MFA e geração única de 8 códigos de recuperação
  Dado que o usuário possui challenge_token com scope "mfa_setup"
  Quando chamar POST /api/v1/auth/mfa/setup e em seguida enviar POST /api/v1/auth/mfa/verify com código TOTP válido gerado a partir do segredo
  Então a API deve ativar mfa_habilitado = true, gravar ultimo_totp_step e retornar status 200 OK com access_token definitivo e exatamente 8 códigos no formato XXXX-XXXX
  E o segredo TOTP armazenado na tabela usuario.mfa_segredo_cifrado deve estar cifrado com Fernet (diferente do segredo base32 plano)

Cenário: Bloqueio de replay TOTP dentro da mesma janela de 30 segundos
  Dado que um usuário com mfa_habilitado = true acabou de concluir login usando o código TOTP do step T
  Quando um atacante tentar reutilizar exatamente o mesmo código TOTP no mesmo intervalo de 30 segundos (step T)
  Então a API deve recusar o desafio com status 401 Unauthorized

Cenário: Uso de código de recuperação único e proibição de desativação para perfil privilegiado
  Dado que um usuário com perfil "secretaria" está autenticado com MFA ativo
  Quando tentar enviar POST /api/v1/auth/mfa/disable
  Então a API deve responder com status 403 Forbidden informando obrigatoriedade de MFA para o perfil
  E quando um usuário usar um dos 8 códigos de recuperação válidos em POST /api/v1/auth/mfa/verify
  Então o acesso deve ser concedido com status 200 OK e o código utilizado deve ser marcado com usado_em, não podendo ser reutilizado
```

#### História 4: Paridade RBAC Front/Back, Validação de `exp` e Escopo Multi-Campus na SPA
> **Como** usuário da interface Angular do SIGAAS  
> **Quero** que os menus, rotas, redirecionamento inicial e seletores de campus reflitam fielmente as permissões do backend e que tokens expirados ou inválidos sejam rejeitados na navegação  
> **Para que** não ocorram cliques em botões que falham com 403 nem acessos espúrios via stubs locais.

```gherkin
Cenário: Coordenador não visualiza ações exclusivas de Admin e acessa Secretaria
  Dado que um usuário com perfil "coordenador" está autenticado com JWT válido na SPA
  Quando navegar pela aplicação
  Então AuthService.hasRole('admin') deve retornar false
  E os botões "Excluir" sala e "Benchmark Científico" não devem ser renderizados no AdminComponent
  E o link e a rota /secretaria devem estar acessíveis para "admin" e "coordenador"
  E o link e a rota /historico devem estar acessíveis para "secretaria"

Cenário: Guard rejeita token expirado e rota raiz redireciona sem banner falso
  Dado que o token armazenado no localStorage possui claim exp no passado ou scope diferente de "access"
  Quando o usuário tentar acessar /admin protegido pelo authGuard
  Então authGuard deve limpar a sessão via logout() e redirecionar para /login
  E quando um usuário autenticado com perfil "secretaria" acessar a rota "/"
  Então homeRedirectGuard deve redirecionar diretamente para "/secretaria" sem exibir mensagem de acesso restrito

Cenário: Admin global alterna campus dinamicamente no AdminComponent e /horarios/meus
  Dado que um usuário "admin" está autenticado e o backend retorna 2 campi em GET /api/v1/campi
  Quando selecionar o Campus 2 no seletor dinâmico do AdminComponent
  Então as consultas de salas, usuários, alocação e GET /api/v1/horarios/meus?campus_id=2 devem refletir os dados do Campus 2
```

---

## 3. Arquitetura e Contratos Técnicos

### 3.1 Endpoints FastAPI e Contratos Pydantic v2

Todos os schemas utilizam Pydantic v2 com `model_config = ConfigDict(extra="forbid")` em payloads de entrada e `ConfigDict(from_attributes=True)` em leituras ORM.

1. **`backend/app/schemas/motor.py` / `motor.py:21-25` (`MotorStatusResponse`):**
   - Adicionar `heuristica: Optional[str] = Field(default=None, description="Algoritmo heuristico ativo no motor C")` mantendo retrocompatibilidade.
2. **`backend/app/schemas/usuario.py`:**
   - Criar validador compartilhado `validar_politica_senha(v: str) -> str`:
     - `len(v) >= 8` e `len(v.encode("utf-8")) <= 72` (`ValueError` explicito caso exceda 72 bytes UTF-8).
     - Exigir ao menos 1 letra minúscula, 1 letra maiúscula e 1 dígito numérico (`re.search(r"[a-z]", v)`, `re.search(r"[A-Z]", v)`, `re.search(r"\d", v)`), além de rejeitar espaços em branco nas extremidades ou sequências totalmente triviais. *(Nota de compatibilidade: atualizar o fixture `"senha_segura_123"` em `backend/tests/test_api_logs.py:468` para `"SenhaSegura123"`).*
   - Em `UsuarioCreate`: `senha: str = Field(..., min_length=8, max_length=72, description="Senha de acesso (maximo 72 bytes UTF-8)")`.
   - Novos schemas:
     - `RedefinirSenhaAdminRequest`: `{ nova_senha_temporaria: str }` (mesmo validador `validar_politica_senha`).
     - `UsuarioSenhaResetResponse`: `{ usuario_id: int, deve_trocar_senha: bool, mensagem: str }`.
     - `UsuarioMfaResetResponse`: `{ usuario_id: int, mfa_habilitado: bool, mensagem: str }`.
     - Em `UsuarioRead`: incluir `mfa_habilitado: bool` e `deve_trocar_senha: bool` (sem expor `mfa_segredo_cifrado` nem `token_version`).
3. **`backend/app/schemas/auth.py`:**
   - `TokenResponse`:
     ```python
     class TokenResponse(BaseModel):
         access_token: Optional[str] = None
         token_type: str = "bearer"
         mfa_required: bool = False
         mfa_setup_required: bool = False
         challenge_token: Optional[str] = None
         deve_trocar_senha: bool = False
         usuario: Optional[UsuarioSummary] = None
     ```
     *(Quando `mfa_required=True`, `access_token` e `usuario` são `None` para evitar vazamento de PII antes da validação do segundo fator; quando `mfa_required=False`, `access_token` e `usuario` são preenchidos mantendo compatibilidade com fluxos diretos de `professor`/`aluno`.)*
   - `AlterarSenhaRequest`: `{ senha_atual: str = Field(..., min_length=1, max_length=72), nova_senha: str }` (validado por `validar_politica_senha` e distinto de `senha_atual`).
   - `MfaSetupResponse`: `{ segredo_manual: str, otpauth_uri: str, issuer: str }`.
   - `MfaVerifyRequest`: `{ codigo: str = Field(..., min_length=6, max_length=16, description="Codigo TOTP de 6 digitos ou codigo de recuperacao XXXX-XXXX") }`.
   - `MfaVerifyResponse(TokenResponse)`: herda `access_token`, `token_type`, `deve_trocar_senha`, `usuario` e acrescenta `codigos_recuperacao: Optional[list[str]] = None` (preenchido **uma única vez** na ativação inicial).
   - `MfaActionConfirmRequest`: `{ senha_atual: str = Field(..., min_length=1, max_length=72), codigo_totp: str = Field(..., min_length=6, max_length=8) }`.
   - `MfaRecoveryRegenerateResponse`: `{ codigos_recuperacao: list[str] }`.
4. **Endpoints em `auth.py`, `usuarios.py`, `campi.py`, `equipamentos.py`, `motor.py`, `salas.py`, `horarios.py`:**
   - `POST /api/v1/auth/login`: mantém verificação constante (`DUMMY_HASH`), consulta política por perfil (`ADMIN`, `COORDENADOR`, `SECRETARIA` exigem MFA se `settings.MFA_MANDATORY_FOR_PRIVILEGED` estiver ativo).
   - `POST /api/v1/auth/alterar-senha`: exige `get_current_user`, verifica `senha_atual`, aplica `get_password_hash(nova_senha)`, define `deve_trocar_senha=False`, incrementa `token_version += 1`, grava `LogAlocacao` (`ALTERACAO`, sem jamais logar senhas), emite novo `access_token`.
   - `POST /api/v1/auth/logout`: exige `get_current_user`, incrementa `token_version += 1`, grava `LogAlocacao` (`ALTERACAO`, `detalhes="Logout realizado com revogacao de sessao"`), retorna `{ "detail": "Sessao encerrada com sucesso" }`.
   - `POST /api/v1/auth/mfa/setup`: dependência `get_mfa_setup_or_access_user` (`scope in {"access", "mfa_setup"}`), gera `pyotp.random_base32()`, cifra com Fernet e persiste em `mfa_segredo_cifrado` mantendo `mfa_habilitado=False` até confirmação em `/verify`.
   - `POST /api/v1/auth/mfa/verify`: dependência `get_mfa_challenge_user` (`scope in {"mfa_challenge", "mfa_setup"}`), valida TOTP (`valid_window=1`) com checagem `current_step > (user.ultimo_totp_step or -1)` OU valida código de recuperação ainda não usado (`usado_em IS NULL`). Na primeira ativação, marca `mfa_habilitado=True`, `mfa_verificado_em=now()`, gera 8 códigos `XXXX-XXXX` e retorna `access_token` (`scope="access"`).
   - `POST /api/v1/auth/mfa/disable`: exige `get_current_user`; bloqueia `ADMIN`/`COORDENADOR`/`SECRETARIA` com `403` quando `MFA_MANDATORY_FOR_PRIVILEGED=True`; para `PROFESSOR`/`ALUNO`, valida `senha_atual` + `codigo_totp`, limpa `mfa_segredo_cifrado`, `mfa_habilitado=False`, `mfa_verificado_em=None`, remove registros de `mfa_codigo_recuperacao` e registra `LogAlocacao`.
   - `POST /api/v1/auth/mfa/recovery-codes/regenerate`: exige `get_current_user` + `mfa_habilitado=True` + `senha_atual` + `codigo_totp`; apaga códigos antigos e gera 8 novos códigos.
   - `POST /api/v1/usuarios/{usuario_id}/redefinir-senha` e `POST /api/v1/usuarios/{usuario_id}/mfa/reset`: aplicam regras estritas de hierarquia e `require_campus_access`, incrementam `token_version += 1` e gravam `LogAlocacao`.
   - `DELETE /api/v1/salas/{sala_id}` (`salas.py:214-252`): adicionar `require_campus_access(sala.campus_id, current_user)` antes da remoção.
   - `GET /api/v1/horarios/meus` (`horarios.py:18-48`): adicionar parâmetro `campus_id: Optional[int] = Query(default=None, gt=0)`. Para `ADMIN`, filtrar por `campus_id` somente quando fornecido; para demais perfis, manter vínculo do próprio usuário/campus.

### 3.2 Segurança Criptográfica, JWT e Cifra MFA (`config.py`, `security.py`, `mfa_service.py`)

- **Configuração (`backend/app/config.py`):**
  - `ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"`
  - `JWT_ISSUER: str = "sigaas-api"`
  - `JWT_AUDIENCE: str = "sigaas-spa"`
  - `ACCESS_TOKEN_EXPIRE_MINUTES: int = 30` (<= 60 min conforme `owasp-api-security`)
  - `MFA_CHALLENGE_EXPIRE_MINUTES: int = 5`
  - `MFA_SETUP_EXPIRE_MINUTES: int = 10`
  - `MFA_ENCRYPTION_KEY: Optional[str] = None`
  - `MFA_MANDATORY_FOR_PRIVILEGED: bool = True`
  - `@model_validator(mode="after")` rejeita `SECRET_KEY` padrão ou `< 32` chars, `POSTGRES_PASSWORD == "changeme_local_only"` e `MFA_ENCRYPTION_KEY` ausente/inválida sempre que `ENVIRONMENT in {"staging", "production"}`.
- **Estrutura dos Claims JWT (`security.py`):**
  - Payload obrigatório: `sub` (string do `user.id`), `perfil`, `campus_id`, `iss` (`settings.JWT_ISSUER`), `aud` (`settings.JWT_AUDIENCE`), `jti` (`uuid4().hex`), `iat` (UTC timestamp), `exp` (UTC timestamp), `scope` (`"access"`, `"mfa_challenge"` ou `"mfa_setup"`), `ver` (`user.token_version`, presente em `scope="access"`).
  - `decode_token(token, expected_scopes)`: verifica assinatura `HS256`, `exp`, `issuer=settings.JWT_ISSUER`, `audience=settings.JWT_AUDIENCE` e exige `payload.get("scope") in expected_scopes`.
  - `get_password_hash(password: str)`: valida `len(password.encode("utf-8")) <= 72` antes de invocar `bcrypt.hashpw(...)`.

### 3.3 Modelo de Dados PostgreSQL e Migration Alembic (`004_seguranca_auth_mfa`)

- **Cadeia Alembic:** `revision = "004_seguranca_auth_mfa"`, `down_revision = "003_release_candidate_indexes"`.
- **Compatibilidade SQLite (`env.py:55`) e PostgreSQL (`postgres-alembic-ops`):** Toda alteração em `usuario` deve usar `with op.batch_alter_table("usuario") as batch_op:` e colunas não-nulas devem declarar `server_default=sa.text(...)` para evitar bloqueio de tabela em produção.
- **Alterações na tabela `usuario` (`backend/app/models/usuario.py`):**
  - `token_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa.text("1"), default=1)`
  - `deve_trocar_senha: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.text("false"), default=False)`
  - `mfa_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.text("false"), default=False)`
  - `mfa_segredo_cifrado: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)`
  - `mfa_verificado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)`
  - `ultimo_totp_step: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)`
- **Nova tabela `mfa_codigo_recuperacao` (`backend/app/models/usuario.py`):**
  - `id`: `Integer` PK autoincrement
  - `usuario_id`: `Integer`, `ForeignKey("usuario.id", ondelete="CASCADE")`, `nullable=False` (índice `ix_mfa_codigo_recuperacao_usuario_id`)
  - `codigo_hash`: `String(255)`, `nullable=False` (HMAC-SHA256 hex digest do código normalizado `XXXX-XXXX`)
  - `usado_em`: `DateTime(timezone=True)`, `nullable=True`
  - `created_at`: `DateTime(timezone=True)`, `server_default=func.now()`, `nullable=False`
- **Reversibilidade (`downgrade()`):**
  - Remover índice `ix_mfa_codigo_recuperacao_usuario_id` e tabela `mfa_codigo_recuperacao`.
  - Remover as 6 colunas adicionadas em `usuario` dentro de `with op.batch_alter_table("usuario") as batch_op:`.
  - Testar ciclo completo: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`.

### 3.4 Contratos `openapi-typescript` e Arquitetura Frontend Angular 20

- **Contrato OpenAPI (`contract-testing`):** Após PR 3, regenerar `frontend/src/app/core/models/api-contracts.ts` via `npx openapi-typescript openapi.json -o frontend/src/app/core/models/api-contracts.ts`. Proibido o uso de `HttpClient.get<any>()` / `post<any>()`.
- **`AuthService` (`frontend/src/app/services/auth.service.ts`):**
  - **Remover completamente `setRole()`** (`:121-128`).
  - Implementar decodificação segura do payload JWT (`decodeJwtPayload(token)`): validar presença de 3 segmentos base64url, `exp` numérico > `Date.now() / 1000` e `scope === 'access'`. Se inválido ou expirado em `restoreSession()` ou `isAuthenticated()`, chamar `logout()` e retornar `false`.
  - Corrigir `hasRole(role: string)` para comparação estrita (`return this._currentRole() === role`), eliminando o alias `role === 'admin' && curr === 'coordenador'`. Criar helper `hasAnyRole(roles: readonly UserRole[])`.
  - Adicionar `challengeToken` em memória (nunca persistir `challenge_token` no `localStorage`), `mfaSetupRequired` e métodos tipados: `verifyMfa(codigo, challengeToken)`, `setupMfa(challengeToken?)`, `disableMfa(payload)`, `regenerateRecoveryCodes(payload)`, `changePassword(payload)` e `logoutServer()`.
- **Roteamento, Guards e Shell (`app.routes.ts`, `auth.guard.ts`, `role.guard.ts`, `shell.component.ts`):**
  - Substituir `{ path: '', redirectTo: 'admin', pathMatch: 'full' }` por rota com `canActivate: [homeRedirectGuard]` que direciona para `authService.getHomeRoute()` (ou `/login` se não autenticado), evitando banner falso de acesso negado.
  - Atualizar rota `/secretaria`: `data: { roles: ['admin', 'coordenador', 'secretaria'] }`.
  - Atualizar rota `/historico`: `data: { roles: ['admin', 'coordenador', 'secretaria'] }`.
  - Adicionar rota `/seguranca` (`SegurancaComponent`, protegida por `authGuard`, acessível a todos os perfis autenticados).
  - Atualizar `ShellComponent` para refletir exatamente os mesmos perfis nas abas de navegação e exibir atalho para `/seguranca` com ícones `lucide-angular` (zero emojis).
- **Componentes de Negócio (`AdminComponent`, `SecretariaComponent`, `DashboardComponent`, `LoginComponent`):**
  - `AdminComponent`: separar `isAdminGlobal` (`perfil === 'admin'`) de `podeGerenciarOperacao` (`admin` ou `coordenador`), ocultando `Excluir Sala` e `Benchmark Científico` para `coordenador`; carregar lista dinâmica de campi via `GET /api/v1/campi` para `admin` selecionar `campus_id` ativo (inclusive em `GET /api/v1/horarios/meus?campus_id=...`).
  - `DashboardComponent`: substituir IDs fixos `#1`, `#2`, `#3` por listagem dinâmica de `GET /api/v1/campi`.
  - `LoginComponent`: implementar máquina de estados em 3 passos (Credenciais -> Setup TOTP + exibição única dos 8 códigos de recuperação com cópia/download `.txt` -> Desafio TOTP de 6 dígitos ou código de recuperação), além de redirecionar automaticamente via `getHomeRoute()` se o usuário já possuir sessão válida.

---

## 4. Fatiamento em PRs Incrementais (Limite `<= 300-400` LOC)

Em conformidade com `AGENTS.md` §6.4, `diff-slicer` e `scripts/check_pr_size.py` (que contabiliza adições em `.py`, `.ts`, `.html`, `.scss` não-global, isentando `alembic/versions/`, `backend/tests/*.py`, `*.spec.ts` e `docs/`), toda a entrega é fatiada em **5 PRs independentes e testáveis**:

| PR | Branch | Escopo Técnico | Arquivos de Produção Alvo | LOC Prod. Est. | Conventional Commit | Dependência | Gate 2 |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **PR 1** | `fix/security-endpoints-password-jwt` | Auth em `campi`, `equipamentos`, `motor`; `MotorStatusResponse.heuristica`; fail-fast em `config.py`; guarda 72B e claims `iss`/`aud`/`jti`/`scope` em `security.py` + `deps.py`; política de senha em `schemas/usuario.py`; remover `passlib`. | `config.py`, `.env.example`, `requirements.txt`, `security.py`, `deps.py`, `schemas/usuario.py`, `schemas/motor.py`, `campi.py`, `equipamentos.py`, `motor.py` | ~180 | `fix(security): proteger endpoints expostos, validar segredos e claims jwt` | - | Sim (revisão PR) |
| **PR 2** | `feat/auth-password-lifecycle-and-schema` | Migration `004_seguranca_auth_mfa`; `token_version` e `deve_trocar_senha` em `Usuario`; checagem de `ver` em `deps.py`; `/auth/alterar-senha`, `/auth/logout` e `/usuarios/{id}/redefinir-senha`. | `models/usuario.py`, `models/__init__.py`, `schemas/auth.py`, `schemas/usuario.py`, `deps.py`, `endpoints/auth.py`, `endpoints/usuarios.py` (`004_*.py` isento) | ~210 | `feat(auth): adicionar ciclo de senha, logout e revogacao via token_version` | PR 1 | **Sim (Migration PG)** |
| **PR 3** | `feat/mfa-totp-pyotp-recovery` | `pyotp` + `cryptography`, `mfa_service.py` (Fernet + HMAC códigos recuperação + replay guard), login 2FA com política obrigatória por perfil, `/auth/mfa/*` e `/usuarios/{id}/mfa/reset`. | `requirements.txt`, `core/security.py`, `services/mfa_service.py`, `schemas/auth.py`, `api/deps.py`, `endpoints/auth.py`, `endpoints/usuarios.py` | ~290 | `feat(security): implementar mfa totp rfc 6238 e codigos de recuperacao` | PR 2 | Sim (revisão PR) |
| **PR 4** | `fix/rbac-campus-parity-frontend-backend` | `require_campus_access` em `excluir_sala`; `campus_id` opcional em `/horarios/meus`; remoção de `setRole()`, checagem de `exp`/`scope`, `hasRole` estrito, `/secretaria`, `/historico`, `homeRedirectGuard`, seletor de campus dinâmico. | `salas.py`, `horarios.py`, `auth.service.ts`, `auth.guard.ts`, `role.guard.ts`, `app.routes.ts`, `shell.component.ts`, `admin.component.ts`, `secretaria.component.ts`, `dashboard.component.ts`, `login.component.ts` | ~240 | `fix(rbac): alinhar permissoes multi-campus e remover stub setRole` | PR 1 | Sim (revisão PR) |
| **PR 5** | `feat/frontend-mfa-and-password-ux` | Contratos `api-contracts.ts`, fluxo 2FA e onboarding no `LoginComponent`, página `/seguranca` (QR/URI TOTP, 8 códigos de recuperação, desativação para perfis opcionais, troca de senha) e `AuthService` MFA. | `core/models/api-contracts.ts`, `auth.service.ts`, `app.routes.ts`, `shell.component.ts`, `login.component.ts`, `pages/seguranca/seguranca.component.ts` | ~300 | `feat(frontend): adicionar fluxo mfa 2fa e pagina de seguranca da conta` | PR 3, PR 4 | Sim (revisão PR) |

---

## 5. Plano de Testes TDD (RED / GREEN / REFACTOR)

Esta seção utiliza exclusivamente listas numeradas e marcadores simples (sem caixas de seleção Markdown) para manter compatibilidade estrita com o parser de subtasks do `scripts/clickup_sync.py`.

### 5.1 Atualizações Obrigatórias em Lockstep nos Testes Existentes

1. **PR 1 (`fix/security-endpoints-password-jwt`):**
   - `backend/tests/test_api_endpoints.py:44-57` (`test_crud_campus`, `test_paginacao_sanitizada`): passar header `Authorization: Bearer <token_admin>` nas chamadas a `/api/v1/campi`.
   - `backend/tests/test_api_motor.py:9-29`: autenticar como `admin` ou `coordenador` em `GET /api/v1/motor/status` e `POST /api/v1/motor/teste-integracao`, e validar presença da chave `heuristica`.
   - `backend/tests/test_openapi_docs.py:40-70`: incluir `"401"` e `"403"` em `EXPECTED_ERROR_RESPONSES` para `/api/v1/motor/teste-integracao` e adicionar `/api/v1/campi`, `/api/v1/equipamentos` e `/api/v1/motor/*` em `PROTECTED_CRITICAL_ROUTES`.
   - `backend/tests/test_api_logs.py:468`: atualizar payload `"senha": "senha_segura_123"` para `"SenhaSegura123"` visando conformidade com a política de complexidade.
2. **PR 2 (`feat/auth-password-lifecycle-and-schema`):**
   - `backend/tests/test_migrations.py:132-141`: atualizar a asserção de `command.downgrade(alembic_cfg, "-1")` que atualmente verifica a remoção do índice de `003`, passando a validar a remoção de `mfa_codigo_recuperacao` e das 6 colunas de `usuario` da revisão `004_seguranca_auth_mfa`, além da paridade completa `upgrade head` -> `downgrade -1` -> `upgrade head`.
3. **PR 3 (`feat/mfa-totp-pyotp-recovery`):**
   - `backend/tests/test_auth.py:81-96, 129-138`: atualizar os testes de login bem-sucedido do `ADMIN` (`admin@sigaas.edu`) para cobrir explicitamente o fluxo de 2 etapas (`mfa_setup_required=True` -> `/auth/mfa/setup` -> `/auth/mfa/verify` com `pyotp.TOTP(segredo).now()` -> `GET /auth/me`), mantendo login direto apenas para perfis opcionais (`professor`/`aluno`) sem MFA ativado.
4. **PR 4 (`fix/rbac-campus-parity-frontend-backend`):**
   - Substituir todas as **32 invocações de `setRole()`** nos 6 arquivos (`role.guard.spec.ts` [9], `shell.component.spec.ts` [2], `components.spec.ts` [7], `integration-flow.spec.ts` [1], `dashboard.component.spec.ts` [11], `auth.service.spec.ts` [2]) por um helper compartilhado de teste (`createMockJwt({ sub, perfil, campus_id, scope: 'access', exp })`) injetado via `localStorage` ou `AuthService.login()`.
   - Atualizar payloads falsos de token (`'mock_jwt_token_123'`, `'fake_token_jwt'`, `'jwt_coord_token'`, `'tok'`) em `auth.interceptor.spec.ts`, `auth.service.spec.ts` e `integration-flow.spec.ts` para JWTs base64url com `exp` futuro e `scope: 'access'`.
   - Atualizar expectativas de paridade RBAC em `app.routes.spec.ts:9-25`, `role.guard.spec.ts:81-100`, `components.spec.ts:58-69`, `integration-flow.spec.ts:161-163` e `auth.service.spec.ts:27-28`.

### 5.2 Novos Testes Automatizados por Fase (RED -> GREEN -> REFACTOR)

1. **Fase RED — Backend (`backend/tests/test_security_policy.py`, `test_auth.py`, `test_mfa_totp.py`):**
   - `test_security_policy.py::test_endpoints_publicos_bloqueados_retornam_401`: verifica `401` em `/campi`, `/equipamentos` e `/motor/*` sem token, e `403` para `aluno`/`professor`/`secretaria` em `/motor/*` e `POST /campi`.
   - `test_security_policy.py::test_senha_maior_72_bytes_utf8_retorna_422`: envia `"A1b" + "ç" * 36` (75 bytes UTF-8) e verifica `422` sem `ValueError` 500.
   - `test_security_policy.py::test_settings_fail_fast_producao_segredos_fracos`: instancia `Settings(ENVIRONMENT="production", ...)` com `SECRET_KEY` padrão ou `MFA_ENCRYPTION_KEY=None` e verifica `ValidationError`/`ValueError`.
   - `test_auth.py::test_logout_e_alterar_senha_revogam_token_anterior`: valida incremento de `token_version` e retorno `401` com o token anterior.
   - `test_auth.py::test_challenge_token_nao_autentica_rotas_comuns`: usa token com `scope="mfa_challenge"` em `GET /api/v1/auth/me` e `/salas` e exige `401`.
   - `test_mfa_totp.py::test_fluxo_completo_setup_verify_e_cifra_fernet`: verifica que `mfa_segredo_cifrado` no banco difere do segredo base32, confirma geração única de 8 códigos `XXXX-XXXX` e sucesso de login subsequente.
   - `test_mfa_totp.py::test_totp_bloqueia_replay_no_mesmo_step`: envia o mesmo código TOTP duas vezes na mesma janela de 30s e valida `401` na segunda tentativa.
   - `test_mfa_totp.py::test_codigo_recuperacao_uso_unico_e_disable_bloqueado_admin`: confirma uso único de recovery code, `403` em `/mfa/disable` para `admin`/`coordenador`/`secretaria`, e `200` para `professor`/`aluno`.
   - `test_rbac_security.py::test_excluir_sala_outro_campus_retorna_404` e `test_horarios_meus_admin_campus_id`.
2. **Fase RED — Frontend (`frontend/src/app/**/*.spec.ts`):**
   - `auth.service.spec.ts` & `auth.guard.spec.ts`: rejeição de token expirado (`exp` passado), rejeição de `scope !== 'access'`, e remoção definitiva de `setRole`.
   - `admin.component.spec.ts`: `coordenador` não vê botões `Excluir` sala nem `Benchmark`; `admin` lista campi via `/api/v1/campi` e troca `campus_id`.
   - `login.component.spec.ts`: renderização do passo `mfa_setup` (QR/chave + 8 códigos) e passo `mfa_challenge`.
   - `seguranca.component.spec.ts`: troca de senha, regeneração de códigos e ocultação/bloqueio do botão de desativar MFA para perfis privilegiados.
3. **Fase GREEN + REFACTOR — Comandos de Verificação Obrigatórios:**
   - Backend + Cobertura: `pytest --cov=backend/app --cov-fail-under=85`
   - Segurança estática: `bandit -r backend/app -ll` e `ruff check backend/app --select=S,B,E,F`
   - Migrations PostgreSQL/SQLite: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
   - Frontend: `npx ng test --watch=false --browsers=ChromeHeadless` e `npx ng build`
   - Contratos & Diff: `npx openapi-typescript openapi.json -o frontend/src/app/core/models/api-contracts.ts` e `python scripts/check_pr_size.py origin/main 400`

---

## 6. Decomposição ClickUp e Portões (Gate 1 / Debate Adversarial / Gate 2)

### 6.1 Subtasks para Sincronização ClickUp (`clickup_sync.py sync-spec`)

- [ ] [SPEC-014-PR1] Blindar endpoints `/campi`, `/equipamentos` e `/motor/*`, adicionar `heuristica`, validar segredos em `config.py`, guarda UTF-8 <= 72B e claims JWT (`iss`/`aud`/`jti`/`scope`) + testes TDD
- [ ] [SPEC-014-PR2] Criar migration `004_seguranca_auth_mfa`, adicionar `token_version` e endpoints `/auth/alterar-senha`, `/auth/logout` e `/usuarios/{id}/redefinir-senha` + atualizar `test_migrations.py`
- [ ] [SPEC-014-PR3] Implementar MFA TOTP RFC 6238 (`pyotp`), cifra Fernet, proteção anti-replay, 8 códigos de recuperação com hash, login em 2 etapas e obrigatoriedade por perfil + testes `test_mfa_totp.py`
- [ ] [SPEC-014-PR4] Corrigir paridade RBAC Front/Back (`excluir_sala`, `/horarios/meus`, remoção de `setRole()`, `exp`/`scope` no `authGuard`, `hasRole` estrito, `/secretaria`, `/historico`, `homeRedirectGuard`, seletor dinâmico de campi) + migrar 6 `.spec.ts`
- [ ] [SPEC-014-PR5] Implementar fluxo Angular de login 2FA/onboarding, página `/seguranca`, regeneração de `api-contracts.ts` via `openapi-typescript` e suíte Jasmine/Karma

### 6.2 Protocolo de Portões e Auditoria (AGENTS.md §5-7)

1. **Gate 1 (Pré-Implementação):** Aprovação formal desta especificação `[SPEC-014]` antes de abrir branches ou alterar código-fonte, seguida do comando `python scripts/clickup_sync.py sync-spec docs/specs/spec-seguranca-mfa-rbac.md`.
2. **Debate Adversarial Multi-Agente Pré-PR:** Antes de submeter cada PR (especialmente PR 1, PR 2 e PR 3), executar auditoria dialética com `advocate-mapper`, `adversary-breaker`, `adversary-security`, `adversary-compliance` e `debate-arbiter`, aplicando o loop obrigatório de Re-Review sobre `git diff origin/main...HEAD` até consenso unânime sem vetos.
3. **Inspeção CodeRabbit AI & Fallback:** Após abertura de cada PR, inspecionar comentários textuais via `gh pr view <PR> --comments`; em caso de rate limit do CodeRabbit, anexar o parecer unânime do debate adversarial local.
4. **Gate 2 (Pré-Merge Human-in-the-Loop):** Aprovação humana explícita obrigatória antes de aplicar a migration `004_seguranca_auth_mfa` (PR 2) e antes de qualquer `gh pr merge <PR> --squash --delete-branch` em `main`.
