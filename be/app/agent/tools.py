from typing import Protocol


class KnowledgeSource(Protocol):
    async def get_document(self, source_doc: str) -> str: ...


_TOOL_TO_SOURCE_DOC = {
    "get_resume": "resume.md",
    "get_project_details": "projects.md",
    "get_contact_info": "faq.md",
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_resume",
            "description": (
                "Get syamsulhudauul's resume: summary, current role, education, contact."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_details",
            "description": "Get details about syamsulhudauul's projects.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_contact_info",
            "description": (
                "Get how to contact syamsulhudauul to schedule an interview, "
                "including availability and preferred engagement type."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class ToolExecutor:
    """Structured lookups the agent can call instead of relying purely on RAG."""

    def __init__(self, knowledge: KnowledgeSource):
        self.knowledge = knowledge

    def list_tools(self) -> list[dict]:
        return TOOL_SCHEMAS

    async def execute(self, tool_name: str, args: dict) -> str:
        source_doc = _TOOL_TO_SOURCE_DOC.get(tool_name)
        if source_doc is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await self.knowledge.get_document(source_doc)
