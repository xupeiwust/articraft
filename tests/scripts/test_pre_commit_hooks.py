from __future__ import annotations

import pytest

from scripts import pre_commit_hooks


@pytest.mark.parametrize(
    ("assignment", "label"),
    [
        ("".join(["OPENAI_API_", "KEY=sk-test-value"]), "OpenAI API key assignment"),
        ("".join(["OPENAI_API_", "KEYS=sk-test-value"]), "OpenAI API key assignment"),
        ("".join(["GEMINI_API_", "KEYS=gemini-test-value"]), "Gemini API keys assignment"),
    ],
)
def test_detect_secrets_flags_provider_key_assignments(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    assignment: str,
    label: str,
) -> None:
    path = tmp_path / "secrets.txt"
    path.write_text(f"{assignment}\n", encoding="utf-8")

    exit_code = pre_commit_hooks.detect_secrets([str(path)])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Potential secrets detected:" in output
    assert label in output


def test_detect_secrets_ignores_files_without_matches(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "clean.txt"
    path.write_text("".join(["OPENAI_API_", "KEYS = \n"]), encoding="utf-8")

    exit_code = pre_commit_hooks.detect_secrets([str(path)])

    assert exit_code == 0
    assert capsys.readouterr().out == ""
