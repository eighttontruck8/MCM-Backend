from __future__ import annotations

from pathlib import Path

import pytest

from app.demo_qr import generate_qr_svg


ENTRY_URL = "https://api.mjourney.test/entry/opaque-production-token-12345"


def test_generate_printable_svg_qr_without_plaintext_token(tmp_path: Path) -> None:
    output = tmp_path / "mjourney-entry.svg"

    generated = generate_qr_svg(ENTRY_URL, output)

    svg = output.read_text(encoding="utf-8")
    assert generated == output.resolve()
    assert "<svg" in svg
    assert "<path" in svg
    assert "<rect" in svg
    assert "opaque-production-token-12345" not in svg


def test_qr_generation_refuses_overwrite_without_force(tmp_path: Path) -> None:
    output = tmp_path / "mjourney-entry.svg"
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="--force"):
        generate_qr_svg(ENTRY_URL, output)

    generate_qr_svg(ENTRY_URL, output, force=True)
    assert "<svg" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("entry_url", "filename"),
    [
        ("http://api.mjourney.test/entry/token", "entry.svg"),
        ("https://api.mjourney.test/not-entry/token", "entry.svg"),
        ("https://api.mjourney.test/entry/short-token", "entry.svg"),
        (f"{ENTRY_URL}?customer_id=C001", "entry.svg"),
        (ENTRY_URL, "entry.png"),
    ],
)
def test_qr_generation_rejects_unsafe_input(entry_url: str, filename: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        generate_qr_svg(entry_url, tmp_path / filename)
