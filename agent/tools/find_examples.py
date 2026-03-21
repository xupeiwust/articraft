from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agent.examples import search_example_documents
from agent.tools.base import BaseDeclarativeTool, BaseToolInvocation, ToolResult, make_tool_schema


class FindExamplesParams(BaseModel):
    file_path: str | None = None
    query: str
    limit: int = 3


class FindExamplesInvocation(BaseToolInvocation[FindExamplesParams, list[dict[str, object]]]):
    def __init__(self, params: FindExamplesParams, *, sdk_package: str) -> None:
        super().__init__(params)
        self.sdk_package = sdk_package

    def get_description(self) -> str:
        return (
            f"Search curated {self.sdk_package} examples for query={self.params.query!r} "
            f"(limit={self.params.limit})"
        )

    async def execute(self) -> ToolResult:
        query = self.params.query.strip()
        if not query:
            return ToolResult(error="query must not be empty")
        if self.params.limit < 1:
            return ToolResult(error="limit must be >= 1")

        matches = search_example_documents(
            query,
            sdk_package=self.sdk_package,
            limit=self.params.limit,
        )
        return ToolResult(
            output=[
                {
                    "title": doc.title,
                    "description": doc.description,
                    "tags": list(doc.tags),
                    "path": doc.path.relative_to(Path(__file__).resolve().parents[2]).as_posix(),
                    "content": doc.content,
                }
                for doc in matches
            ]
        )


class FindExamplesTool(BaseDeclarativeTool):
    def __init__(self, *, sdk_package: str) -> None:
        self.sdk_package = sdk_package
        schema = make_tool_schema(
            name="find_examples",
            description=(
                "Search curated example documents for the active SDK and return full markdown "
                "matches.\n\n"
                "Use this when you need a concrete CadQuery or hybrid authoring reference before "
                "editing code.\n\n"
                "Returns: a list of matches with title, description, tags, path, and full content."
            ),
            parameters={
                "query": {
                    "type": "string",
                    "description": "What example pattern to search for.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of full example documents to return.",
                },
            },
            required=["query"],
        )
        super().__init__("find_examples", schema)

    async def build(self, params: dict) -> FindExamplesInvocation:
        validated = FindExamplesParams(**params)
        return FindExamplesInvocation(validated, sdk_package=self.sdk_package)
