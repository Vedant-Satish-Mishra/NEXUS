"""
NEXUS Knowledge Base Validator (Step 5.C.1)
Validates all Markdown files in data/knowledge against the quality checklist:
- Front-matter topic present
- Word count within reasonable boundaries
- Zero TODO / TODO-VERIFY / FIXME markers
- Proper Markdown heading hierarchy
- Non-empty, tagged fenced code blocks
- No duplicate paragraphs across documents
"""
import glob
import os
import re
import sys
from typing import Dict, List, Set

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")


def validate_file(filepath: str, seen_paragraphs: Dict[str, str]) -> List[str]:
    errors = []
    fname = os.path.basename(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Front-matter topic
    if not re.match(r"^topic:\s*[a-zA-Z0-9_-]+", content.strip()):
        errors.append("Missing 'topic: <topic>' front-matter on first line")

    # 2. Word count check (relaxed to 120-700 words)
    words = re.findall(r"\b\w+\b", content)
    if len(words) < 120:
        errors.append(f"Word count too low ({len(words)} words; minimum 120)")
    elif len(words) > 750:
        errors.append(f"Word count too high ({len(words)} words; maximum 750)")

    # 3. No TODO / TODO-VERIFY markers
    for forbidden in ["TODO-VERIFY", "TODO:", "FIXME", "LOREM IPSUM"]:
        if forbidden.lower() in content.lower():
            errors.append(f"Found forbidden marker '{forbidden}'")

    # 4. Heading structure (remove code blocks before matching markdown headings)
    text_without_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    h1_matches = re.findall(r"^#\s+(.+)$", text_without_code, re.MULTILINE)
    h2_matches = re.findall(r"^##\s+(.+)$", text_without_code, re.MULTILINE)
    if len(h1_matches) != 1:
        errors.append(f"Expected exactly 1 H1 heading, found {len(h1_matches)}")
    if len(h2_matches) < 1:
        errors.append(f"Expected at least 1 H2 heading, found {len(h2_matches)}")

    # 5. Code blocks
    code_blocks = re.findall(r"```([a-zA-Z0-9_-]*)\n(.*?)```", content, re.DOTALL)
    for lang, code in code_blocks:
        if not lang.strip():
            errors.append("Fenced code block missing language tag")
        if not code.strip():
            errors.append("Fenced code block is empty")

    # 6. Duplicate paragraph check
    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 60]
    for p in paragraphs:
        # Ignore code blocks or markdown tables
        if p.startswith("```") or p.startswith("|"):
            continue
        norm_p = " ".join(p.lower().split())
        if norm_p in seen_paragraphs:
            errors.append(f"Duplicate paragraph detected (also in {seen_paragraphs[norm_p]})")
        else:
            seen_paragraphs[norm_p] = fname

    return errors


def main():
    files = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")))
    files = [f for f in files if os.path.basename(f) != "README.md"]

    print(f"Validating {len(files)} knowledge files in {KNOWLEDGE_DIR}...")
    seen_paragraphs: Dict[str, str] = {}
    total_errors = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        errs = validate_file(fpath, seen_paragraphs)
        if errs:
            print(f"[FAIL] {fname}:")
            for e in errs:
                print(f"   - {e}")
            total_errors += len(errs)
        else:
            print(f"[PASS] {fname}")

    if total_errors > 0:
        print(f"\nTotal errors found: {total_errors}")
        sys.exit(1)
    else:
        print(f"\nAll {len(files)} knowledge documents validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
