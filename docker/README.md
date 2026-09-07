# Arquitetura e Guia do Ecossistema Docker (SIGAAS)

Este diretorio contem a infraestrutura de conteinerizacao completa e padronizada do SIGAAS para desenvolvimento local, homologacao e producao.

---

## 1. Estrutura de Diretorios

`	ext
docker/
├── compose/
│   ├── docker-compose.local.yml     # Desenvolvimento local com hot-reload e portas mapeadas
│   ├── docker-compose.homolog.yml   # Homologacao e testes integrados
│   └── docker-compose.prod.yml      # Producao segura (non-root, restart always, limites de recursos)
├── backend/
│   └── Dockerfile                   # Build do FastAPI com compilacao C/OpenMP
├── frontend/
│   ├── Dockerfile                   # Multi-stage build Angular (Node 22) + Nginx Alpine
│   └── nginx.conf                   # Roteamento SPA Angular e proxy reverso para /api/
└── cron/
    ├── Dockerfile                   # Container leve para tarefas agendadas
    ├── crontab                      # Configuracao de agendamento de jobs
    └── entrypoint.sh                # Script de inicializacao do daemon cron
`

---

## 2. Servicos do Ecossistema

- **sigaas_postgres**: PostgreSQL 16 Alpine com persistencia em volume nomeado e healthcheck nativo.
- **sigaas_backend**: Backend Python 3.12 (FastAPI), compilacao automatica do motor de alocacao C (motor_alocacao.so) com OpenMP e hot-reload no modo local.
- **sigaas_frontend**: Single Page Application em Angular 20 compilada e servida por servidor web Nginx de alta performance com proxy reverso transparente para a API (/api/) e documentacao Swagger (/docs).
- **sigaas_cron**: Execucao agendada em lote para as rotinas de previsao de faltas da IA, sincronizacoes e manutencao.

---

## 3. Como Executar os Ambientes

### Ambiente Local (Desenvolvimento)
Para subir o ecossistema completo a partir da raiz do projeto:
`ash
docker compose up --build
`
Ou especificando o arquivo compose dedicado:
`ash
docker compose -f docker/compose/docker-compose.local.yml up --build
`

**Portas e Acessos Locais:**
- Frontend Angular: http://localhost:4200
- API FastAPI (Swagger Docs): http://localhost:8000/docs
- API via Proxy Nginx: http://localhost:4200/api/v1/motor/status
- PostgreSQL: localhost:5432

---

### Ambiente de Homologacao
Utilizado para validacao integrada e espelhamento de producao:
`ash
docker compose -f docker/compose/docker-compose.homolog.yml up --build -d
`

---

### Ambiente de Producao
Modo endurecido, com politicas de reinicio automatico e sem ferramentas de compilacao no runtime do frontend:
`ash
docker compose -f docker/compose/docker-compose.prod.yml up --build -d
`
