import pytest

from app.agent.tools import ToolExecutor


class FakeKnowledgeSource:
    def __init__(self, documents: dict[str, str]):
        self._documents = documents
        self.requested: list[str] = []

    async def get_document(self, source_doc: str) -> str:
        self.requested.append(source_doc)
        return self._documents.get(source_doc, "")


@pytest.mark.asyncio
async def test_get_resume_fetches_resume_document():
    knowledge = FakeKnowledgeSource({"resume.md": "Applied AI Engineer, 5 years experience."})
    executor = ToolExecutor(knowledge)

    result = await executor.execute("get_resume", {})

    assert result == "Applied AI Engineer, 5 years experience."
    assert knowledge.requested == ["resume.md"]


@pytest.mark.asyncio
async def test_get_project_details_fetches_projects_document():
    knowledge = FakeKnowledgeSource({"projects.md": "uul_chat_ai: an AI portfolio chat."})
    executor = ToolExecutor(knowledge)

    result = await executor.execute("get_project_details", {})

    assert result == "uul_chat_ai: an AI portfolio chat."
    assert knowledge.requested == ["projects.md"]


@pytest.mark.asyncio
async def test_get_contact_info_fetches_faq_document():
    knowledge = FakeKnowledgeSource({"faq.md": "Reach out via email to schedule an interview."})
    executor = ToolExecutor(knowledge)

    result = await executor.execute("get_contact_info", {})

    assert result == "Reach out via email to schedule an interview."
    assert knowledge.requested == ["faq.md"]


@pytest.mark.asyncio
async def test_execute_unknown_tool_raises_value_error():
    executor = ToolExecutor(FakeKnowledgeSource({}))

    with pytest.raises(ValueError, match="Unknown tool"):
        await executor.execute("delete_everything", {})


def test_list_tools_returns_all_three_tool_schemas():
    executor = ToolExecutor(FakeKnowledgeSource({}))

    names = {tool["function"]["name"] for tool in executor.list_tools()}

    assert names == {"get_resume", "get_project_details", "get_contact_info"}
