# SIGAAS Frontend (Angular)

Interface web Single Page Application (SPA) para o **Sistema de Gestão de Salas e Escalas com IA**.

## Perfis de Acesso
- **Admin / Coordenação**: Gestão de campi, salas, equipamentos e aprovação de sugestões de remanejamento.
- **Secretaria**: Cadastro de cursos, turmas, disciplinas e matrículas.
- **Professor**: Visualização de horários e turmas atribuídas.
- **Aluno**: Consulta de turmas, salas e horários matriculados.

## Regras Normativas
Conforme definido em `AGENTS.md`:
1. Nenhuma lógica de negócio ou cálculo pesado vive no frontend.
2. Toda comunicação é feita via HTTP consumindo a API FastAPI.
3. Componentes e rotas isolados por perfil com guards de autenticação JWT.

## Instalação e Execução
```bash
npm install
npm start
```
