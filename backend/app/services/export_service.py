"""Servico de exportacao CSV em streaming com UTF-8 BOM, sanitizacao e teto de 10000 linhas."""

import csv
import io
import re
from itertools import islice
from typing import Any, Iterable, Iterator, Mapping, Sequence
from fastapi.responses import StreamingResponse

MAX_EXPORT_ROWS = 10000
UTF8_BOM = "\ufeff"
PREFIXOS_PERIGOSOS_CSV = ("=", "+", "-", "@", "\t", "\r")
_PADRAO_NOME_ARQUIVO = re.compile(r"[^a-zA-Z0-9_.-]")


def sanitizar_celula_csv(valor: Any) -> str:
    """Converte valor para string e neutraliza formulas de planilha (CSV Injection)."""
    if valor is None:
        return ""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return str(valor)
    texto = str(valor)
    if texto and (texto.startswith(PREFIXOS_PERIGOSOS_CSV) or texto.lstrip().startswith(PREFIXOS_PERIGOSOS_CSV)):
        return f"'{texto}"
    return texto


def _iterar_linhas_csv(linhas: Iterable[Mapping[str, Any]], colunas: Sequence[str]) -> Iterator[str]:
    """Gera o stream CSV linha a linha com UTF-8 BOM e teto de MAX_EXPORT_ROWS."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    buffer.write(UTF8_BOM)
    writer.writerow(colunas)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for registro in islice(linhas, MAX_EXPORT_ROWS):
        writer.writerow([sanitizar_celula_csv(registro.get(col)) for col in colunas])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def gerar_csv_streaming(
    linhas: Iterable[Mapping[str, Any]],
    colunas: Sequence[str],
    nome_arquivo: str = "exportacao.csv",
) -> StreamingResponse:
    """Retorna StreamingResponse CSV com UTF-8 BOM e Content-Disposition seguro."""
    nome_limpo = _PADRAO_NOME_ARQUIVO.sub("_", nome_arquivo)
    if not nome_limpo.lower().endswith(".csv"):
        nome_limpo = f"{nome_limpo}.csv"
    return StreamingResponse(
        _iterar_linhas_csv(linhas, colunas),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome_limpo}"'},
    )
