"""Chapter file I/O, shared by the bible builder and the chapter pipeline."""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"


def list_chapter_numbers(book_id: str) -> list[int]:
    book_dir = INPUT_DIR / book_id
    if not book_dir.is_dir():
        raise FileNotFoundError(f"No such input directory: {book_dir}")
    return sorted(int(p.stem) for p in book_dir.glob("*.md") if p.stem.isdigit())


def read_chapter_text(book_id: str, chapter_no: int) -> str:
    return (INPUT_DIR / book_id / f"{chapter_no}.md").read_text(encoding="utf-8")


def split_paragraphs(chapter_text: str) -> list[str]:
    """Split on blank lines, dropping the leading "# N." heading so paragraph
    numbering starts at real content — this numbering is what the model cites
    as the image insertion point."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", chapter_text) if b.strip()]
    if blocks and re.match(r"^#\s*\d+\.?\s*$", blocks[0]):
        blocks = blocks[1:]
    return blocks


def numbered_paragraphs(paragraphs: list[str]) -> str:
    return "\n\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs, start=1))
