"""
Testes TDD para validacao da documentacao interativa OpenAPI/Swagger/ReDoc e versao RC.
"""

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_TAGS = [
    "Autenticacao",
    "Campi",
    "Usuarios",
    "Cursos",
    "Disciplinas",
    "Salas",
    "Equipamentos",
    "Turmas",
    "Matriculas",
    "Horarios",
    "Motor",
    "Alocacao",
    "Sugestoes",
    "IA Preditiva",
    "Logs",
    "Dashboard",
    "Relatorios",
    "Health",
    "Root",
]

CRITICAL_ROUTES = [
    ("post", "/api/v1/auth/login"),
    ("get", "/api/v1/auth/me"),
    ("post", "/api/v1/alocacao/otimizar"),
    ("post", "/api/v1/alocacao/benchmark"),
    ("get", "/api/v1/sugestoes"),
    ("patch", "/api/v1/sugestoes/{sugestao_id}"),
    ("post", "/api/v1/sugestoes/analisar"),
    ("post", "/api/v1/ia/analisar"),
    ("get", "/api/v1/motor/status"),
    ("post", "/api/v1/motor/teste-integracao"),
    ("get", "/api/v1/dashboard/resumo"),
    ("get", "/api/v1/dashboard/ocupacao"),
]

EXPECTED_ERROR_RESPONSES = {
    ("post", "/api/v1/auth/login"): {"401", "403"},
    ("get", "/api/v1/auth/me"): {"401", "403"},
    ("post", "/api/v1/alocacao/otimizar"): {"400", "401", "403", "500", "503"},
    ("post", "/api/v1/alocacao/benchmark"): {"401", "403", "503"},
    ("get", "/api/v1/sugestoes"): {"401", "403"},
    ("patch", "/api/v1/sugestoes/{sugestao_id}"): {"400", "401", "403", "404", "409"},
    ("post", "/api/v1/sugestoes/analisar"): {"401", "403"},
    ("post", "/api/v1/ia/analisar"): {"401", "403"},
    ("post", "/api/v1/motor/teste-integracao"): {"400", "503"},
    ("get", "/api/v1/dashboard/resumo"): {"401", "403"},
    ("get", "/api/v1/dashboard/ocupacao"): {"401", "403"},
}

PROTECTED_CRITICAL_ROUTES = [
    ("get", "/api/v1/auth/me"),
    ("post", "/api/v1/alocacao/otimizar"),
    ("post", "/api/v1/alocacao/benchmark"),
    ("get", "/api/v1/sugestoes"),
    ("patch", "/api/v1/sugestoes/{sugestao_id}"),
    ("post", "/api/v1/sugestoes/analisar"),
    ("post", "/api/v1/ia/analisar"),
    ("get", "/api/v1/dashboard/resumo"),
    ("get", "/api/v1/dashboard/ocupacao"),
]


def test_openapi_json_version_metadata_and_tags():
    with TestClient(app) as client:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        info = schema.get("info", {})
        assert info.get("version") == "1.0.0-rc.1"
        assert info.get("description")
        assert "SIGAAS" in info["description"]
        assert info.get("contact")
        assert info.get("license")

        tags_by_name = {tag["name"]: tag for tag in schema.get("tags", [])}
        for tag_name in EXPECTED_TAGS:
            assert tag_name in tags_by_name, f"Tag '{tag_name}' ausente em openapi_tags"
            assert tags_by_name[tag_name].get("description"), f"Tag '{tag_name}' sem descricao"

        # Validacao anti-drift: toda tag usada nas rotas deve estar declarada em openapi_tags
        used_tags = set()
        for methods in schema.get("paths", {}).values():
            for operation in methods.values():
                if isinstance(operation, dict):
                    used_tags.update(operation.get("tags", []))
        assert used_tags.issubset(set(tags_by_name.keys()))


def test_swagger_and_redoc_endpoints_return_200():
    with TestClient(app) as client:
        docs_resp = client.get("/api/v1/docs")
        assert docs_resp.status_code == 200
        assert "text/html" in docs_resp.headers.get("content-type", "")
        assert "/api/v1/openapi.json" in docs_resp.text

        redoc_resp = client.get("/api/v1/redoc")
        assert redoc_resp.status_code == 200
        assert "text/html" in redoc_resp.headers.get("content-type", "")
        assert "/api/v1/openapi.json" in redoc_resp.text

        redirect_resp = client.get("/redoc", follow_redirects=False)
        assert redirect_resp.status_code == 307
        assert redirect_resp.headers["location"] == "/api/v1/redoc"


def test_openapi_security_scheme_bearer_oauth2_present():
    with TestClient(app) as client:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        security_schemes = schema.get("components", {}).get("securitySchemes", {})
        assert security_schemes, "components.securitySchemes nao pode estar vazio"

        has_oauth_or_bearer = any(
            scheme.get("type") in ("oauth2", "http")
            for scheme in security_schemes.values()
        )
        assert has_oauth_or_bearer, "Esquema Bearer/OAuth2 ausente em securitySchemes"

        paths = schema.get("paths", {})
        for method, path in PROTECTED_CRITICAL_ROUTES:
            operation = paths[path][method]
            assert operation.get("security"), f"Seguranca ausente em {method.upper()} {path}"


def test_critical_routes_have_summary_description_and_responses():
    with TestClient(app) as client:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        paths = response.json().get("paths", {})

        for method, path in CRITICAL_ROUTES:
            assert path in paths, f"Rota '{path}' ausente no schema OpenAPI"
            operation = paths[path].get(method)
            assert operation is not None, f"Metodo '{method}' ausente na rota '{path}'"
            assert operation.get("summary"), f"summary vazio em {method.upper()} {path}"
            assert operation.get("description"), f"description vazio em {method.upper()} {path}"
            responses = operation.get("responses", {})
            assert "200" in responses, f"Resposta 200 ausente em {method.upper()} {path}"


def test_protected_routes_document_error_responses():
    with TestClient(app) as client:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        paths = response.json().get("paths", {})

        for (method, path), expected_codes in EXPECTED_ERROR_RESPONSES.items():
            documented_codes = set(paths[path][method]["responses"].keys())
            missing = expected_codes - documented_codes
            assert not missing, f"Codigos {missing} ausentes em {method.upper()} {path}"
