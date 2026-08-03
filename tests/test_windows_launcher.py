"""Static regression checks for the Windows launcher contract."""

from pathlib import Path


LAUNCHER = Path(__file__).resolve().parents[1] / "run-ai-blog.bat"


def test_windows_launcher_preserves_linux_schedule_and_runtime_commands():
    content = LAUNCHER.read_text(encoding="utf-8")

    assert "AI Blog - RSS Refresh" in content
    assert "AI Blog - Post Generation" in content
    assert "$refreshStart = $now.Date.AddMinutes(5)" in content
    assert "$generationStart = $now.Date.AddMinutes(12)" in content
    assert "-RepetitionInterval (New-TimeSpan -Hours 1)" in content
    assert "[DateTime]::UtcNow" in content
    assert "[DayOfWeek]::Monday" in content
    assert "[DayOfWeek]::Wednesday" in content
    assert "[DayOfWeek]::Friday" in content
    assert "[TimeSpan]::Parse('14:12:00')" in content
    assert "blog.generate_helpers check-today" in content
    assert "last-generation-attempt-utc.txt" in content
    assert "Generation was already evaluated" in content
    assert "blog.refresh_sources" in content
    assert "./blog/generate.sh" in content
    assert "uvicorn.run('api.main:app'" in content


def test_windows_launcher_is_idempotent_and_bounded():
    content = LAUNCHER.read_text(encoding="utf-8")

    assert content.count("Register-ScheduledTask") >= 3
    assert content.count("call :install_scheduled_tasks install") == 1
    assert "$quote = [char]34" in content
    assert "$quote + $quote + $script + $quote" in content
    assert "-Force | Out-Null" in content
    assert "-StartWhenAvailable" in content
    assert "-MultipleInstances IgnoreNew" in content
    assert "New-TimeSpan -Minutes 15" in content
    assert "New-TimeSpan -Minutes 45" in content


def test_default_and_server_modes_do_not_install_scheduled_tasks():
    content = LAUNCHER.read_text(encoding="utf-8")

    default_block = content.split("\n:default\n", 1)[1].split("\n:check\n", 1)[0]
    server_block = content.split("\n:server\n", 1)[1].split(
        "\n:check_server_requirements\n", 1
    )[0]

    assert "install_scheduled_tasks" not in default_block
    assert "install_scheduled_tasks" not in server_block
    assert "call :check_server_requirements" in default_block
    assert "call :check_server_requirements" in server_block
