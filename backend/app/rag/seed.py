"""
NEXUS System Knowledge Base Seeder CLI
Step 2.C.1 — Ingests curated markdown/code files into kb_system
Usage: python -m app.rag.seed [directory] [--reset]
"""

import argparse
import asyncio
from pathlib import Path
import sys

from app.rag.ingestion import ingest_file_path
from app.rag.vectorstore import VectorStore


async def seed_directory(dir_path: str, reset: bool = False):
    p = Path(dir_path)
    if not p.is_dir():
        print(f"Error: Directory '{dir_path}' does not exist.")
        sys.exit(1)

    vs = VectorStore()
    if reset:
        print("[NEXUS SEED] Reset flag provided. Clearing kb_system collection...")
        try:
            vs.client.delete_collection("kb_system")
            vs.kb_system = vs.client.create_collection("kb_system", metadata={"hnsw:space": "cosine"})
            print("[NEXUS SEED] kb_system cleared and re-initialized.")
        except Exception as e:
            print(f"[NEXUS SEED] Warning during reset: {e}")

    files = [
        f for f in p.iterdir()
        if f.is_file() and f.name.lower() != "readme.md" and f.suffix.lower() in [".md", ".txt", ".py", ".java", ".sql", ".js", ".ts"]
    ]

    print(f"[NEXUS SEED] Found {len(files)} knowledge files in {dir_path}. Ingesting into kb_system...")
    total_chunks = 0

    for f in sorted(files):
        file_id = f"sys_{f.stem}"
        chunks_count = await ingest_file_path(
            path_str=str(f),
            file_id=file_id,
            scope="system",
            vectorstore=vs
        )
        print(f"  -> Ingested {f.name}: {chunks_count} chunks")
        total_chunks += chunks_count

    print(f"\n[NEXUS SEED] Successfully seeded {total_chunks} chunks into system knowledge base!")


def main():
    parser = argparse.ArgumentParser(description="Seed NEXUS System Knowledge Base")
    parser.add_argument("directory", nargs="?", default="data/knowledge", help="Directory containing knowledge files")
    parser.add_argument("--reset", action="store_true", help="Clear kb_system before seeding")
    args = parser.parse_args()

    asyncio.run(seed_directory(args.directory, reset=args.reset))


if __name__ == "__main__":
    main()
