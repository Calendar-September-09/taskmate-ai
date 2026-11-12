"""Bản nháp task phía agent, mỗi trường kèm nguồn gốc (design mục 4.1, 4.6).

Giao diện duyệt dùng `Sourced.label` để ghi “từ ‘gấp’”, “mặc định”, “từ bộ nhớ”.
Khi người dùng duyệt, `TaskDraft.to_payload()` chuyển sang `domain.schemas.TaskDraft`
— payload gửi MCP Server và được gắn với approval_token.
"""

import re
from datetime import date
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

from domain import schemas
from domain.schemas import IssueType, Priority

FieldSource = Literal["user", "inferred", "memory", "default"]
T = TypeVar("T")

PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
SUMMARY_MAX_LENGTH = 120


class Sourced(BaseModel, Generic[T]):
    """Giá trị một trường kèm nguồn: người dùng nói, AI suy ra, Memory hay mặc định."""

    value: T
    source: FieldSource
    evidence: str | None = Field(
        default=None, description="Cụm gốc trong yêu cầu làm căn cứ, ví dụ 'gấp'."
    )

    @property
    def label(self) -> str:
        """Nhãn tiếng Việt hiển thị cạnh trường trên bản xem trước."""
        if self.source == "memory":
            return "từ bộ nhớ"
        if self.source == "default":
            return "mặc định"
        if self.evidence:
            return f"từ ‘{self.evidence}’"
        return "người dùng nhập" if self.source == "user" else "AI suy ra"


class TaskDraft(BaseModel):
    """Bản nháp task theo bảng mục 4.1. Trường chưa có giá trị là None.

    Bản nháp được phép dở dang (thiếu project, mô tả...) để agent hỏi bổ sung;
    `missing_fields()` cho biết còn thiếu gì trước khi duyệt.
    """

    project_key: Sourced[str] | None = None
    issue_type: Sourced[IssueType] = Field(
        default_factory=lambda: Sourced[IssueType](value="Task", source="default")
    )
    summary: Sourced[str] | None = None
    description: Sourced[str] | None = None
    assignee_id: Sourced[str] | None = Field(
        default=None, description="accountId Jira, khớp tên qua list_members."
    )
    assignee_name: str | None = Field(default=None, description="Tên hiển thị, chỉ để xem.")
    sprint_id: Sourced[int] | None = None
    priority: Sourced[Priority] | None = None
    due_date: Sourced[date] | None = None
    story_points: Sourced[float] | None = None
    labels: Sourced[list[str]] | None = None
    epic_key: Sourced[str] | None = None
    parent_key: Sourced[str] | None = None
    confidence: float = Field(default=1.0, ge=0, le=1, description="Độ chắc chắn của LLM.")

    @field_validator("project_key")
    @classmethod
    def _check_project_key(cls, field: Sourced[str] | None) -> Sourced[str] | None:
        if field is not None and not PROJECT_KEY_RE.fullmatch(field.value):
            raise ValueError("project_key phải dạng chữ in hoa, ví dụ SHOP")
        return field

    @field_validator("summary")
    @classmethod
    def _check_summary(cls, field: Sourced[str] | None) -> Sourced[str] | None:
        if field is None:
            return None
        if not field.value.strip():
            raise ValueError("summary không được để trống")
        if len(field.value.strip()) > SUMMARY_MAX_LENGTH:
            raise ValueError(f"summary tối đa {SUMMARY_MAX_LENGTH} ký tự")
        return field

    @field_validator("epic_key", "parent_key")
    @classmethod
    def _check_issue_key(cls, field: Sourced[str] | None) -> Sourced[str] | None:
        if field is not None and not ISSUE_KEY_RE.fullmatch(field.value):
            raise ValueError("issue key phải dạng PROJECT-123")
        return field

    @field_validator("story_points")
    @classmethod
    def _check_story_points(cls, field: Sourced[float] | None) -> Sourced[float] | None:
        if field is not None and field.value < 0:
            raise ValueError("story_points không được âm")
        return field

    @model_validator(mode="after")
    def _check_assignee_name(self) -> "TaskDraft":
        if self.assignee_name and self.assignee_id is None:
            raise ValueError("có assignee_name thì phải có assignee_id")
        return self

    def missing_fields(self) -> list[str]:
        """Các trường bắt buộc còn thiếu, theo thứ tự cần hỏi."""
        missing: list[str] = []
        if self.project_key is None:
            missing.append("project_key")
        if self.summary is None:
            missing.append("summary")
        if self.description is None or not self.description.value.strip():
            missing.append("description")
        if self.issue_type.value == "Sub-task" and self.parent_key is None:
            missing.append("parent_key")
        return missing

    def to_payload(self) -> schemas.TaskDraft:
        """Chuyển sang payload cho MCP (create_task). Còn thiếu trường bắt buộc thì báo lỗi."""
        missing = self.missing_fields()
        if missing:
            raise ValueError("Bản nháp còn thiếu: " + ", ".join(missing))
        assert self.project_key is not None and self.summary is not None
        parent = self.parent_key or self.epic_key
        return schemas.TaskDraft(
            project_key=self.project_key.value,
            issue_type=self.issue_type.value,
            summary=self.summary.value.strip(),
            description=self.description.value if self.description else "",
            assignee_id=self.assignee_id.value if self.assignee_id else None,
            sprint_id=self.sprint_id.value if self.sprint_id else None,
            priority=self.priority.value if self.priority else None,
            due_date=self.due_date.value if self.due_date else None,
            story_points=self.story_points.value if self.story_points else None,
            labels=list(self.labels.value) if self.labels else [],
            parent_key=parent.value if parent else None,
            confidence=self.confidence,
        )


class MeetingExtraction(BaseModel):
    """Kết quả bóc tách biên bản họp: task, quyết định, câu chưa rõ cần hỏi lại."""

    tasks: list[TaskDraft] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    unclear: list[str] = Field(default_factory=list)
