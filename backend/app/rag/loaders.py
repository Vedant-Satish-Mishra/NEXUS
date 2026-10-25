"""
NEXUS Document Loaders and Parsers (Milestone 3)
Step 3.C.1 — Parsers for PDF, DOCX, PPTX, XLSX, CSV, Markdown, text, and code.
Includes magic-byte sniffing, size limits, page caps, and safe error handling.
"""

import csv
from dataclasses import dataclass, field
import io
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Core parsers
import pypdf
import docx
import pptx
import openpyxl

MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_PAGES = 200
MAX_SHEET_ROWS = 1000


class ParseError(Exception):
    """User-safe parsing exception."""
    pass


@dataclass
class PageContent:
    number: int
    text: str
    needs_ocr: bool = False


@dataclass
class ParsedDocument:
    pages: List[PageContent]
    filename: str
    extension: str
    topic: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)


@dataclass
class LoadedDocument:
    content: str
    source: str
    filename: str
    extension: str
    topic: str
    language: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


def sniff_magic_bytes(path: Path, expected_ext: str):
    """Validates file magic header bytes against the declared extension."""
    with open(path, "rb") as f:
        header = f.read(16)

    ext = expected_ext.lower()
    if ext == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise ParseError(f"File '{path.name}' does not match standard PDF header magic bytes.")
    elif ext in [".docx", ".pptx", ".xlsx"]:
        if not header.startswith(b"PK\x03\x04"):
            raise ParseError(f"File '{path.name}' does not match standard Office OpenXML (ZIP) magic bytes.")


# -----------------------------------------------------------------------------
# Parser Functions
# -----------------------------------------------------------------------------

def parse_pdf(path: Path) -> ParsedDocument:
    """Parses PDF text per page. Flags pages without text for OCR. Rejects encrypted PDFs."""
    sniff_magic_bytes(path, ".pdf")
    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            raise ParseError(f"PDF '{path.name}' is password-encrypted and cannot be indexed.")

        pages: List[PageContent] = []
        for idx, page in enumerate(reader.pages[:MAX_PAGES]):
            text = page.extract_text() or ""
            text_clean = text.strip()
            needs_ocr = len(text_clean) < 20  # Flag if empty or minimal text layer
            pages.append(PageContent(number=idx + 1, text=text_clean, needs_ocr=needs_ocr))

        topic = path.stem.replace("_", " ").title()
        return ParsedDocument(
            pages=pages,
            filename=path.name,
            extension=".pdf",
            topic=topic,
            source=str(path),
            metadata={"total_pages": len(pages), "file_size": path.stat().st_size}
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Failed to parse PDF document '{path.name}': {str(exc)}")


def parse_docx(path: Path) -> ParsedDocument:
    """Parses Word DOCX documents: headings, paragraphs, and tables as markdown."""
    sniff_magic_bytes(path, ".docx")
    try:
        doc = docx.Document(str(path))
        lines: List[str] = []

        # Paragraphs and headings
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style and p.style.name.lower().startswith("heading"):
                lines.append(f"### {text}")
            else:
                lines.append(text)

        # Tables to markdown
        for table in doc.tables:
            table_lines = []
            for r_idx, row in enumerate(table.rows):
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                row_str = "| " + " | ".join(cells) + " |"
                table_lines.append(row_str)
                if r_idx == 0:
                    table_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
            if table_lines:
                lines.append("\n" + "\n".join(table_lines) + "\n")

        full_body = "\n\n".join(lines)
        topic = path.stem.replace("_", " ").title()
        page = PageContent(number=1, text=full_body, needs_ocr=False)
        return ParsedDocument(
            pages=[page],
            filename=path.name,
            extension=".docx",
            topic=topic,
            source=str(path),
            metadata={"total_pages": 1, "file_size": path.stat().st_size}
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Failed to parse DOCX document '{path.name}': {str(exc)}")


def parse_pptx(path: Path) -> ParsedDocument:
    """Parses PowerPoint PPTX slides: titles, shapes, notes, tables."""
    sniff_magic_bytes(path, ".pptx")
    try:
        prs = pptx.Presentation(str(path))
        pages: List[PageContent] = []

        for idx, slide in enumerate(prs.slides):
            if idx >= MAX_PAGES:
                break
            slide_lines: List[str] = []
            title = ""
            if slide.shapes.title and slide.shapes.title.text:
                title = slide.shapes.title.text.strip()
                slide_lines.append(f"## Slide {idx + 1}: {title}")
            else:
                slide_lines.append(f"## Slide {idx + 1}")

            for shape in slide.shapes:
                if shape.has_text_frame and shape != slide.shapes.title:
                    for para in shape.text_frame.paragraphs:
                        txt = para.text.strip()
                        if txt:
                            slide_lines.append(txt)

            # Slide notes
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    slide_lines.append(f"**Presenter Notes:** {notes}")

            slide_text = "\n".join(slide_lines)
            pages.append(PageContent(number=idx + 1, text=slide_text, needs_ocr=len(slide_text) < 15))

        topic = path.stem.replace("_", " ").title()
        return ParsedDocument(
            pages=pages,
            filename=path.name,
            extension=".pptx",
            topic=topic,
            source=str(path),
            metadata={"total_pages": len(pages), "file_size": path.stat().st_size}
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Failed to parse PPTX presentation '{path.name}': {str(exc)}")


def parse_xlsx(path: Path) -> ParsedDocument:
    """Parses Excel XLSX sheets: renders rows as 'Header: value' lines."""
    sniff_magic_bytes(path, ".xlsx")
    try:
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        pages: List[PageContent] = []

        for sheet_idx, sheet_name in enumerate(wb.sheetnames):
            sheet = wb[sheet_name]
            lines = [f"# Sheet: {sheet_name}"]
            headers: List[str] = []

            for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                if r_idx >= MAX_SHEET_ROWS:
                    lines.append(f"... [Truncated at {MAX_SHEET_ROWS} rows]")
                    break

                str_cells = [str(c).strip() if c is not None else "" for c in row]
                if not any(str_cells):
                    continue

                if not headers:
                    headers = str_cells
                    continue

                row_parts = []
                for h, val in zip(headers, str_cells):
                    if h and val:
                        row_parts.append(f"{h}: {val}")
                if row_parts:
                    lines.append(", ".join(row_parts))

            sheet_text = "\n".join(lines)
            pages.append(PageContent(number=sheet_idx + 1, text=sheet_text, needs_ocr=False))

        wb.close()
        topic = path.stem.replace("_", " ").title()
        return ParsedDocument(
            pages=pages,
            filename=path.name,
            extension=".xlsx",
            topic=topic,
            source=str(path),
            metadata={"total_pages": len(pages), "file_size": path.stat().st_size}
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Failed to parse XLSX workbook '{path.name}': {str(exc)}")


def parse_csv(path: Path) -> ParsedDocument:
    """Parses CSV files with header-aware rows."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers: List[str] = []
            lines = [f"# CSV: {path.name}"]

            for r_idx, row in enumerate(reader):
                if r_idx >= MAX_SHEET_ROWS:
                    lines.append(f"... [Truncated at {MAX_SHEET_ROWS} rows]")
                    break
                str_cells = [c.strip() for c in row]
                if not any(str_cells):
                    continue
                if not headers:
                    headers = str_cells
                    continue

                row_parts = [f"{h}: {v}" for h, v in zip(headers, str_cells) if h and v]
                if row_parts:
                    lines.append(", ".join(row_parts))

        full_text = "\n".join(lines)
        topic = path.stem.replace("_", " ").title()
        return ParsedDocument(
            pages=[PageContent(number=1, text=full_text, needs_ocr=False)],
            filename=path.name,
            extension=".csv",
            topic=topic,
            source=str(path),
            metadata={"total_pages": 1, "file_size": path.stat().st_size}
        )
    except Exception as exc:
        raise ParseError(f"Failed to parse CSV file '{path.name}': {str(exc)}")


def parse_text_or_markdown(path: Path) -> ParsedDocument:
    """Parses markdown or plain text files."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        topic = path.stem.replace("_", " ").title()
        return ParsedDocument(
            pages=[PageContent(number=1, text=content, needs_ocr=False)],
            filename=path.name,
            extension=path.suffix.lower(),
            topic=topic,
            source=str(path),
            metadata={"total_pages": 1, "file_size": path.stat().st_size}
        )
    except Exception as exc:
        raise ParseError(f"Failed to read text file '{path.name}': {str(exc)}")


# -----------------------------------------------------------------------------
# Parser Registry
# -----------------------------------------------------------------------------

PARSER_REGISTRY: Dict[str, Callable[[Path], ParsedDocument]] = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".pptx": parse_pptx,
    ".xlsx": parse_xlsx,
    ".csv": parse_csv,
    ".txt": parse_text_or_markdown,
    ".md": parse_text_or_markdown,
    ".markdown": parse_text_or_markdown,
    ".py": parse_text_or_markdown,
    ".java": parse_text_or_markdown,
    ".js": parse_text_or_markdown,
    ".ts": parse_text_or_markdown,
    ".html": parse_text_or_markdown,
    ".css": parse_text_or_markdown,
    ".sql": parse_text_or_markdown,
}


def parse_file(path_str: str) -> ParsedDocument:
    """Main entry point to parse any supported file format."""
    path = Path(path_str)
    if not path.is_file():
        raise ParseError(f"File not found: {path_str}")

    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ParseError(f"File size ({size / (1024*1024):.1f} MB) exceeds maximum allowed limit of 25 MB.")

    ext = path.suffix.lower()
    parser_fn = PARSER_REGISTRY.get(ext)
    if not parser_fn:
        raise ParseError(f"Unsupported file format '{ext}'. Supported: {list(PARSER_REGISTRY.keys())}")

    return parser_fn(path)


# Backward compatibility adapter for Step 2.C.1 chunking functions
def load_file(path_str: str) -> Optional[LoadedDocument]:
    try:
        parsed = parse_file(path_str)
        return LoadedDocument(
            content=parsed.full_text,
            source=parsed.source,
            filename=parsed.filename,
            extension=parsed.extension,
            topic=parsed.topic,
            metadata={k: str(v) for k, v in parsed.metadata.items()}
        )
    except Exception:
        return None
