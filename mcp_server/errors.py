"""Exception khi làm việc với Jira. Thông điệp bằng tiếng Việt và không bao giờ chứa token."""


class JiraError(Exception):
    """Lỗi chung khi gọi Jira."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status_code={self.status_code!r}, message={self.message!r})"


class JiraAuthError(JiraError):
    """401/403: sai thông tin xác thực hoặc thiếu quyền."""


class JiraNotFound(JiraError):
    """404: không tìm thấy tài nguyên."""


class JiraRateLimited(JiraError):
    """429: bị giới hạn tần suất, đã hết số lần thử lại."""


def redact(text: str, secrets: list[str]) -> str:
    """Thay mọi bí mật (nếu vô tình xuất hiện) bằng '***'."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    return text
