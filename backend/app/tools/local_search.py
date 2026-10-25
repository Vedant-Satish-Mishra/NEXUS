"""
NEXUS Safe Local Knowledge Search Tool
Uses HybridRetriever (vector semantic + BM25 reciprocal rank fusion) scoped strictly to the run's Principal.
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.rag.hybrid import HybridRetriever
from app.tools.base import ToolContext, ToolResult


class LocalSearchInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=300, description="Knowledge search query")
    top_k: Optional[int] = Field(5, ge=1, le=10, description="Number of results to return")


class LocalSearchTool:
    name: str = "local_search"
    description: str = (
        "Searches local knowledge base (system documents and user uploaded files) using hybrid vector + BM25 search."
    )
    input_model = LocalSearchInput
    requires_approval: bool = False
    timeout_s: float = 8.0

    async def run(self, ctx: ToolContext, args: LocalSearchInput) -> ToolResult:
        try:
            retriever = HybridRetriever()
            limit = args.top_k or 5
            results = await retriever.search_hybrid(
                principal=ctx.principal,
                query=args.query,
                top_k=limit,
            )

            if not results:
                return ToolResult(
                    status="success",
                    output=f"No matching documents found in knowledge base for query: '{args.query}'.",
                )

            formatted_chunks = []
            for idx, r in enumerate(results, start=1):
                file_name = r.get("file", "unknown")
                page = r.get("page", 1)
                score = r.get("score", 0.0)
                snippet = r.get("snippet", "")
                formatted_chunks.append(
                    f"[{idx}] Source: {file_name} (Page {page}, Score: {score:.3f})\n{snippet}"
                )

            return ToolResult(
                status="success",
                output="\n\n".join(formatted_chunks),
            )
        except Exception as e:
            return ToolResult(
                status="error",
                output=f"Local search failed: {str(e)}",
                message="Search error",
            )
