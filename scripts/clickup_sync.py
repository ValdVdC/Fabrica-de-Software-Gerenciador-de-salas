#!/usr/bin/env python3
"""
scripts/clickup_sync.py - Ferramenta CLI para automação e sincronização com ClickUp.

Suporta:
- Testar conexão e listar Workspaces/Espaços/Listas.
- Importar backlog CSV para o ClickUp.
- Criar tarefas e subtarefas a partir de arquivos de especificação (SDD).
- Atualizar status de tarefas.
"""

import os
import sys
import csv
import argparse
import re
from pathlib import Path

# Carregar variáveis de ambiente de .env se existir
try:
    from dotenv import load_dotenv
    # Carregar do diretório raiz do projeto
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("ERRO: Pacote 'requests' não encontrado. Instale com: pip install requests python-dotenv", file=sys.stderr)
    sys.exit(1)

CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"


def get_headers(api_key: str = None) -> dict:
    key = api_key or os.getenv("CLICKUP_API_KEY")
    if not key or key.startswith("pk_your_clickup") or not key.strip():
        print("\n[!] ERRO: CLICKUP_API_KEY não configurada no arquivo .env ou nas variáveis de ambiente.", file=sys.stderr)
        print("    Abra o arquivo .env e preencha CLICKUP_API_KEY=pk_...\n", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": key.strip(),
        "Content-Type": "application/json"
    }


def test_connection(args):
    headers = get_headers(args.api_key)
    print("Testando conexão com a API do ClickUp...")
    
    # Obter usuário autenticado
    res = requests.get(f"{CLICKUP_BASE_URL}/user", headers=headers)
    if res.status_code != 200:
        print(f"[X] Falha na autenticação (HTTP {res.status_code}): {res.text}", file=sys.stderr)
        sys.exit(1)
    
    user_data = res.json().get("user", {})
    print("[OK] Conexao bem-sucedida!")
    print(f"    Usuario: {user_data.get('username')} ({user_data.get('email')})")
    
    # Listar equipes/workspaces
    res_teams = requests.get(f"{CLICKUP_BASE_URL}/team", headers=headers)
    if res_teams.status_code == 200:
        teams = res_teams.json().get("teams", [])
        print(f"\nWorkspaces disponiveis ({len(teams)}):")
        for team in teams:
            team_id = team.get("id")
            print(f"  - [{team_id}] {team.get('name')}")
            
            # Listar espacos
            res_spaces = requests.get(f"{CLICKUP_BASE_URL}/team/{team_id}/space?archived=false", headers=headers)
            if res_spaces.status_code == 200:
                spaces = res_spaces.json().get("spaces", [])
                for sp in spaces:
                    space_id = sp.get("id")
                    print(f"    * Espaco: [{space_id}] {sp.get('name')}")
                    # Listar listas avulsas do espaco
                    res_lists = requests.get(f"{CLICKUP_BASE_URL}/space/{space_id}/list?archived=false", headers=headers)
                    if res_lists.status_code == 200:
                        lists = res_lists.json().get("lists", [])
                        for lst in lists:
                            print(f"        -> Lista: [{lst.get('id')}] {lst.get('name')}")
                    
                    # Listar pastas e suas listas
                    res_folders = requests.get(f"{CLICKUP_BASE_URL}/space/{space_id}/folder?archived=false", headers=headers)
                    if res_folders.status_code == 200:
                        folders = res_folders.json().get("folders", [])
                        for fld in folders:
                            print(f"        Pasta: [{fld.get('id')}] {fld.get('name')}")
                            for flist in fld.get("lists", []):
                                print(f"           -> Lista: [{flist.get('id')}] {flist.get('name')}")


def import_csv(args):
    headers = get_headers(args.api_key)
    list_id = args.list_id or os.getenv("CLICKUP_LIST_ID")
    if not list_id or list_id == "your_clickup_list_id_here" or not list_id.strip():
        print("\n[!] ERRO: CLICKUP_LIST_ID não fornecido. Use --list-id ou preencha no .env\n", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"ERRO: Arquivo CSV '{args.csv_file}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"Importando backlog de '{csv_path}' para a Lista ClickUp ID: {list_id}...")

    # Primeiro, verificar status válidos da lista
    list_info = requests.get(f"{CLICKUP_BASE_URL}/list/{list_id}", headers=headers)
    available_statuses = []
    if list_info.status_code == 200:
        statuses = list_info.json().get("statuses", [])
        available_statuses = [s.get("status", "").lower() for s in statuses]
        print(f"Status configurados na lista: {', '.join(available_statuses)}")

    created_count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sprint = row.get("Sprint", "").strip()
            tarefa = row.get("Tarefa", "").strip()
            papel = row.get("Papel", "").strip()
            status_raw = row.get("Status", "").strip()
            descricao = row.get("Descrição", "").strip()

            if not tarefa:
                continue

            # Mapeamento inteligente de status
            mapped_status = None
            if "conclu" in status_raw.lower() or "done" in status_raw.lower():
                for s in available_statuses:
                    if s in ["closed", "complete", "concluído", "concluido", "done"]:
                        mapped_status = s
                        break
            elif "fazer" in status_raw.lower() or "to do" in status_raw.lower() or "todo" in status_raw.lower() or "pendente" in status_raw.lower():
                for s in available_statuses:
                    if s in ["pendente", "to do", "open", "a fazer", "backlog"]:
                        mapped_status = s
                        break

            tags = []
            if sprint:
                tags.append(sprint)
            if papel:
                tags.append(papel)

            desc_body = f"**Sprint:** {sprint}\n**Papel:** {papel}\n**Descrição:** {descricao}\n\n*Importado automaticamente pelo Antigravity SDD Sync.*"

            payload = {
                "name": f"[{sprint}] {tarefa}",
                "description": desc_body,
                "markdown_content": desc_body,
                "tags": tags
            }
            if mapped_status:
                payload["status"] = mapped_status

            resp = requests.post(f"{CLICKUP_BASE_URL}/list/{list_id}/task", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                task_data = resp.json()
                print(f" [OK] Criada: [{sprint}] {tarefa} -> ID: {task_data.get('id')}")
                created_count += 1
            else:
                print(f" [X] Falha ao criar '{tarefa}': HTTP {resp.status_code} - {resp.text}")

    print(f"\nImportação concluída: {created_count} tarefas criadas com sucesso!")


def create_task(args):
    headers = get_headers(args.api_key)
    list_id = args.list_id or os.getenv("CLICKUP_LIST_ID")
    if not list_id:
        print("ERRO: CLICKUP_LIST_ID não fornecido.", file=sys.stderr)
        sys.exit(1)

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    payload = {
        "name": args.name,
        "description": args.description or "",
        "markdown_content": args.description or "",
        "tags": tags
    }
    if args.status:
        payload["status"] = args.status
    if args.parent:
        payload["parent"] = args.parent

    resp = requests.post(f"{CLICKUP_BASE_URL}/list/{list_id}/task", headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        data = resp.json()
        print("[OK] Tarefa criada com sucesso!")
        print(f"    ID: {data.get('id')}")
        print(f"    Nome: {data.get('name')}")
        print(f"    URL: {data.get('url')}")
        return data.get("id")
    else:
        print(f"[X] Erro ao criar tarefa: HTTP {resp.status_code} - {resp.text}", file=sys.stderr)
        sys.exit(1)


def update_status(args):
    headers = get_headers(args.api_key)
    payload = {"status": args.status}
    resp = requests.put(f"{CLICKUP_BASE_URL}/task/{args.task_id}", headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        print(f"[OK] Status da tarefa {args.task_id} atualizado para '{args.status}'")
    else:
        print(f"[X] Erro ao atualizar status: HTTP {resp.status_code} - {resp.text}", file=sys.stderr)
        sys.exit(1)


def sync_spec(args):
    """
    Lê um arquivo de especificação markdown (docs/specs/*.md)
    e cria uma tarefa principal (Épico/Story) e subtarefas baseadas nas seções.
    """
    headers = get_headers(args.api_key)
    list_id = args.list_id or os.getenv("CLICKUP_LIST_ID")
    if not list_id:
        print("ERRO: CLICKUP_LIST_ID não fornecido.", file=sys.stderr)
        sys.exit(1)

    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"ERRO: Spec '{args.spec_file}' não encontrada.", file=sys.stderr)
        sys.exit(1)

    content = spec_path.read_text(encoding="utf-8")
    
    # Extrair título principal
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else spec_path.stem

    # Criar Tarefa Principal (Épico/Feature)
    main_desc = f"**Especificação SDD associada:** `{spec_path.name}`\n\n" + content[:3000]
    parent_payload = {
        "name": f"[SPEC] {title}",
        "description": main_desc,
        "markdown_content": main_desc,
        "tags": ["sdd-spec", "epic"]
    }
    
    resp_parent = requests.post(f"{CLICKUP_BASE_URL}/list/{list_id}/task", headers=headers, json=parent_payload)
    if resp_parent.status_code not in [200, 201]:
        print(f"Erro ao criar tarefa principal da spec: {resp_parent.text}", file=sys.stderr)
        sys.exit(1)

    parent_id = resp_parent.json().get("id")
    print(f"[OK] Tarefa Principal criada: {title} (ID: {parent_id})")

    # Extrair tarefas/subtarefas da seção de tarefas ou checklists
    # Procura por linhas como "- [ ] Tarefa tal" ou "### Tarefa"
    tasks = re.findall(r"-\s*\[[\s\w]*\]\s*(.+)", content)
    if not tasks:
        # Tentar subtítulos de nível 3 ou 4 na seção de decomposição
        tasks = re.findall(r"###+\s+(.+)", content)

    for subtask_name in tasks:
        sub_payload = {
            "name": subtask_name.strip(),
            "parent": parent_id,
            "tags": ["subtask", "tdd"]
        }
        r_sub = requests.post(f"{CLICKUP_BASE_URL}/list/{list_id}/task", headers=headers, json=sub_payload)
        if r_sub.status_code in [200, 201]:
            print(f"   - Subtarefa criada: {subtask_name.strip()}")


def main():
    parser = argparse.ArgumentParser(description="CLI de Sincronização ClickUp para o projeto SIGAAS.")
    parser.add_argument("--api-key", help="ClickUp API Key (sobrescreve .env)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # test-connection
    subparsers.add_parser("test-connection", help="Testa conectividade e lista Workspaces/Listas")

    # import-csv
    sub_import = subparsers.add_parser("import-csv", help="Importa tarefas de um arquivo CSV")
    sub_import.add_argument("csv_file", help="Caminho do arquivo CSV")
    sub_import.add_argument("--list-id", help="ID da Lista do ClickUp")

    # create-task
    sub_create = subparsers.add_parser("create-task", help="Cria uma nova tarefa")
    sub_create.add_argument("--name", required=True, help="Nome da tarefa")
    sub_create.add_argument("--description", help="Descrição da tarefa")
    sub_create.add_argument("--status", help="Status da tarefa")
    sub_create.add_argument("--tags", help="Tags separadas por vírgula")
    sub_create.add_argument("--parent", help="ID da tarefa pai (para subtarefas)")
    sub_create.add_argument("--list-id", help="ID da Lista do ClickUp")

    # update-status
    sub_up = subparsers.add_parser("update-status", help="Atualiza o status de uma tarefa")
    sub_up.add_argument("--task-id", required=True, help="ID da tarefa")
    sub_up.add_argument("--status", required=True, help="Novo status")

    # sync-spec
    sub_sync = subparsers.add_parser("sync-spec", help="Gera Épico e Subtarefas a partir de uma Spec SDD")
    sub_sync.add_argument("spec_file", help="Caminho do arquivo de spec .md")
    sub_sync.add_argument("--list-id", help="ID da Lista do ClickUp")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "test-connection": test_connection,
        "import-csv": import_csv,
        "create-task": create_task,
        "update-status": update_status,
        "sync-spec": sync_spec
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)


if __name__ == "__main__":
    main()
