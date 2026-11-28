# Guia Prático de Operação DevOps, AWS, GitHub, Zabbix, Grafana e Postman — SIGAAS

- **Sistema:** SIGAAS — Sistema Integrado de Gestão de Salas e Escalas com IA
- **Marco de Referência:** Entrega Final de DevOps (`07/12/2026`) — Especificação `docs/specs/spec-devops-entrega-final.md`
- **Data de Atualização:** `2026-11-27`
- **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
- **Curso e Turma:** Curso de Bacharelado em Ciência da Computação — Turma 8MB - CC (Semestre 2026/2)
- **Equipe:** Grupo 31 — SIGAAS
- **Repositório:** `https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas`

| Integrante | Matrícula | Papel no Squad |
| :--- | :---: | :--- |
| Ewerton Thyago Tavares da Silva | `01573977` | Scrum Master (Líder) |
| Wesclei Batista Da Cruz Júnior | `01606772` | Product Owner |
| Osvaldo Vasconcelos de Carvalho | `01614171` | Dev Backend / Sistemas |
| Gabriel Porfírio dos Santos | `01591399` | Dev Frontend |
| Flávio Vecch de Brito Farias | `01600988` | DBA & Documentação |

---

## 1. Visão Geral, Escopo e Pré-Requisitos Locais e de Contas

Este guia reúne **100% das ações manuais externas** que dependem de operação direta do usuário para colocar o SIGAAS em nuvem AWS com deploy contínuo, observabilidade via Zabbix e Grafana em Docker e validação automatizada via Postman/Newman, seguindo a ordem cronológica exata de execução.

> [!NOTE]
> Todos os arquivos de código, Dockerfiles, workflows e coleções descritos neste guia estão planejados na especificação `docs/specs/spec-devops-entrega-final.md` e serão entregues nos PRs 1 a 7 após aprovação do Gate 1. Execute os passos das Seções 2 e 3 antes da ativação dos pipelines de deploy automático (PR 7).

### 1.1 Contas e Ferramentas Necessárias
1. **Conta AWS ativa** com permissão para criar instâncias EC2, volumes EBS, Elastic IPs e Security Groups (região recomendada: `us-east-1` ou `sa-east-1`).
2. **Acesso Admin ao repositório GitHub** (`ValdVdC/Fabrica-de-Software-Gerenciador-de-salas`) para criar branches protegidas, Rulesets, Environments e Secrets.
3. **Estação de trabalho local** com:
   - Git (`>= 2.40`) e cliente OpenSSH (`ssh`, `ssh-keygen`);
   - **Postman Desktop** instalado (`https://www.postman.com/downloads/`);
   - **Node.js 22 LTS** e **Newman CLI** para execução em terminal:
     ```bash
     npm install -g newman
     newman --version
     ```

### 1.2 Geração do Par de Chaves SSH para Deploy do GitHub Actions
Na sua máquina local (fora do repositório), gere uma chave dedicada exclusiva para automação CI/CD:

```bash
ssh-keygen -t ed25519 -C "sigaas-github-actions-deploy" -f ~/.ssh/sigaas_aws_deploy
```

- **Chave privada (`~/.ssh/sigaas_aws_deploy`):** será cadastrada no Secret `AWS_SSH_KEY` do GitHub (nunca comite este arquivo no Git).
- **Chave pública (`~/.ssh/sigaas_aws_deploy.pub`):** será adicionada ao arquivo `~/.ssh/authorized_keys` do usuário na instância EC2.

---

## 2. Provisionamento na AWS (EC2, EBS, Security Groups, Docker e Diretórios)

### 2.1 Dimensionamento Recomendado da Instância EC2

A pilha completa do SIGAAS (PostgreSQL + FastAPI/C + Angular Nginx + Cron + Zabbix DB + Zabbix Server + Zabbix Web + Zabbix Agent 2 + Grafana = 9 contêineres) consome cerca de **4,2 GB a 5,6 GB de RAM** em operação contínua.

| Cenário de Implantação | Tipo de Instância | Especificação | Disco EBS | Indicação |
| :--- | :--- | :--- | :--- | :--- |
| **Opção A (Recomendada): EC2 Única Completa** | `t3.large` (ou `t3a.large`) | 2 vCPU, 8 GB RAM | 40 GB `gp3` | Executa Produção + Staging (em portas/diretórios separados) + Zabbix + Grafana sem risco de `OOMKill`. |
| **Opção B: Benchmark OpenMP 4 Threads em Nuvem** | `t3.xlarge` | 4 vCPU, 16 GB RAM | 40–50 GB `gp3` | Necessária se desejar demonstrar speedup paralelo real com `OMP_NUM_THREADS=4` diretamente na EC2. |
| **Opção C: Duas EC2s Separadas** | Staging: `t3.medium` / Prod: `t3.large` | 4 GB RAM / 8 GB RAM | 30 GB / 40 GB `gp3` | Isolamento físico completo entre Staging (`:80`) e Produção + Monitoramento. |

> [!CAUTION]
> Não utilize instâncias `t2.micro` ou `t3.micro` (1 GB de RAM) para rodar a pilha completa com Zabbix e Grafana. A memória insuficiente derrubará os processos Java/C/Python e do PostgreSQL por `OOMKill`.

### 2.2 Criação da Instância EC2 e Elastic IP no Console AWS
1. Acesse **AWS Console -> EC2 -> Instances -> Launch instances**.
2. Defina o nome (ex.: `sigaas-devops-ec2`).
3. Em **Application and OS Images (AMI)**, selecione **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type (`64-bit x86`)**.
4. Em **Instance type**, selecione `t3.large` (ou a opção escolhida na tabela acima).
5. Em **Key pair (login)**, selecione ou crie um par `.pem`/`.ppk` administrativo para acesso inicial via SSH.
6. Em **Configure storage**, defina **40 GiB**, tipo **`gp3`**.
7. Após criar a instância, acesse **Network & Security -> Elastic IPs -> Allocate Elastic IP address** e associe-o à instância (`Actions -> Associate Elastic IP address`) para evitar mudança de IP público após reinicializações.

### 2.3 Regras do Security Group (Firewall AWS)

Crie ou edite o Security Group anexado à EC2 com as regras exatas abaixo:

| Direção | Tipo / Protocolo | Porta | Origem / Destino | Finalidade |
| :--- | :--- | :---: | :--- | :--- |
| **Inbound** | SSH (`TCP`) | `22` | `<SEU_IP_ADMIN>/32` (e IPs da equipe / runner se aplicável) | Acesso SSH administrativo e deploy CI/CD. Evite `0.0.0.0/0` em produção definitiva. |
| **Inbound** | HTTP (`TCP`) | `80` | `0.0.0.0/0` | Acesso público à interface Nginx (Produção) e proxy `/api/`, `/health`, `/health/ready`, `/docs`. |
| **Inbound** | HTTPS (`TCP`) | `443` | `0.0.0.0/0` | Acesso HTTPS quando TLS/Certbot estiver configurado em domínio próprio. |
| **Inbound** | Custom TCP | `8080` | `0.0.0.0/0` ou `<IP_EQUIPE>/32` | **Apenas se Staging e Produção compartilharem a mesma EC2** (Nginx Staging na porta `8080`). |
| **Inbound** | Custom TCP | `8081` | `<IP_EQUIPE_AVALIACAO>/32` | Interface Web do **Zabbix** (restrinja ao IP da equipe/banca ou use túnel SSH). |
| **Inbound** | Custom TCP | `3000` | `<IP_EQUIPE_AVALIACAO>/32` | Interface Web do **Grafana** (restrinja ao IP da equipe/banca ou use túnel SSH). |
| **Inbound** | PostgreSQL / FastAPI / Zabbix Server | `5432`, `8000`, `10051` | **FECHADAS (NÃO ABRIR)** | Comunicação estritamente interna nas redes Docker `backend_net` e `monitoring_net`. |
| **Outbound** | All traffic | All | `0.0.0.0/0` | Downloads de pacotes `apt`, imagens Docker e atualizações. |

### 2.4 Instalação de Docker Engine, Compose v2, Swap, `DOCKER_GID` e Diretórios na EC2

Conecte-se à instância via SSH usando sua chave administrativa e execute os comandos na ordem:

```bash
ssh -i /caminho/sua-chave-admin.pem ubuntu@<ELASTIC_IP_AWS>
```

1. **Atualizar sistema e instalar utilitários base + Docker Engine + Docker Compose v2:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   sudo apt-get install -y ca-certificates curl gnupg git ufw

   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   sudo chmod a+r /etc/apt/keyrings/docker.gpg

   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker ubuntu
   ```

2. **Configurar arquivo Swap de 2 GB (margem preventiva contra picos de build):**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Obter o GID do grupo `docker` (necessário para o `zabbix-agent2` ler `/var/run/docker.sock`):**
   ```bash
   getent group docker | cut -d: -f3
   ```
   Anote esse número (ex.: `988` ou `999`) — ele será usado na variável `DOCKER_GID` do `.env`.

4. **Registrar a chave pública do GitHub Actions na EC2:**
   Cole o conteúdo de `~/.ssh/sigaas_aws_deploy.pub` em `~/.ssh/authorized_keys` na EC2:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   echo "ssh-ed25519 AAAA... sigaas-github-actions-deploy" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```
   Encerre a sessão (`exit`) e teste da sua máquina local a conexão sem senha:
   ```bash
   ssh -i ~/.ssh/sigaas_aws_deploy ubuntu@<ELASTIC_IP_AWS> "docker --version && docker compose version"
   ```

5. **Criar diretórios de implantação e clonar o repositório na EC2:**
   - **Caso EC2 única para Staging + Produção:**
     ```bash
     sudo mkdir -p /opt/sigaas/staging /opt/sigaas/prod
     sudo chown -R ubuntu:ubuntu /opt/sigaas

     git clone -b staging https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas.git /opt/sigaas/staging
     git clone -b main https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas.git /opt/sigaas/prod
     ```
   - *(Se optar por duas EC2s separadas, clone apenas `/opt/sigaas/staging` na EC2 de Staging e `/opt/sigaas/prod` na EC2 de Produção.)*

---

## 3. Configuração do GitHub (Branches, Proteções, Environments e Secrets)

### 3.1 Criação das 3 Branches Permanentes (`main`, `staging`, `develop`)
Mantendo `main` como branch principal protegida e atendendo ao mínimo de 3 branches exigido na rubrica:

```bash
git checkout main
git pull origin main

git checkout -b staging
git push -u origin staging

git checkout -b develop
git push -u origin develop
```

Confirmar que o repositório remoto exibe exatamente `main`, `staging` e `develop` em **GitHub -> Code -> Branches**.

### 3.2 Configuração de Proteção de Branch (Branch Protection Rules / Rulesets)
Repita a configuração abaixo em **GitHub -> Settings -> Branches -> Add branch protection rule** (ou **Rulesets**) para **cada uma das 3 branches** (`main`, `staging` e `develop`):

1. **Branch name pattern:** criar uma regra para `main`, uma para `staging` e uma para `develop`.
2. Marcar **Require a pull request before merging**:
   - Em `main` e `staging`: **Require approvals** = `1` (e marcar **Dismiss stale pull request approvals when new commits are pushed**).
   - Marcar **Require conversation resolution before merging**.
3. Marcar **Require status checks to pass before merging** e **Require branches to be up to date before merging**. Selecionar os jobs obrigatórios do workflow `Continuous Integration (CI)`:
   - `Code Quality & Policy Enforcement`
   - `Backend Tests & Coverage (Pytest)`
   - `Allocation Engine (C & OpenMP)`
   - `Frontend Tests & Build (Angular)`
   - `Docker Environment Smoke Test`
   - `Newman API Integration Suite`
4. Marcar **Do not allow bypassing the above settings** (ou restringir bypass apenas ao líder em emergências documentadas).
5. **Proibir commits e force pushes diretos:** manter desmarcadas **Allow force pushes** e **Allow deletions**.
6. Em **Settings -> General -> Pull Requests**:
   - Deixar marcada **APENAS** a opção **Allow squash merging**;
   - **Desmarcar** *Allow merge commits* e *Allow rebase merging* (regra de Squash and Merge exclusivo do `AGENTS.md` §6.3);
   - Marcar **Automatically delete head branches**.

### 3.3 Cadastro de GitHub Environments (`staging` e `production`)
Em **GitHub -> Settings -> Environments**:

1. Clique em **New environment**, crie `staging`:
   - Em **Deployment branches and tags -> Selected branches**, adicione regra apenas para `staging`.
2. Clique em **New environment**, crie `production`:
   - Marque **Required reviewers** e adicione o Scrum Master (`Ewerton Thyago`) e/ou responsável técnico pelo Gate 2 (assim o deploy em produção só executa após aprovação humana explícita após o CI verde);
   - Em **Deployment branches and tags -> Selected branches**, adicione regra apenas para `main`.

### 3.4 Tabela Completa de GitHub Secrets

Cadastre os secrets dentro de cada respectivo **Environment** (`staging` e `production`) em **Settings -> Environments -> <ambiente> -> Environment secrets**:

| Nome do Secret | Environment | Valor Esperado | Observação de Segurança |
| :--- | :--- | :--- | :--- |
| `AWS_HOST` | `staging` e `production` | `<ELASTIC_IP_AWS>` (ou IP da EC2 de cada ambiente) | Endereço público ou DNS da instância EC2. |
| `AWS_USER` | `staging` e `production` | `ubuntu` | Usuário SSH configurado na EC2. |
| `AWS_PORT` | `staging` e `production` | `22` | Porta SSH configurada no Security Group. |
| `AWS_SSH_KEY` | `staging` e `production` | Conteúdo integral de `~/.ssh/sigaas_aws_deploy` (incluindo `-----BEGIN OPENSSH PRIVATE KEY-----` e `-----END OPENSSH PRIVATE KEY-----`) | Nunca use chave com passphrase interativa no CI. |
| `DEPLOY_PATH` | `staging` / `production` | `/opt/sigaas/staging` (no `staging`) e `/opt/sigaas/prod` (no `production`) | Diretório onde o repositório foi clonado na EC2. |
| `ENV_FILE_STAGING` | `staging` | Conteúdo completo do arquivo `.env.staging` (Seção 4) | Gravado na EC2 com `chmod 600 .env` durante o deploy. |
| `ENV_FILE_PROD` | `production` | Conteúdo completo do arquivo `.env.prod` (Seção 4) | Gravado na EC2 com `chmod 600 .env` durante o deploy. |

> [!CAUTION]
> O conteúdo de `ENV_FILE_STAGING` e `ENV_FILE_PROD` já transporta com segurança as credenciais internas (`POSTGRES_PASSWORD`, `POSTGRES_RO_PASSWORD`, `SECRET_KEY`, `ZABBIX_DB_PASSWORD`, `ZABBIX_API_PASSWORD` e `GRAFANA_ADMIN_PASSWORD`) sem jamais comitar nenhum arquivo `.env` no Git.

---

## 4. Configuração de Variáveis `.env` na AWS e Subida Inicial

### 4.1 Geração de Chaves e Senhas Fortes na EC2
Nunca utilize `changeme_local_only`, `changeme_homolog_only` ou `super-secret-key-change-in-production-min-32-chars` em nuvem. Execute na EC2 para gerar valores criptográficos únicos:

```bash
# Gerar SECRET_KEY (64 caracteres hexadecimais)
openssl rand -hex 32

# Gerar senhas fortes para PostgreSQL, sigaas_ro, Zabbix e Grafana (execute uma vez para cada senha)
openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24; echo
```

### 4.2 Modelo `.env.staging` (`/opt/sigaas/staging/.env` e Secret `ENV_FILE_STAGING`)

```env
# === Ambiente e Seguranca ===
ENVIRONMENT=staging
SECRET_KEY=<GERADO_VIA_OPENSSL_RAND_HEX_32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://<ELASTIC_IP_AWS>:8080,http://<ELASTIC_IP_AWS>

# === PostgreSQL SIGAAS (Staging) ===
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=gestao_salas_staging
POSTGRES_USER=sigaas_staging
POSTGRES_PASSWORD=<SENHA_FORTE_MIN_24_CHARS>
POSTGRES_RO_PASSWORD=<SENHA_FORTE_READONLY_MIN_24_CHARS>
DATABASE_URL=postgresql+psycopg2://sigaas_staging:<SENHA_FORTE_MIN_24_CHARS>@db:5432/gestao_salas_staging

# === Motor C / Backend ===
RUN_MIGRATIONS_ON_STARTUP=true
UVICORN_WORKERS=1
OMP_NUM_THREADS=2
MOTOR_ALOCACAO_LIB_PATH=/opt/sigaas/motor_alocacao.so
STAGING_HTTP_PORT=8080
```

### 4.3 Modelo `.env.prod` (`/opt/sigaas/prod/.env` e Secret `ENV_FILE_PROD`)

```env
# === Ambiente e Seguranca ===
ENVIRONMENT=prod
SECRET_KEY=<GERADO_VIA_OPENSSL_RAND_HEX_32_DISTINTO>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://<ELASTIC_IP_AWS>,https://<SEU_DOMINIO_SE_HOUVER>

# === PostgreSQL SIGAAS (Producao) ===
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=gestao_salas_prod
POSTGRES_USER=sigaas_prod
POSTGRES_PASSWORD=<SENHA_FORTE_PROD_MIN_24_CHARS>
POSTGRES_RO_PASSWORD=<SENHA_FORTE_READONLY_PROD_MIN_24_CHARS>
DATABASE_URL=postgresql+psycopg2://sigaas_prod:<SENHA_FORTE_PROD_MIN_24_CHARS>@db:5432/gestao_salas_prod

# === Motor C / Backend ===
RUN_MIGRATIONS_ON_STARTUP=true
UVICORN_WORKERS=1
OMP_NUM_THREADS=2
MOTOR_ALOCACAO_LIB_PATH=/opt/sigaas/motor_alocacao.so

# === Observabilidade: Zabbix + Grafana ===
DOCKER_GID=<ID_DO_GRUPO_DOCKER_OBTIDO_COM_GETENT>
ZABBIX_HOSTNAME=sigaas-ec2-host
ZABBIX_DB_NAME=zabbix
ZABBIX_DB_USER=zabbix
ZABBIX_DB_PASSWORD=<SENHA_FORTE_ZABBIX_DB>
ZABBIX_API_USER=grafana_reader
ZABBIX_API_PASSWORD=<SENHA_FORTE_ZABBIX_API>
GRAFANA_ADMIN_USER=sigaas_admin
GRAFANA_ADMIN_PASSWORD=<SENHA_FORTE_GRAFANA_ADMIN>
```

Proteja os arquivos `.env` na EC2:
```bash
chmod 600 /opt/sigaas/staging/.env /opt/sigaas/prod/.env
```

### 4.4 Subida Inicial, Verificação de Migrations e Seed Inicial

Após o merge dos PRs de infraestrutura e observabilidade (ou na primeira validação manual na EC2):

```bash
cd /opt/sigaas/prod
docker compose -p sigaas-prod \
  -f docker/compose/docker-compose.prod.yml \
  -f docker/compose/docker-compose.monitoring.yml \
  up -d --build
```

Verifique o status dos contêineres, migrations automáticas e saúde da API:

```bash
# 1. Todos os 9 conteineres devem exibir status Up / (healthy)
docker compose -p sigaas-prod ps

# 2. Confirmar que alembic upgrade head foi aplicado no boot
docker compose -p sigaas-prod exec -T backend alembic current

# 3. Povoar dados iniciais (apenas na primeira inicializacao ou demonstracao)
docker compose -p sigaas-prod exec -T backend python /scripts/seed_db.py

# 4. Validar endpoints /health e /health/ready via Nginx (porta 80)
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1/health/ready
curl -fsS http://127.0.0.1/api/v1/motor/status
```

Para o ambiente de Staging (caso co-hospedado na porta `8080`):
```bash
cd /opt/sigaas/staging
docker compose -p sigaas-staging -f docker/compose/docker-compose.staging.yml up -d --build
docker compose -p sigaas-staging ps
curl -fsS http://127.0.0.1:8080/health/ready
```

---

## 5. Configuração Manual e Validação do Zabbix e do Grafana

### 5.1 Configuração Inicial no Zabbix Web (`http://<ELASTIC_IP_AWS>:8081`)

1. Abra o navegador em `http://<ELASTIC_IP_AWS>:8081` (ou use túnel SSH `ssh -i ~/.ssh/sigaas_aws_deploy -L 8081:127.0.0.1:8081 ubuntu@<ELASTIC_IP_AWS>` e acesse `http://localhost:8081`).
2. Faça login com as credenciais padrão iniciais do Zabbix:
   - **Username:** `Admin`
   - **Password:** `zabbix`
3. **Troca obrigatória de senha do Admin:**
   - No menu esquerdo, acesse **Users -> Users -> Admin -> Change password**;
   - Defina uma senha forte e salve (**Update**).
4. **Criar usuário de API para o Grafana:**
   - Acesse **Users -> Users -> Create user**;
   - **Username:** mesmo valor de `ZABBIX_API_USER` do `.env` (ex.: `grafana_reader`);
   - **Groups:** `Guests` ou grupo com permissão de leitura (`Read`) nos hosts monitorados;
   - **Password:** exatamente o valor de `ZABBIX_API_PASSWORD` do `.env`;
   - Na aba **Permissions**, selecione role **User role** (com acesso de leitura à API JSON-RPC) e salve.
5. **Cadastrar e validar o Host Docker (`sigaas-ec2-host`):**
   - Acesse **Data collection -> Hosts -> Create host**;
   - **Host name:** `sigaas-ec2-host` (deve coincidir exatamente com `ZBX_HOSTNAME` / `ZABBIX_HOSTNAME` no contêiner `zabbix-agent2`);
   - **Templates:** vincule **Docker by Zabbix agent 2** e **Linux by Zabbix agent 2**;
   - **Host groups:** `Linux servers` / `Applications` (ou crie `SIGAAS Containers`);
   - **Interfaces -> Add -> Agent:**
     - **DNS name:** `zabbix-agent2`
     - **Connect to:** `DNS`
     - **Port:** `10050`
   - Clique em **Add** e aguarde 1 a 2 minutos.
6. **Validar coleta em tempo real:**
   - Acesse **Monitoring -> Hosts** e confirme que o ícone **ZBX** do host `sigaas-ec2-host` está verde;
   - Acesse **Monitoring -> Latest data**, filtre por `sigaas-ec2-host` e confirme que todos os contêineres (`sigaas_postgres_prod`, `sigaas_backend_prod`, `sigaas_frontend_prod`, `sigaas_cron_prod`, `zabbix-*`, `grafana`) aparecem com métricas de CPU, memória, uptime, restarts e status de healthcheck.

### 5.2 Validação e Ajustes no Grafana (`http://<ELASTIC_IP_AWS>:3000`)

1. Acesse `http://<ELASTIC_IP_AWS>:3000` (ou via túnel SSH `-L 3000:127.0.0.1:3000`).
2. Faça login com `GRAFANA_ADMIN_USER` e `GRAFANA_ADMIN_PASSWORD` definidos no `.env.prod`.
3. **Validar plugin Zabbix (`alexanderzobnin-zabbix-app`):**
   - Acesse **Administration -> Plugins and data -> Plugins**;
   - Pesquise por **Zabbix** e confirme que o plugin está **Enabled** (habilitado automaticamente pelo arquivo `docker/grafana/provisioning/plugins/zabbix.yaml`). Caso esteja desabilitado, clique em **Enable**.
4. **Validar Datasources provisionados:**
   - Acesse **Connections -> Data sources**;
   - Abra **Zabbix**, confirme a URL `http://zabbix-web:8080/api_jsonrpc.php` e clique em **Save & test** — o retorno deve ser `Zabbix API version: 7.0.x`;
   - Abra **SIGAAS PostgreSQL**, confirme host `db:5432`, usuário read-only `sigaas_ro` e clique em **Save & test** — o retorno deve ser `Database Connection OK`.
5. **Validar Dashboards ao vivo:**
   - Acesse **Dashboards -> SIGAAS** e abra:
     - **SIGAAS — Infraestrutura e Contêineres (Zabbix)**: CPU por contêiner, consumo de memória RAM, disponibilidade e contagem de reinicializações;
     - **SIGAAS — Operação Acadêmica e IA Preditiva (PostgreSQL)**: ocupação por campus, distribuição de `SugestaoRemanejamento` (`pendente`, `aprovado`, `rejeitado`), histograma de `PrevisaoFalta` e taxa de eventos `LogAlocacao`.
   - *(Caso precise importar ou duplicar manualmente um dashboard pela interface Web: acesse **Dashboards -> New -> Import**, faça upload do arquivo JSON de `docker/grafana/dashboards/`, selecione os datasources `Zabbix` e `SIGAAS PostgreSQL` e clique em **Import**.)*

---

## 6. Importação, Execução e Documentação no Postman e Newman CLI

### 6.1 Importação no Postman Desktop
1. Abra o **Postman Desktop** e clique em **Import**.
2. Selecione simultaneamente os arquivos do diretório `docs/postman/`:
   - `docs/postman/sigaas-devops.postman_collection.json`
   - `docs/postman/sigaas-local.postman_environment.json`
   - `docs/postman/sigaas-staging.postman_environment.json`
   - `docs/postman/sigaas-prod.postman_environment.json`
3. No canto superior direito do Postman, selecione o environment ativo (`SIGAAS - Local`, `SIGAAS - Staging` ou `SIGAAS - Prod`).
4. Clique no ícone de edição do environment selecionado e ajuste:
   - `base_url`: `http://localhost:8000` (local), `http://<ELASTIC_IP_AWS>:8080` (staging) ou `http://<ELASTIC_IP_AWS>` / `https://<SEU_DOMINIO>` (prod);
   - `admin_password`, `coord_password`, `aluno_password`: em ambientes povoados pelo script de fixture `scripts/seed_db.py`, a senha inicial é `sigaas123` para os usuários de demonstração (`admin@sigaas.edu`, `coord.cc@sigaas.edu`, `aluno@sigaas.edu`).

> [!CAUTION]
> Em ambiente de Produção exposto publicamente, altere imediatamente as senhas padrão das contas criadas pelo `scripts/seed_db.py` ou remova usuários de demonstração após os testes, mantendo o segredo da conta administrativa apenas no cofre de senhas da equipe e no runner do Newman.

### 6.2 Execução Manual de Requisições (Comprovando GET, POST e Persistência no PostgreSQL)
1. **Pasta `01 - Health & Root`:** execute `GET /health/ready` e confirme HTTP `200` com `"database": "connected"`.
2. **Pasta `02 - Auth & RBAC`:** execute `POST /api/v1/auth/login` (Admin). O script na aba **Tests** captura automaticamente `access_token` e `campus_id` no environment.
3. **Pasta `06 - Salas (CRUD Completo)`:**
   - Execute `POST /api/v1/salas` (cria sala no PostgreSQL e grava evento `criacao` em `log_alocacao`);
   - Execute `GET /api/v1/salas/{{created_sala_id}}` (comprova persistência dos dados gravados);
   - Execute `PATCH /api/v1/salas/{{created_sala_id}}` (altera `capacidade` para `55` e registra `alteracao`);
   - Execute `DELETE /api/v1/salas/{{created_sala_id}}` seguido de `GET` (comprova exclusão com retorno `404`).
4. **Pasta `10 - Matrículas (Contador Atômico)`:** execute `POST /matriculas` -> `GET /turmas/{{created_turma_id}}` (`num_matriculados == 1`) -> `DELETE /matriculas/{{created_matricula_id}}` -> `GET /turmas/{{created_turma_id}}` (`num_matriculados == 0`).

### 6.3 Execução em Lote (Collection Runner) e Documentação no Postman
1. Clique nos três pontos ao lado da coleção **SIGAAS — Entrega Final DevOps** -> **Run collection**.
2. Confirme a ordem das 16 pastas (`01` a `16`), marque **Persist responses for a session** e clique em **Run SIGAAS — Entrega Final DevOps**.
3. Verifique que **100% das asserções (`pm.test`)** ficaram verdes (`Passed`).
4. Para visualizar a documentação completa da API no Postman: clique no nome da coleção -> aba **Overview / View complete documentation** (ou **Publish Docs** caso queira link web público da equipe).

### 6.4 Execução em Linha de Comando via Newman CLI
Para reproduzir localmente ou validar contra Staging na AWS exatamente como o CI executa:

```bash
# Contra ambiente local
newman run docs/postman/sigaas-devops.postman_collection.json \
  -e docs/postman/sigaas-local.postman_environment.json \
  --reporters cli,junit \
  --reporter-junit-export reports/newman-local.xml \
  --timeout-request 10000 \
  --bail

# Contra AWS Staging (injetando URL e senha sem gravar em arquivo)
newman run docs/postman/sigaas-devops.postman_collection.json \
  -e docs/postman/sigaas-staging.postman_environment.json \
  --env-var "base_url=http://<ELASTIC_IP_AWS>:8080" \
  --env-var "admin_password=<SENHA_ADMIN_STAGING>" \
  --reporters cli,junit \
  --reporter-junit-export reports/newman-staging.xml \
  --timeout-request 10000 \
  --bail
```

---

## 7. Checklist Final de Evidências para a Entrega de 07/12/2026

Utilize esta lista antes da apresentação e submissão final para confirmar que todos os itens da rubrica de DevOps possuem evidência pronta:

### 7.1 Aplicação JSON (GET/POST), Front-end, Back-end e PostgreSQL
- [ ] Front-end Angular carregando via Nginx na EC2 (`http://<ELASTIC_IP_AWS>/`) sem erros de console ou CORS.
- [ ] Fluxo demonstrado ao vivo na interface e via Postman: login JWT (`POST /api/v1/auth/login`), cadastro via `POST` (ex.: Sala ou Turma), consulta `GET` após recarregar a página e alteração/exclusão persistida no PostgreSQL (`docker compose exec -T db psql ...`).
- [ ] Retorno `200 OK` de `http://<ELASTIC_IP_AWS>/health` e `http://<ELASTIC_IP_AWS>/health/ready`.

### 7.2 Arquitetura Docker Completa (App + Zabbix + Grafana)
- [ ] Saída de `docker compose -p sigaas-prod ps` exibindo todos os 9 contêineres saudáveis (`db`, `backend`, `frontend`, `cron`, `zabbix-db`, `zabbix-server`, `zabbix-web`, `zabbix-agent2`, `grafana`).
- [ ] Saída de `docker compose -p sigaas-prod logs --tail=30 cron` comprovando execução real do job `run_ia_job.py` sem alteração direta de `horario.sala_id`.
- [ ] Captura do **Zabbix Web (`:8081`)** em *Monitoring -> Hosts* (`ZBX` verde em `sigaas-ec2-host`) e *Monitoring -> Latest data* exibindo métricas de contêineres coletadas via `/var/run/docker.sock`.
- [ ] Captura do **Grafana (`:3000`)** com os dois datasources (`Zabbix` e `SIGAAS PostgreSQL`) testados e ambos os dashboards exibindo gráficos em tempo real.

### 7.3 Estratégia Git/GitHub (>= 3 Branches com `main` Principal) e Auto-Deploy AWS
- [ ] Print de **GitHub -> Branches** mostrando `main` (default/principal), `staging` e `develop` todas protegidas com regras de PR, CI obrigatório e Squash & Merge exclusivo.
- [ ] Histórico de PRs fatiados (`<= 400` LOC) promovidos em `feat/* -> develop -> staging -> main` com checks verdes no GitHub Actions (`Continuous Integration (CI)`) e revisão do CodeRabbit inspecionada.
- [ ] Execução comprovada de `deploy-staging.yml` (automático após CI verde em `staging`) e `deploy-prod.yml` (após aprovação no Environment `production` e CI verde em `main`) refletindo imediatamente uma mudança visível na EC2 AWS.

### 7.4 Postman e Newman
- [ ] Print do **Postman Collection Runner** com todas as requisições e asserções `pm.test` aprovadas e da tela de documentação da coleção.
- [ ] Log de execução do `newman run` no terminal ou no job `test-newman-api` do GitHub Actions com relatório JUnit gerado e zero falhas.
