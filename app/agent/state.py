from dataclasses import dataclass, field
from typing import Optional
from app.security.auth import UserContext


@dataclass
class AgentState:
    user_query: str
    user: UserContext
    account_id: Optional[str] = None
    retrieved_docs: list = field(default_factory=list)
    structured_data: dict = field(default_factory=dict)
    citations: list = field(default_factory=list)
    pending_actions: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    reasoning_steps: list = field(default_factory=list)
    response: str = ""
    confidence: str = "medium"
    tool_calls: list = field(default_factory=list)
    error: Optional[str] = None
