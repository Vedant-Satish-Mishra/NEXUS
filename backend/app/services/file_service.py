"""
NEXUS File Storage & Ingestion Service (Milestone 3)
Step 3.D.1 — Multipart upload handling, quota validation, background worker, and deletion cascade.
"""

import asyncio
import hashlib
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.models import FileRecord, User
from app.rag.chunking import DocumentChunk, chunk_document
from app.rag.hybrid import sanitize_chunk_text
from app.rag.ingestion import ingest_chunks
from app.rag.loaders import LoadedDocument, ParseError, parse_file
from app.rag.ocr import ocr_pdf_pages
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal

logger = logging.getLogger("nexus.file_service")

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".csv",
    ".txt", ".md", ".markdown", ".py", ".java",
    ".js", ".ts", ".html", ".css", ".sql"
}


class FileService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self.vectorstore = VectorStore()

    def start_worker(self):
        """Starts the background worker queue."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("Background file ingestion worker started.")

    async def stop_worker(self):
        """Stops background worker."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def upload_file(
        self,
        file: UploadFile,
        scope: str,
        conversation_id: Optional[str],
        current_user: User
    ) -> FileRecord:
        """
        Validates, saves, records, and queues an uploaded file for ingestion.
        """
        filename = file.filename or "uploaded_file"
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' not allowed. Allowed: {sorted(list(ALLOWED_EXTENSIONS))}"
            )

        if scope == "chat" and not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id is required when scope='chat'"
            )

        # Read contents and calculate SHA-256
        content = await file.read()
        file_size = len(content)

        if file_size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size limit of {settings.MAX_UPLOAD_MB} MB"
            )

        file_sha256 = hashlib.sha256(content).hexdigest()

        # Check user quota and duplicate file
        async with self.session_factory() as db:
            # Quota check
            sum_stmt = select(func.sum(FileRecord.size)).where(FileRecord.user_id == current_user.id)
            total_used = (await db.execute(sum_stmt)).scalar() or 0
            if total_used + file_size > settings.MAX_USER_QUOTA_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"User quota exceeded (Limit: {settings.MAX_USER_QUOTA_MB} MB)"
                )

            # Duplicate detection per user
            dup_stmt = select(FileRecord).where(
                FileRecord.user_id == current_user.id,
                FileRecord.sha256 == file_sha256,
                FileRecord.status != "failed"
            )
            dup = (await db.execute(dup_stmt)).scalar_one_or_none()
            if dup:
                return dup

            # Create DB row
            file_record = FileRecord(
                user_id=current_user.id,
                conversation_id=conversation_id if scope == "chat" else None,
                scope=scope,
                filename=filename,
                mime=file.content_type or "application/octet-stream",
                size=file_size,
                sha256=file_sha256,
                status="processing",
            )
            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)

        # Save to disk: uploads/<user_id>/<file_id><ext>
        user_dir = Path(settings.UPLOAD_DIR) / current_user.id
        user_dir.mkdir(parents=True, exist_ok=True)
        disk_path = user_dir / f"{file_record.id}{ext}"
        with open(disk_path, "wb") as f:
            f.write(content)

        # Enqueue for background ingestion
        await self.queue.put(file_record.id)
        return file_record

    async def _process_queue(self):
        """Worker loop processing files sequentially to prevent CPU/memory contention."""
        while True:
            file_id = await self.queue.get()
            try:
                await self._process_single_file(file_id)
            except Exception as exc:
                logger.error(f"Error processing file '{file_id}': {exc}", exc_info=True)
            finally:
                self.queue.task_done()

    async def _process_single_file(self, file_id: str):
        async with self.session_factory() as db:
            stmt = select(FileRecord).where(FileRecord.id == file_id)
            rec = (await db.execute(stmt)).scalar_one_or_none()
            if not rec:
                return

            ext = Path(rec.filename).suffix.lower()
            disk_path = Path(settings.UPLOAD_DIR) / rec.user_id / f"{rec.id}{ext}"

            try:
                parsed = parse_file(str(disk_path))
                
                # Check for pages needing OCR
                ocr_needed_pages = [p.number for p in parsed.pages if p.needs_ocr]
                if ocr_needed_pages and ext == ".pdf":
                    ocr_results = await ocr_pdf_pages(str(disk_path), ocr_needed_pages)
                    ocr_map = {res["page"]: res["text"] for res in ocr_results}
                    for p in parsed.pages:
                        if p.number in ocr_map and ocr_map[p.number]:
                            p.text = (p.text + "\n" + ocr_map[p.number]).strip()
                            p.needs_ocr = False

                # Chunking
                loaded_doc = LoadedDocument(
                    content=parsed.full_text,
                    source=rec.filename,
                    filename=rec.filename,
                    extension=rec.extension,
                    topic=parsed.topic
                )
                raw_chunks = chunk_document(loaded_doc)

                # Sanitization for prompt injection hygiene
                sanitized_chunks: List[DocumentChunk] = []
                for c in raw_chunks:
                    clean_text, _ = sanitize_chunk_text(c.text)
                    sanitized_chunks.append(DocumentChunk(
                        text=clean_text,
                        source=c.source,
                        topic=c.topic,
                        chunk_index=c.chunk_index,
                        heading_path=c.heading_path,
                        page=c.page
                    ))

                # Ingestion to ChromaDB
                principal = Principal(user_id=rec.user_id, conversation_id=rec.conversation_id)
                num_chunks = await ingest_chunks(
                    chunks=sanitized_chunks,
                    file_id=rec.id,
                    scope=rec.scope,
                    principal=principal,
                    vectorstore=self.vectorstore
                )

                # Mark ready
                rec.status = "ready"
                rec.pages = len(parsed.pages)
                rec.chunks = num_chunks
                await db.commit()
                logger.info(f"File '{rec.filename}' successfully processed into {num_chunks} chunks.")

            except Exception as err:
                logger.error(f"Failed to process file '{rec.filename}': {err}")
                rec.status = "failed"
                rec.error = str(err)
                await db.commit()

    async def promote_file(self, file_id: str, current_user: User) -> FileRecord:
        """Promotes a chat-scoped file to personal scope."""
        async with self.session_factory() as db:
            stmt = select(FileRecord).where(FileRecord.id == file_id, FileRecord.user_id == current_user.id)
            rec = (await db.execute(stmt)).scalar_one_or_none()
            if not rec:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            rec.scope = "personal"
            rec.conversation_id = None
            await db.commit()
            await db.refresh(rec)

        # Update metadata in ChromaDB
        principal = Principal(user_id=current_user.id)
        # Re-index chunks under personal scope
        ext = Path(rec.filename).suffix.lower()
        disk_path = Path(settings.UPLOAD_DIR) / rec.user_id / f"{rec.id}{ext}"
        if disk_path.is_file():
            parsed = parse_file(str(disk_path))
            loaded_doc = LoadedDocument(
                content=parsed.full_text,
                source=rec.filename,
                filename=rec.filename,
                extension=rec.extension,
                topic=parsed.topic
            )
            chunks = chunk_document(loaded_doc)
            await ingest_chunks(
                chunks=chunks,
                file_id=rec.id,
                scope="personal",
                principal=principal,
                vectorstore=self.vectorstore
            )

        return rec

    async def delete_file(self, file_id: str, current_user: User) -> None:
        """Cascade deletes: disk file, DB record, and ChromaDB vectors."""
        async with self.session_factory() as db:
            stmt = select(FileRecord).where(FileRecord.id == file_id, FileRecord.user_id == current_user.id)
            rec = (await db.execute(stmt)).scalar_one_or_none()
            if not rec:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            ext = Path(rec.filename).suffix.lower()
            disk_path = Path(settings.UPLOAD_DIR) / rec.user_id / f"{rec.id}{ext}"
            if disk_path.is_file():
                try:
                    disk_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete file on disk: {e}")

            await db.delete(rec)
            await db.commit()

        # Delete from ChromaDB
        principal = Principal(user_id=current_user.id)
        self.vectorstore.delete_file(principal, file_id)
        logger.info(f"File {file_id} deleted with full cascade.")
