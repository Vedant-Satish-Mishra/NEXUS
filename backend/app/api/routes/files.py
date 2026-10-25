"""
NEXUS Files & Knowledge API Routes (Milestone 3)
Step 3.D.1 & Step 3.C.3 — Scoped file management and hybrid retrieval inspector
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import FileRecord, User
from app.db.session import async_session_maker
from app.rag.hybrid import HybridRetriever
from app.schemas.core import Principal
from app.services.file_service import FileService

router = APIRouter(tags=["files"])
file_service = FileService(session_factory=async_session_maker)
hybrid_retriever = HybridRetriever()


class FileOut(BaseModel):
    id: str
    filename: str
    scope: str
    mime: str
    size: int
    status: str
    error: Optional[str] = None
    pages: int
    chunks: int
    created_at: str

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    top_k: int = 6


@router.post("/files", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    scope: str = Form("chat"),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """Uploads file with background ingestion."""
    record = await file_service.upload_file(
        file=file,
        scope=scope,
        conversation_id=conversation_id,
        current_user=current_user
    )
    return FileOut(
        id=record.id,
        filename=record.filename,
        scope=record.scope,
        mime=record.mime,
        size=record.size,
        status=record.status,
        error=record.error,
        pages=record.pages,
        chunks=record.chunks,
        created_at=str(record.created_at)
    )


@router.get("/files", response_model=List[FileOut])
async def list_files(
    scope: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists files owned by the current user."""
    stmt = select(FileRecord).where(FileRecord.user_id == current_user.id)
    if scope:
        stmt = stmt.where(FileRecord.scope == scope)
    if status_filter:
        stmt = stmt.where(FileRecord.status == status_filter)

    stmt = stmt.order_by(FileRecord.created_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        FileOut(
            id=r.id,
            filename=r.filename,
            scope=r.scope,
            mime=r.mime,
            size=r.size,
            status=r.status,
            error=r.error,
            pages=r.pages,
            chunks=r.chunks,
            created_at=str(r.created_at)
        )
        for r in records
    ]


@router.get("/files/{file_id}", response_model=FileOut)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves file status. 404 for other users' resources."""
    stmt = select(FileRecord).where(FileRecord.id == file_id, FileRecord.user_id == current_user.id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileOut(
        id=rec.id,
        filename=rec.filename,
        scope=rec.scope,
        mime=rec.mime,
        size=rec.size,
        status=rec.status,
        error=rec.error,
        pages=rec.pages,
        chunks=rec.chunks,
        created_at=str(rec.created_at)
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """Deletes file, DB record, and cascade removes ChromaDB vectors."""
    await file_service.delete_file(file_id, current_user)
    return None


@router.post("/files/{file_id}/promote", response_model=FileOut)
async def promote_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """Promotes a chat-scoped file to personal knowledge scope."""
    record = await file_service.promote_file(file_id, current_user)
    return FileOut(
        id=record.id,
        filename=record.filename,
        scope=record.scope,
        mime=record.mime,
        size=record.size,
        status=record.status,
        error=record.error,
        pages=record.pages,
        chunks=record.chunks,
        created_at=str(record.created_at)
    )


@router.post("/knowledge/search")
async def search_knowledge(
    payload: SearchQuery,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieval Inspector: executes hybrid search and returns
    full breakdown (vector score, bm25 score, rrf rank).
    """
    principal = Principal(user_id=current_user.id, conversation_id=payload.conversation_id)
    results = await hybrid_retriever.search_hybrid(
        principal=principal,
        query=payload.query,
        top_k=payload.top_k,
    )
    return {"query": payload.query, "results": results}
