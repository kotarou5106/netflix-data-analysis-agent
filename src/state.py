from pydantic import BaseModel, Field


class AgentState(BaseModel):
    user_query: str = ""
    intent: str = ""
    plan: list = Field(default_factory=list)
    selected_tools: list[str] = Field(default_factory=list)
    tool_results: list = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    draft_report: str = ""
    verification_result: dict = Field(default_factory=dict)
    final_report: str = ""
    retry_count: int = 0
