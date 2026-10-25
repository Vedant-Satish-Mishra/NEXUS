"""
NEXUS Knowledge Pack Builder (Step 5.C.1)
Produces a reproducible manifest (data/knowledge/manifest.json) containing:
- File paths
- SHA-256 checksums
- Estimated chunk counts
- Corpus-level aggregate checksum
Ensures all teammates and deployment environments index identical knowledge content.
"""
import glob
import hashlib
import json
import os
import sys

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")
MANIFEST_PATH = os.path.join(KNOWLEDGE_DIR, "manifest.json")


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def count_chunks_heuristic(content: str) -> int:
    """Estimates chunk count based on heading splits (250-350 words per chunk)."""
    words = len(content.split())
    return max(1, (words + 200) // 250)


def build_pack():
    files = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")))
    files = [f for f in files if os.path.basename(f) not in ("README.md", "manifest.json")]

    manifest = {
        "version": "1.0.0",
        "generated_by": "scripts/build_knowledge_pack.py",
        "file_count": len(files),
        "total_bytes": 0,
        "total_estimated_chunks": 0,
        "files": [],
    }

    corpus_hasher = hashlib.sha256()

    for fpath in files:
        fname = os.path.basename(fpath)
        sha = compute_sha256(fpath)
        size = os.path.getsize(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = count_chunks_heuristic(content)
        corpus_hasher.update(sha.encode("utf-8"))

        manifest["total_bytes"] += size
        manifest["total_estimated_chunks"] += chunks
        manifest["files"].append({
            "filename": fname,
            "sha256": sha,
            "size_bytes": size,
            "estimated_chunks": chunks,
        })

    manifest["corpus_sha256"] = corpus_hasher.hexdigest()

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {MANIFEST_PATH}")
    print(f"  Files: {manifest['file_count']}")
    print(f"  Total Bytes: {manifest['total_bytes']}")
    print(f"  Estimated Chunks: {manifest['total_estimated_chunks']}")
    print(f"  Corpus SHA-256: {manifest['corpus_sha256']}")


if __name__ == "__main__":
    build_pack()
