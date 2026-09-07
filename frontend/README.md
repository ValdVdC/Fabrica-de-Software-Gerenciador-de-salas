# SIGAAS - Frontend Angular

Modulo de apresentacao do Sistema Integrado de Gestao de Salas e Escalas com IA (SIGAAS).

## Arquitetura

- **Framework**: Angular 20 (Standalone Components).
- **Roteamento por Perfis**:
  - `/login`: Formulario e selecao de perfil de acesso.
  - `/admin`: Painel da Coordenacao / Administracao Geral.
  - `/secretaria`: Gestao academica, cursos, turmas e matriculas.
  - `/professor`: Consulta de salas atribuidas e grade horaria docente.
  - `/aluno`: Consulta de grade individual e localizacao de salas.
- **Seguranca e Acesso**:
  - `authGuard`: Valida presenca de credenciais/sessao ativa.
  - `roleGuard`: Restringe e redireciona rotas filhas pelo perfil autorizado.
- **Regras Arquiteturais**:
  - Camada puramente apresentacional (zero logica de negocio ou calculos de alocacao).
  - Estilo visual sobrio institucional baseado no padrao Slate/Navy.
  - Total proibicao de emojis no layout e no codigo (iconografia 100% vetorial).

## Comandos Uteis

```bash
# Instalar dependencias
npm ci

# Executar servidor de desenvolvimento
npm start

# Compilar para producao
npm run build

# Executar testes unitarios
npx ng test --no-watch --browsers=ChromeHeadless
```
