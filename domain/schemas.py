"""Schema dữ liệu có cấu trúc của TaskMate (design mục 4.1)."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

IssueType = Literal["Story", "Task", "Bug", "Sub-task"]
Priority = Literal["Highest", "High", "Medium", "Low", "Lowest"]


class TaskDraft(BaseModel):
    """Bản nháp một task trước khi tạo trên Jira. Người dùng duyệt bản nháp này (HITL)."""

    project_key: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]+$", description="Key project Jira, ví dụ SHOP."
    )
    issue_type: IssueType = Field(default="Task", description="Loại issue.")
    summary: str = Field(
        min_length=1, max_length=120, description="Tiêu đề ngắn, bắt đầu bằng động từ."
    )
    description: str = Field(default="", description="Mô tả dạng Markdown theo template.")
    assignee_id: str | None = Field(
        default=None, description="accountId Jira của người phụ trách (lấy từ list_members)."
    )
    sprint_id: int | None = Field(default=None, description="Id sprint (lấy từ list_sprints).")
    priority: Priority | None = Field(default=None, description="Mức ưu tiên.")
    due_date: date | None = Field(default=None, description="Hạn hoàn thành, dạng YYYY-MM-DD.")
    story_points: float | None = Field(default=None, ge=0)
    labels: list[str] = Field(default_factory=list)
    parent_key: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]+-\d+$",
        description="Issue cha, bắt buộc với Sub-task.",
    )
    confidence: float = Field(
        default=1.0, ge=0, le=1, description="Độ chắc chắn của LLM; không gửi lên Jira."
    )

    @field_validator("summary")
    @classmethod
    def _summary_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary không được để trống")
        return value

    def to_jira_fields(self, *, story_points_field: str, sprint_field: str) -> dict[str, Any]:
        """Chuyển sang dict `fields` cho JiraBackend.create_issue."""
        fields: dict[str, Any] = {
            "project": {"key": self.project_key},
            "issuetype": {"name": self.issue_type},
            "summary": self.summary.strip(),
        }
        if self.description.strip():
            fields["description"] = self.description
        if self.assignee_id:
            fields["assignee"] = {"accountId": self.assignee_id}
        if self.priority:
            fields["priority"] = {"name": self.priority}
        if self.due_date:
            fields["duedate"] = self.due_date.isoformat()
        if self.labels:
            fields["labels"] = sorted({label.strip() for label in self.labels if label.strip()})
        if self.parent_key:
            fields["parent"] = {"key": self.parent_key}
        if self.story_points is not None:
            fields[story_points_field] = self.story_points
        if self.sprint_id is not None:
            fields[sprint_field] = self.sprint_id
        return fields
