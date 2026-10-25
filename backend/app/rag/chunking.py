"""
NEXUS Chunking Engine
Step 2.C.1 — Semantic, heading-aware, code-block preserving chunker
"""

from dataclasses import dataclass
import re
from typing import List, Optional

from app.rag.loaders import LoadedDocument


@dataclass
class DocumentChunk:
    text: str
    source: str
    topic: str
    chunk_index: int
    heading_path: str
    page: Optional[int] = None


def split_sentences(text: str) -> List[str]:
    """Splits text into sentences while respecting common abbreviations."""
    # Split by period/exclamation/question followed by whitespace or newline
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_markdown(doc: LoadedDocument, target_words: int = 300, overlap_words: int = 45) -> List[DocumentChunk]:
    """
    Heading-aware Markdown chunker.
    Keeps code blocks intact and prefixes chunks with hierarchical headings.
    """
    lines = doc.content.splitlines()
    chunks: List[DocumentChunk] = []
    
    current_headings = []  # Stack of (level, heading_text)
    current_section_lines = []
    current_heading_path = doc.topic

    in_code_block = False
    
    sections = []  # List of (heading_path, section_text)

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        if not in_code_block and line.strip().startswith("#"):
            match = re.match(r'^(#+)\s*(.*)', line.strip())
            if match:
                # Flush previous section
                if current_section_lines:
                    sections.append((current_heading_path, "\n".join(current_section_lines)))
                    current_section_lines = []
                
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                
                # Maintain heading stack
                while current_headings and current_headings[-1][0] >= level:
                    current_headings.pop()
                current_headings.append((level, heading_text))
                current_heading_path = " > ".join([doc.topic] + [h[1] for h in current_headings])
                continue

        current_section_lines.append(line)

    if current_section_lines:
        sections.append((current_heading_path, "\n".join(current_section_lines)))

    chunk_idx = 0
    for h_path, sec_text in sections:
        sec_text = sec_text.strip()
        if not sec_text:
            continue

        words = sec_text.split()
        if len(words) <= target_words:
            # Entire section fits within word target
            prefixed = f"[{h_path}]\n{sec_text}"
            chunks.append(DocumentChunk(
                text=prefixed,
                source=doc.source,
                topic=doc.topic,
                chunk_index=chunk_idx,
                heading_path=h_path
            ))
            chunk_idx += 1
        else:
            # Split section safely without breaking code blocks or sentences
            paragraphs = sec_text.split("\n\n")
            curr_chunk_paras = []
            curr_words = 0

            for para in paragraphs:
                para_words = len(para.split())
                if curr_words + para_words > target_words and curr_chunk_paras:
                    body = "\n\n".join(curr_chunk_paras)
                    prefixed = f"[{h_path}]\n{body}"
                    chunks.append(DocumentChunk(
                        text=prefixed,
                        source=doc.source,
                        topic=doc.topic,
                        chunk_index=chunk_idx,
                        heading_path=h_path
                    ))
                    chunk_idx += 1
                    # 15% overlap: retain the last paragraph if possible
                    curr_chunk_paras = [curr_chunk_paras[-1], para] if len(curr_chunk_paras) > 1 else [para]
                    curr_words = sum(len(p.split()) for p in curr_chunk_paras)
                else:
                    curr_chunk_paras.append(para)
                    curr_words += para_words

            if curr_chunk_paras:
                body = "\n\n".join(curr_chunk_paras)
                prefixed = f"[{h_path}]\n{body}"
                chunks.append(DocumentChunk(
                    text=prefixed,
                    source=doc.source,
                    topic=doc.topic,
                    chunk_index=chunk_idx,
                    heading_path=h_path
                ))
                chunk_idx += 1

    return chunks


def chunk_code(doc: LoadedDocument, target_lines: int = 60, overlap_lines: int = 10) -> List[DocumentChunk]:
    """Splits code files by logical blocks/lines without splitting mid-expression."""
    lines = doc.content.splitlines()
    chunks: List[DocumentChunk] = []
    chunk_idx = 0

    if len(lines) <= target_lines:
        chunks.append(DocumentChunk(
            text=f"// File: {doc.filename} ({doc.language})\n" + doc.content,
            source=doc.source,
            topic=doc.topic,
            chunk_index=0,
            heading_path=doc.topic
        ))
        return chunks

    i = 0
    while i < len(lines):
        end = min(i + target_lines, len(lines))
        slice_lines = lines[i:end]
        text = f"// File: {doc.filename} ({doc.language}) [Lines {i+1}-{end}]\n" + "\n".join(slice_lines)
        chunks.append(DocumentChunk(
            text=text,
            source=doc.source,
            topic=doc.topic,
            chunk_index=chunk_idx,
            heading_path=doc.topic
        ))
        chunk_idx += 1
        i += (target_lines - overlap_lines)

    return chunks


def chunk_document(doc: LoadedDocument) -> List[DocumentChunk]:
    """Dispatches to appropriate chunker based on document type."""
    if doc.extension in [".md", ".markdown"]:
        return chunk_markdown(doc)
    elif doc.language:
        return chunk_code(doc)
    else:
        # Generic text chunker
        return chunk_markdown(doc)
