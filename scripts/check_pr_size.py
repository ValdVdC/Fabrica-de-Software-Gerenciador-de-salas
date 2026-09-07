#!/usr/bin/env python3
"""
scripts/check_pr_size.py - Validador de limite de diff por PR para codigo de producao.

Regra definida em AGENTS.md: Maximo de 300 a 400 linhas de codigo modificado por PR.
Ignora automaticamente documentacoes, specs, migrations e arquivos de configuracao.
"""

import sys
import subprocess
import re
from pathlib import Path

# Extensoes consideradas codigo de producao
CODE_EXTENSIONS = {
    ".py", ".c", ".h", ".ts", ".js", ".html", ".css", ".scss", ".sql"
}

# Padroes de caminhos isentos de contagem de diff
IGNORED_PATTERNS = [
    r"^docs/",
    r"^.*\.md$",
    r"^.*/migrations/.*$",
    r"^.*/alembic/versions/.*$",
    r"^\.github/",
    r"^\.agent/",
    r"^\.coderabbit\.yaml$",
    r"^.*lock.*$",
    r"^\.gitignore$",
    r"^.*\.json$",
    r"^.*\.csv$"
]


def is_ignored(path_str: str) -> bool:
    for pattern in IGNORED_PATTERNS:
        if re.search(pattern, path_str, re.IGNORECASE):
            return True
    return False


def is_code_file(path_str: str) -> bool:
    ext = Path(path_str).suffix.lower()
    return ext in CODE_EXTENSIONS


def get_diff_stats(base_ref: str = "origin/homolog") -> list[tuple[int, int, str]]:
    """
    Executa git diff --numstat contra a branch base.
    Retorna lista de (adicoes, remocoes, caminho).
    """
    cmd = ["git", "diff", "--numstat", f"{base_ref}...HEAD"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Se falhar (ex.: branch local isolada), tenta comparar com HEAD~1
    if result.returncode != 0 or not result.stdout.strip():
        cmd = ["git", "diff", "--numstat", "HEAD~1...HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True)

    stats = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            add_str, del_str, file_path = parts
            # Ignora binarios indicados por '-'
            if add_str == "-" or del_str == "-":
                continue
            stats.append((int(add_str), int(del_str), file_path))
    return stats


def main():
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/homolog"
    max_lines = int(sys.argv[2]) if len(sys.argv) > 2 else 400

    print("=" * 60)
    print(f"Auditoria de Tamanho de PR (Limite Maximo: {max_lines} linhas de codigo)")
    print(f"Base de comparacao: {base_ref}")
    print("=" * 60)

    try:
        stats = get_diff_stats(base_ref)
    except Exception as e:
        print(f"[AVISO] Nao foi possivel obter diff com {base_ref}: {e}")
        sys.exit(0)

    total_code_additions = 0
    total_code_deletions = 0
    audited_files = []

    for additions, deletions, file_path in stats:
        if is_ignored(file_path):
            print(f"[ISENTO] {file_path} (+{additions} / -{deletions})")
            continue

        if is_code_file(file_path):
            total_code_additions += additions
            total_code_deletions += deletions
            audited_files.append((file_path, additions, deletions))
            print(f"[CODIGO] {file_path}: +{additions} / -{deletions}")
        else:
            print(f"[OUTRO]  {file_path} (ignorado)")

    print("-" * 60)
    print(f"Total de Linhas de Codigo Adicionadas: {total_code_additions}")
    print(f"Total de Linhas de Codigo Removidas:   {total_code_deletions}")
    print("-" * 60)

    if total_code_additions > max_lines:
        print(f"\n[ERRO] PR reprovado: O volume de codigo modificado (+{total_code_additions} linhas)")
        print(f"       ultrapassa o limite de {max_lines} linhas estabelecido em AGENTS.md.")
        print("       Por favor, fatie esta entrega em Pull Requests menores e incrementais.\n")
        sys.exit(1)

    print(f"\n[SUCESSO] PR aprovado na auditoria de tamanho (+{total_code_additions} <= {max_lines} linhas de codigo).\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
