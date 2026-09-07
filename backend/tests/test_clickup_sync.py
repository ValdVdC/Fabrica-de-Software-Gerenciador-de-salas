"""
Testes de contrato para o utilitario scripts/clickup_sync.py.
Valida o formato dos payloads enviados para a API do ClickUp.
"""

import argparse
from unittest.mock import MagicMock, patch
from scripts import clickup_sync


def test_create_task_payload_contract():
    """Valida que create_task envia markdown_content e preserva formatacao Markdown."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "mock_task_123",
        "name": "Tarefa Teste",
        "url": "https://app.clickup.com/t/mock_task_123"
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        args = argparse.Namespace(
            api_key="pk_test_123",
            list_id="999999",
            name="Tarefa Teste",
            description="**Descricao em negrito** com `codigo` e lista:\n- Item 1\n- Item 2",
            status="to do",
            tags="sdd,backend",
            parent=None
        )

        task_id = clickup_sync.create_task(args)

        assert task_id == "mock_task_123"
        assert mock_post.called
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]

        assert "markdown_content" in payload
        assert "markdown_description" not in payload
        assert "**Descricao em negrito**" in payload["markdown_content"]
        assert "`codigo`" in payload["markdown_content"]
        assert payload["tags"] == ["sdd", "backend"]


def test_sync_spec_parent_task_payload_contract(tmp_path):
    """Valida que sync_spec gera tarefa principal com markdown_content e formatação preservada."""
    mock_spec = tmp_path / "sprint_test_spec.md"
    mock_spec.write_text(
        "# [SPEC-999] Teste Spec\n\n## 1. Contexto\nTexto em **Markdown** com listas:\n- [ ] Subtarefa 1\n",
        encoding="utf-8"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "mock_parent_456"}

    with patch("requests.post", return_value=mock_response) as mock_post:
        args = argparse.Namespace(
            api_key="pk_test_123",
            list_id="999999",
            spec_file=str(mock_spec)
        )

        clickup_sync.sync_spec(args)

        assert mock_post.called
        first_call = mock_post.call_args_list[0]
        parent_payload = first_call[1]["json"]

        assert "markdown_content" in parent_payload
        assert "markdown_description" not in parent_payload
        assert "**Markdown**" in parent_payload["markdown_content"]
        assert "sdd-spec" in parent_payload["tags"]
