"""Dữ liệu Jira đã chuẩn hóa. JiraClient và MockJira trả về cùng các kiểu này."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

SprintState = Literal["active", "future", "closed"]
StatusCategory = Literal["new", "indeterminate", "done"]


class Project(BaseModel):
    key: str
    id: str
    name: str
    issue_types: list[str] = Field(default_factory=list)


class Member(BaseModel):
    account_id: str
    display_name: str
    email_masked: str | None = None
    active: bool = True


class Sprint(BaseModel):
    id: int
    name: str
    state: SprintState
    goal: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    complete_date: datetime | None = None
    board_id: int | None = None


class Issue(BaseModel):
    key: str
    id: str
    summary: str
    issue_type: str
    status: str
    status_category: StatusCategory
    assignee_id: str | None = None
    assignee_name: str | None = None
    priority: str | None = None
    story_points: float | None = None
    due_date: date | None = None
    created: datetime | None = None
    updated: datetime | None = None
    sprint_ids: list[int] = Field(default_factory=list)
    flagged: bool = False
    blocked_by: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    parent_key: str | None = None
    description_text: str | None = None


class ChangelogItem(BaseModel):
    field: str
    from_value: str | None = None
    to_value: str | None = None


class ChangelogEntry(BaseModel):
    id: str
    created: datetime
    author_id: str | None = None
    items: list[ChangelogItem] = Field(default_factory=list)


class FieldMeta(BaseModel):
    field_id: str
    name: str
    required: bool
    has_default: bool = False
    allowed_values: list[str] = Field(default_factory=list)


class Transition(BaseModel):
    id: str
    name: str
    to_status: str


class CreatedIssue(BaseModel):
    key: str
    id: str
    url: str


class JiraField(BaseModel):
    id: str
    name: str
    custom: bool = False


def mask_email(email: str | None) -> str | None:
    """Che email: 'nam.nguyen@example.com' -> 'n***@example.com'."""
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"
