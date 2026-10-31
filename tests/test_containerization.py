"""Tests for production containerization configurations.

Validates Dockerfile, .dockerignore, and docker-compose.yml.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_multi_stage_structure():
    """Verify Dockerfile exists and enforces a modern, secure multi-stage build."""
    dockerfile_path = REPO_ROOT / "Dockerfile"
    assert dockerfile_path.is_file(), "Dockerfile must exist in repo root"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage validation
    assert "AS builder" in content, "Dockerfile must define an isolated builder stage"
    assert "AS runner" in content, "Dockerfile must define a minimal runner stage"

    # Builder stage contains build dependencies
    assert "build-essential" in content or "gcc" in content
    assert "python -m venv /opt/venv" in content

    # Runner stage minimalism & security
    runner_part = content.split("AS runner")[-1]

    # Verify build tools are NOT installed in runner stage
    assert "build-essential" not in runner_part
    assert "gcc" not in runner_part

    # Verify non-root user
    assert "useradd" in runner_part
    assert "USER coachflow" in runner_part

    # Verify virtualenv copy from builder
    assert "COPY --from=builder" in runner_part
    assert "/opt/venv" in runner_part

    # Verify healthcheck endpoint
    assert "HEALTHCHECK" in runner_part
    assert "/health" in runner_part

    # Verify uvicorn entrypoint
    assert "uvicorn" in runner_part
    assert "coach_flow.main:app" in runner_part


def test_dockerignore_configuration():
    """Verify .dockerignore excludes virtualenv & sensitive files while retaining build files."""
    dockerignore_path = REPO_ROOT / ".dockerignore"
    assert dockerignore_path.is_file(), ".dockerignore must exist in repo root"

    lines = [
        line.strip()
        for line in dockerignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    # Critical exclusions
    assert ".git/" in lines or ".git" in lines
    assert ".venv/" in lines or ".venv" in lines
    assert "__pycache__/" in lines or "__pycache__" in lines
    assert ".pytest_cache/" in lines or ".pytest_cache" in lines
    assert ".ruff_cache/" in lines or ".ruff_cache" in lines
    assert ".env" in lines
    assert "postgres_data/" in lines or "postgres_data" in lines

    # Critical inclusions (whitelisted for Hatchling packaging)
    assert "!README.md" in lines
    assert "!LICENSE" in lines


def test_docker_compose_syntax_and_services():
    """Verify docker-compose.yml is valid YAML and configures app and PostgreSQL db properly."""
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.is_file(), "docker-compose.yml must exist in repo root"

    with compose_path.open("r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    assert "services" in compose_data
    services = compose_data["services"]

    # Verify app service
    assert "app" in services
    app_svc = services["app"]
    assert "build" in app_svc
    assert "8000:8000" in app_svc.get("ports", [])
    assert app_svc.get("depends_on", {}).get("db", {}).get("condition") == "service_healthy"

    # Verify db service
    assert "db" in services
    db_svc = services["db"]
    assert "postgres" in db_svc.get("image", "")
    assert "healthcheck" in db_svc
    assert "pg_isready" in str(db_svc["healthcheck"].get("test", []))

    # Verify volume persistence
    assert "volumes" in compose_data
    assert "postgres_data" in compose_data["volumes"]
