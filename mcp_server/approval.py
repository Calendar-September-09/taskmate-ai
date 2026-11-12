"""approval_token cho các tool ghi (design 4.3, 4.5, 4.6).

Token = "v1.<payload base64url>.<chữ ký base64url>", chữ ký HMAC-SHA256 bằng APPROVAL_SECRET.
Payload gồm hash bản nháp đã chuẩn hóa, người duyệt, thời hạn và mã dùng một lần (jti).
"""

import base64
import binascii
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ValidationError

from mcp_server.store import ServerStore

TOKEN_VERSION = "v1"
DEFAULT_TTL = timedelta(minutes=30)

RejectReason = Literal[
    "missing_secret", "missing_token", "malformed", "bad_signature", "expired", "draft_changed",
    "used",
]

_MESSAGES: dict[RejectReason, str] = {
    "missing_secret": "Máy chủ chưa cấu hình APPROVAL_SECRET nên không thể xác nhận duyệt.",
    "missing_token": "Thiếu approval_token. Bản nháp phải được người dùng duyệt trước khi tạo.",
    "malformed": "approval_token không đúng định dạng.",
    "bad_signature": "approval_token không hợp lệ (sai chữ ký).",
    "expired": "approval_token đã hết hạn. Hãy duyệt lại bản nháp.",
    "draft_changed": "Bản nháp đã bị sửa sau khi duyệt. Hãy duyệt lại bản nháp mới.",
    "used": "approval_token đã được dùng. Mỗi lần duyệt chỉ dùng được một lần.",
}


class ApprovalError(Exception):
    """approval_token bị từ chối. Thông điệp không chứa token."""

    def __init__(self, reason: RejectReason) -> None:
        super().__init__(_MESSAGES[reason])
        self.reason: RejectReason = reason


class ApprovalPayload(BaseModel):
    h: str  # hash bản nháp
    approver: str
    exp: int  # Unix timestamp (giây)
    jti: str  # mã dùng một lần


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(digest)


def issue_token(
    draft_hash: str,
    approver: str,
    secret: str,
    now: datetime,
    ttl: timedelta = DEFAULT_TTL,
) -> str:
    """Sinh approval_token sau khi người dùng bấm Approve (bước HITL)."""
    if not secret:
        raise ApprovalError("missing_secret")
    payload = ApprovalPayload(
        h=draft_hash,
        approver=approver,
        exp=int((now + ttl).timestamp()),
        jti=uuid.uuid4().hex,
    )
    body = _b64encode(payload.model_dump_json().encode("utf-8"))
    message = f"{TOKEN_VERSION}.{body}"
    return f"{message}.{_sign(message, secret)}"


def decode_token(token: str, secret: str) -> ApprovalPayload:
    """Kiểm tra định dạng và chữ ký, trả payload. Chưa kiểm tra hạn hay số lần dùng."""
    if not secret:
        raise ApprovalError("missing_secret")
    if not token:
        raise ApprovalError("missing_token")
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_VERSION:
        raise ApprovalError("malformed")
    message = f"{parts[0]}.{parts[1]}"
    if not hmac.compare_digest(_sign(message, secret), parts[2]):
        raise ApprovalError("bad_signature")
    try:
        return ApprovalPayload.model_validate(json.loads(_b64decode(parts[1])))
    except (ValueError, binascii.Error, ValidationError) as exc:
        raise ApprovalError("malformed") from exc


def verify_token(
    token: str,
    draft_hash: str,
    secret: str,
    store: ServerStore,
    now: datetime,
) -> ApprovalPayload:
    """Xác minh token cho đúng bản nháp; nếu hợp lệ thì đánh dấu đã dùng.

    Từ chối khi: sai định dạng, sai chữ ký, hết hạn, bản nháp bị sửa sau khi duyệt, đã dùng.
    """
    payload = decode_token(token, secret)
    if now.timestamp() > payload.exp:
        raise ApprovalError("expired")
    if not hmac.compare_digest(payload.h, draft_hash):
        raise ApprovalError("draft_changed")
    if not store.consume_approval(payload.jti, payload.approver, now):
        raise ApprovalError("used")
    return payload
