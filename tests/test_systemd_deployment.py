"""Static regression checks for the Linux production deployment contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_SERVICE = ROOT / "systemd" / "blog-api.service"
INSTALLER = ROOT / "systemd" / "install.sh"


def test_api_service_runs_fastapi_as_the_blog_user():
    content = API_SERVICE.read_text(encoding="utf-8")

    assert "Type=simple" in content
    assert "User=blog" in content
    assert "Group=blog" in content
    assert "EnvironmentFile=/etc/blog-backend/env" in content
    assert "uvicorn.run('api.main:app'" in content
    assert "host=settings.api_host" in content
    assert "port=settings.api_port" in content
    assert "Restart=on-failure" in content
    assert "WantedBy=multi-user.target" in content


def test_installer_installs_and_documents_starting_the_api_service():
    content = INSTALLER.read_text(encoding="utf-8")

    assert "cat > /etc/systemd/system/blog-api.service" in content
    assert "WorkingDirectory=$PROJECT_PATH" in content
    assert "ExecStart=$PROJECT_PATH/.venv/bin/python" in content
    assert (
        "systemctl enable --now blog-api.service blog-refresh.timer "
        "blog-generator.timer"
    ) in content
