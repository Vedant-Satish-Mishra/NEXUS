"""
NEXUS Safe File Reader Tool
Reads parsed file content scoped strictly to the current user's uploaded documents.
Never accepts arbitrary filesystem paths.
"""
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db.models import FileRecord
from app.rag.vectorstore import VectorStore
from app.tools.base import ToolContext, ToolResult


class FileReaderInput(BaseModel):
    file_id: str = Field(..., description="ID of the uploaded document to read")
    page_from: Optional[int] = Field(None, ge=1, description="Optional start page (1-based)")
    page_to: Optional[int] = Field(None, ge=1, description="Optional end page (inclusive)")


class FileReaderTool:
    name: str = "file_reader"
    description: str = "Reads text and pages from an uploaded document owned by the user."
    input_model = FileReaderInput
    requires_approval: bool = False
    timeout_s: float = 5.0

    async def run(self, ctx: ToolContext, args: FileReaderInput) -> ToolResult:
        if not ctx.db:
            return ToolResult(
                status="error",
                output="Database session unavailable for file reader.",
                message="Internal error",
            )

        session = ctx.db
        close_session = False
        if hasattr(ctx.db, "begin") and not hasattr(ctx.db, "execute"):
            session = ctx.db()
            close_session = True

        try:
            # 1. Verify existence and ownership
            stmt = select(FileRecord).where(FileRecord.id == args.file_id)
            result = await session.execute(stmt)
            file_rec = result.scalar_one_or_none()
        finally:
            if close_session:
                await session.close()

        if not file_rec:
            return ToolResult(
                status="error",
                output=f"File '{args.file_id}' not found or access denied.",
                message="File not found",
            )

        # Strict multi-tenant isolation
        if file_rec.user_id != ctx.principal.user_id and file_rec.scope != "system":
            return ToolResult(
                status="error",
                output=f"File '{args.file_id}' not found or access denied.",
                message="Access denied",
            )

        # 2. Retrieve chunked text from Chroma
        try:
            vs = VectorStore()
            col = vs.kb_user if file_rec.scope != "system" else vs.kb_system

            # Fetch chunks belonging to this file
            where_clause = {"file_id": args.file_id}
            records = col.get(where=where_clause, include=["documents", "metadatas"])

            if not records or not records.get("documents"):
                return ToolResult(
                    status="success",
                    output=f"File '{file_rec.filename}' has no indexed text chunks yet.",
                )

            docs = records["documents"]
            metas = records["metadatas"]

            # Sort by chunk_index
            combined = sorted(
                zip(docs, metas),
                key=lambda item: (item[1].get("page", 1), item[1].get("chunk_index", 0)),
            )

            lines = []
            for doc, meta in combined:
                page = meta.get("page", 1)
                if args.page_from and page < args.page_from:
                    continue
                if args.page_to and page > args.page_to:
                    continue
                lines.append(f"--- [Page {page}] ---\n{doc}")

            if not lines:
                return ToolResult(
                    status="success",
                    output=f"No content found in '{file_rec.filename}' for the specified page range.",
                )

            return ToolResult(status="success", output="\n\n".join(lines))
        except Exception as e:
            return ToolResult(
                status="error",
                output=f"Error reading file '{file_rec.filename}': {str(e)}",
                message="Read failure",
            )
