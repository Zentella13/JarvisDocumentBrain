from pathlib import Path

from app.services.document_service import extract_text


def test_extract_text_from_plain_text(tmp_path: Path) -> None:
    sample_file = tmp_path / "notes.txt"
    sample_file.write_text("Hello Jarvis Document Brain", encoding="utf-8")

    text = extract_text(sample_file)

    assert "Jarvis Document Brain" in text
