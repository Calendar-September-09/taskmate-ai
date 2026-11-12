"""Test bộ Skill runtime trong skills/ và loader."""

import json
import re
from pathlib import Path

import pytest

from skills.loader import (
    DESCRIPTION_MAX_LENGTH,
    SKILLS_DIR,
    SkillError,
    SkillNotFoundError,
    list_skills,
    load_skill,
)

EXPECTED_SKILLS = [
    "bug-report",
    "meeting-to-tasks",
    "missing-info",
    "retro",
    "scrum-conventions",
    "sprint-report",
    "standup-brief",
    "task-writing",
]
MAX_SKILL_LINES = 200
_JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def test_list_skills_returns_all_expected() -> None:
    assert [s.name for s in list_skills()] == EXPECTED_SKILLS


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_frontmatter_valid(name: str) -> None:
    text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    info = next(s for s in list_skills() if s.name == name)
    assert info.description
    assert len(info.description) < DESCRIPTION_MAX_LENGTH
    assert "dùng" in info.description.lower(), "description phải nói rõ khi nào dùng"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_file_is_short(name: str) -> None:
    lines = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) < MAX_SKILL_LINES


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_examples_have_input_and_output(name: str) -> None:
    skill = load_skill(name)
    assert 1 <= len(skill.examples) <= 2
    for example in skill.examples:
        assert "## Đầu vào" in example.content, example.filename
        assert "## Đầu ra" in example.content, example.filename


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_json_blocks_in_examples_are_valid(name: str) -> None:
    for example in load_skill(name).examples:
        for block in _JSON_BLOCK_RE.findall(example.content):
            json.loads(block)


def test_load_skill_strips_frontmatter_and_includes_examples() -> None:
    skill = load_skill("meeting-to-tasks")
    assert skill.name == "meeting-to-tasks"
    assert not skill.instructions.startswith("---")
    assert "description:" not in skill.instructions
    assert skill.instructions.startswith("# Trích task từ biên bản họp")
    assert [e.filename for e in skill.examples] == [
        "01-sprint-planning.md",
        "02-daily-standup.md",
    ]
    prompt = skill.to_prompt()
    assert "# Skill: meeting-to-tasks" in prompt
    assert "## Ví dụ 1 (01-sprint-planning.md)" in prompt
    assert "## Ví dụ 2 (02-daily-standup.md)" in prompt
    assert "Sprint Planning" in prompt


def test_meeting_to_tasks_covers_four_meeting_types() -> None:
    instructions = load_skill("meeting-to-tasks").instructions
    for meeting in ("Sprint Planning", "Daily Stand-up", "Sprint Review", "Retrospective"):
        assert meeting in instructions


# --- Lỗi định dạng, dùng thư mục tạm -------------------------------------------------


def _write_skill(root: Path, dirname: str, content: str) -> None:
    (root / dirname).mkdir(parents=True, exist_ok=True)
    (root / dirname / "SKILL.md").write_text(content, encoding="utf-8")


def test_loader_reads_custom_root(tmp_path: Path) -> None:
    _write_skill(tmp_path, "demo", "---\nname: demo\ndescription: Dùng khi thử\n---\n# Demo\n")
    (tmp_path / "demo" / "examples").mkdir()
    (tmp_path / "demo" / "examples" / "b.md").write_text("B", encoding="utf-8")
    (tmp_path / "demo" / "examples" / "a.md").write_text("A", encoding="utf-8")
    (tmp_path / "demo" / "examples" / "note.txt").write_text("bỏ qua", encoding="utf-8")
    (tmp_path / "not-a-skill").mkdir()

    assert [s.name for s in list_skills(tmp_path)] == ["demo"]
    skill = load_skill("demo", tmp_path)
    assert skill.instructions == "# Demo"
    assert [e.content for e in skill.examples] == ["A", "B"]


def test_skill_without_examples_dir(tmp_path: Path) -> None:
    _write_skill(tmp_path, "demo", "---\nname: demo\ndescription: Dùng khi thử\n---\nNội dung\n")
    assert load_skill("demo", tmp_path).examples == []


def test_windows_line_endings(tmp_path: Path) -> None:
    _write_skill(tmp_path, "demo", "---\r\nname: demo\r\ndescription: Dùng khi thử\r\n---\r\nX\r\n")
    assert load_skill("demo", tmp_path).description == "Dùng khi thử"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("# Không có frontmatter\n", "frontmatter"),
        ("---\nname: demo\n---\nX\n", "description"),
        ("---\ndescription: Dùng khi thử\n---\nX\n", "name"),
        ("---\nname: khac\ndescription: Dùng khi thử\n---\nX\n", "tên thư mục"),
        (f"---\nname: demo\ndescription: {'x' * 301}\n---\nX\n", "tối đa"),
        ("---\nname: demo\ndòng sai\n---\nX\n", "khóa: giá trị"),
    ],
)
def test_invalid_frontmatter(tmp_path: Path, content: str, message: str) -> None:
    _write_skill(tmp_path, "demo", content)
    with pytest.raises(SkillError, match=message):
        load_skill("demo", tmp_path)
    with pytest.raises(SkillError):
        list_skills(tmp_path)


def test_invalid_name_format(tmp_path: Path) -> None:
    _write_skill(tmp_path, "Demo_X", "---\nname: Demo_X\ndescription: Dùng khi thử\n---\nX\n")
    with pytest.raises(SkillError, match="chữ thường"):
        list_skills(tmp_path)


@pytest.mark.parametrize(
    "name", ["khong-co", "../etc", "task-writing/../retro", "", "Task-Writing"]
)
def test_load_unknown_or_unsafe_name(name: str) -> None:
    with pytest.raises(SkillNotFoundError):
        load_skill(name)
