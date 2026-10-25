"""
NEXUS Web Search Tool (Registered but Disabled by Default)
Preserves local-first privacy policy.
"""
from pydantic import BaseModel, Field
from app.tools.base import ToolContext, ToolResult


class WebSearchInput(BaseModel):
    query: str = Field(..., description="Web search query")


class WebSearchTool:
    name: str = "web_search"
    description: str = "Searches the public web. (Disabled by default under local-first privacy policy)."
    input_model = WebSearchInput
    requires_approval: bool = True
    timeout_s: float = 5.0

    async def run(self, ctx: ToolContext, args: WebSearchInput) -> ToolResult:
        return ToolResult(
            status="error",
            output="Web search is currently disabled by privacy policy (NEXUS local-first mode).",
            message="Disabled",
        )
