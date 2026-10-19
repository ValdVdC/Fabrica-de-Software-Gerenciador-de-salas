"""
Testes unitarios TDD para o servico de exportacao CSV (Sprint 07 - Historia 4).
Cobre:
- Presenca de UTF-8 BOM (\ufeff / 0xEF 0xBB 0xBF)
- Cabecalhos HTTP Content-Type (text/csv; charset=utf-8) e Content-Disposition (.csv)
- Sanitizacao contra CSV Injection (=, +, -, @, tab, cr e espacos precedentes)
- Teto maximo de 10000 linhas de dados em streaming
"""

import asyncio
import csv
import io
import pytest

from app.services.export_service import (
    MAX_EXPORT_ROWS,
    gerar_csv_streaming,
    sanitizar_celula_csv,
)


async def _ler_streaming_response(response) -> bytes:
    chunks = []
    async for chunk in response.body_iterator:
        if isinstance(chunk, str):
            chunks.append(chunk.encode("utf-8"))
        else:
            chunks.append(chunk)
    return b"".join(chunks)


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("=SUM(A1:A2)", "'=SUM(A1:A2)"),
        ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
        ("-2+3", "'-2+3"),
        ("@SUM(1+1)", "'@SUM(1+1)"),
        ("\t=1+1", "'\t=1+1"),
        ("\r=1+1", "'\r=1+1"),
        ("  =cmd()", "'  =cmd()"),
        ("Texto normal", "Texto normal"),
        ("", ""),
        (None, ""),
        (42, "42"),
        (75.5, "75.5"),
    ],
)
def test_sanitizar_celula_csv_previne_formula_injection(entrada, esperado):
    """Garante que celulas iniciadas por =, +, -, @, tab ou CR recebam apostrofo."""
    assert sanitizar_celula_csv(entrada) == esperado


def test_gerar_csv_streaming_cabecalhos_bom_e_conteudo():
    """Valida Content-Type, Content-Disposition, UTF-8 BOM e serializacao de linhas."""
    dados = [
        {"sala": "A-101", "bloco": "A", "capacidade": 40, "obs": "=HYPERLINK(\"http://evil\")"},
        {"sala": "B-202", "bloco": "B", "capacidade": 60, "obs": "Sala regular"},
    ]
    colunas = ["sala", "bloco", "capacidade", "obs"]

    resp = gerar_csv_streaming(dados, colunas, nome_arquivo="ocupacao_salas")
    assert resp.media_type == "text/csv; charset=utf-8"
    assert "text/csv" in resp.headers["content-type"]
    assert "charset=utf-8" in resp.headers["content-type"]
    assert 'attachment; filename="ocupacao_salas.csv"' == resp.headers["content-disposition"]

    raw_bytes = asyncio.run(_ler_streaming_response(resp))
    assert raw_bytes.startswith(b"\xef\xbb\xbf")

    texto_sem_bom = raw_bytes.decode("utf-8-sig")
    leitor = list(csv.DictReader(io.StringIO(texto_sem_bom)))
    assert len(leitor) == 2
    assert leitor[0]["sala"] == "A-101"
    assert leitor[0]["obs"] == "'=HYPERLINK(\"http://evil\")"
    assert leitor[1]["sala"] == "B-202"
    assert leitor[1]["obs"] == "Sala regular"


def test_gerar_csv_streaming_respeita_teto_10000_linhas():
    """Quando o gerador possui mais de 10000 registros, exporta no maximo 10000 linhas de dados."""
    assert MAX_EXPORT_ROWS == 10000

    gerador_excedente = (
        {"id": i, "valor": f"item_{i}"} for i in range(1, MAX_EXPORT_ROWS + 501)
    )
    resp = gerar_csv_streaming(gerador_excedente, ["id", "valor"], nome_arquivo="limite.csv")
    raw_bytes = asyncio.run(_ler_streaming_response(resp))
    texto = raw_bytes.decode("utf-8-sig")

    linhas = texto.strip().splitlines()
    # 1 linha de cabecalho + 10000 linhas de dados
    assert len(linhas) == MAX_EXPORT_ROWS + 1
    leitor = list(csv.DictReader(io.StringIO(texto)))
    assert len(leitor) == MAX_EXPORT_ROWS
    assert leitor[0]["id"] == "1"
    assert leitor[-1]["id"] == str(MAX_EXPORT_ROWS)
