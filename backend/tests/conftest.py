"""
Configuração do pytest para o ambiente de testes do SIGAAS.
"""

import sys
from pathlib import Path

# Adiciona a raiz do projeto e backend ao sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

for directory in [root_dir, backend_dir]:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
