"""CLI regression tests."""

from typer.testing import CliRunner

from portchecker import cli


def test_fav_list_empty_json(monkeypatch) -> None:
    """Empty favorites remain valid JSON for native app consumers."""
    monkeypatch.setattr(cli, "load_favorites", lambda: [])

    result = CliRunner().invoke(cli.app, ["fav-list", "--json"])

    assert result.exit_code == 0
    assert result.stdout == "[]\n"
