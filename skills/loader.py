"""Nạp Skill runtime của TaskMate (design mục 4.2).

Agent gọi `list_skills()` để có tên + mô tả ngắn của mọi Skill, chọn Skill phù hợp,
rồi gọi `load_skill(name)` để lấy hướng dẫn đầy đủ kèm ví dụ đưa vào prompt.
"""

import re
from pathlib import Path

from pydantic import BaseModel

SKILLS_DIR = Path(__file__).resolve().parent
SKILL_FILE = "SKILL.md"
EXAMPLES_DIR = "examples"
DESCRIPTION_MAX_LENGTH = 300
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<meta>.*?)\r?\n---\r?\n?(?P<body>.*)\Z", re.DOTALL)
_REQUIRED_KEYS = ("name", "description")


class SkillError(ValueError):
    """Skill sai định dạng."""


class SkillNotFoundError(SkillError):
    """Không có Skill với tên này."""


class SkillInfo(BaseModel):
    """Tên và mô tả ngắn (khi nào dùng) của một Skill."""

    name: str
    description: str


class SkillExample(BaseModel):
    """Một file ví dụ đầu vào → đầu ra."""

    filename: str
    content: str


class Skill(SkillInfo):
    """Nội dung đầy đủ của một Skill."""

    instructions: str
    examples: list[SkillExample]

    def to_prompt(self) -> str:
        """Ghép hướng dẫn và ví dụ thành một khối văn bản để đưa vào prompt."""
        parts = [f"# Skill: {self.name}", self.instructions.strip()]
        for index, example in enumerate(self.examples, start=1):
            parts.append(f"## Ví dụ {index} ({example.filename})\n\n{example.content.strip()}")
        return "\n\n".join(parts) + "\n"


def _parse_frontmatter(text: str, source: Path) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(text.lstrip("﻿"))
    if match is None:
        raise SkillError(f"{source}: thiếu frontmatter mở đầu và kết thúc bằng '---'")
    meta: dict[str, str] = {}
    for line_no, line in enumerate(match["meta"].splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip():
            raise SkillError(f"{source}:{line_no}: dòng frontmatter phải dạng 'khóa: giá trị'")
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, match["body"]


def _read_skill_file(skill_dir: Path) -> tuple[SkillInfo, str]:
    path = skill_dir / SKILL_FILE
    meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"), path)
    for key in _REQUIRED_KEYS:
        if not meta.get(key):
            raise SkillError(f"{path}: frontmatter thiếu '{key}'")
    name, description = meta["name"], meta["description"]
    if not NAME_RE.fullmatch(name):
        raise SkillError(f"{path}: name '{name}' chỉ được gồm chữ thường, số và dấu '-'")
    if name != skill_dir.name:
        raise SkillError(f"{path}: name '{name}' phải trùng tên thư mục '{skill_dir.name}'")
    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise SkillError(
            f"{path}: description dài {len(description)} ký tự, tối đa {DESCRIPTION_MAX_LENGTH}"
        )
    return SkillInfo(name=name, description=description), body


def list_skills(root: Path = SKILLS_DIR) -> list[SkillInfo]:
    """Tên và mô tả của mọi Skill trong `root`, sắp theo tên."""
    skill_dirs = sorted(p for p in root.iterdir() if (p / SKILL_FILE).is_file())
    return [_read_skill_file(skill_dir)[0] for skill_dir in skill_dirs]


def load_skill(name: str, root: Path = SKILLS_DIR) -> Skill:
    """Hướng dẫn đầy đủ (bỏ frontmatter) và các ví dụ của Skill `name`."""
    if not NAME_RE.fullmatch(name):
        raise SkillNotFoundError(f"Tên Skill không hợp lệ: {name!r}")
    skill_dir = root / name
    if not (skill_dir / SKILL_FILE).is_file():
        raise SkillNotFoundError(f"Không có Skill '{name}'")
    info, body = _read_skill_file(skill_dir)
    examples_dir = skill_dir / EXAMPLES_DIR
    examples = (
        [
            SkillExample(filename=p.name, content=p.read_text(encoding="utf-8"))
            for p in sorted(examples_dir.iterdir())
            if p.is_file() and p.suffix == ".md"
        ]
        if examples_dir.is_dir()
        else []
    )
    return Skill(
        name=info.name,
        description=info.description,
        instructions=body.strip(),
        examples=examples,
    )
