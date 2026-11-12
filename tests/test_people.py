"""Test match_member với danh sách thành viên giống project SHOP trên Jira mock."""

import pytest
from pydantic import BaseModel

from domain.people import Ambiguous, NotFound, Unique, match_member


class FakeMember(BaseModel):
    account_id: str
    display_name: str
    active: bool = True


MEMBERS = [
    FakeMember(account_id="acc-nam-be", display_name="Nguyễn Văn Nam"),
    FakeMember(account_id="acc-nam-qa", display_name="Trần Hoài Nam"),
    FakeMember(account_id="acc-duc", display_name="Phạm Minh Đức"),
    FakeMember(account_id="acc-ha", display_name="Lê Thu Hà"),
    FakeMember(account_id="acc-lan-old", display_name="Võ Thị Lan", active=False),
]


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("Phạm Minh Đức", "acc-duc"),
        ("pham minh duc", "acc-duc"),
        ("Đức", "acc-duc"),
        ("duc", "acc-duc"),
        ("anh Đức", "acc-duc"),
        ("@duc", "acc-duc"),
        ("Hà", "acc-ha"),
        ("chị ha", "acc-ha"),
        ("Hoài Nam", "acc-nam-qa"),
        ("hoai nam", "acc-nam-qa"),
        ("Văn Nam", "acc-nam-be"),
        ("Nguyễn Văn Nam", "acc-nam-be"),
        ("Tran Hoai Nam", "acc-nam-qa"),
        ("Pham Min Duc", "acc-duc"),  # gõ thiếu chữ
        ("Nguyen Van Nma", "acc-nam-be"),  # gõ đảo chữ
        ("Le Thu Haa", "acc-ha"),
    ],
)
def test_unique(query: str, expected_id: str) -> None:
    result = match_member(query, MEMBERS)
    assert isinstance(result, Unique), result
    assert result.member.account_id == expected_id


@pytest.mark.parametrize("query", ["Nam", "nam", "anh Nam", "NAM"])
def test_two_nams_are_ambiguous(query: str) -> None:
    result = match_member(query, MEMBERS)
    assert isinstance(result, Ambiguous)
    assert {m.account_id for m in result.candidates} == {"acc-nam-be", "acc-nam-qa"}


@pytest.mark.parametrize("query", ["Lan", "Võ Thị Lan", "Minh Anh", "", "   ", "anh"])
def test_not_found(query: str) -> None:
    assert isinstance(match_member(query, MEMBERS), NotFound)


def test_inactive_member_is_ignored() -> None:
    assert isinstance(match_member("Lan", MEMBERS), NotFound)


def test_not_found_gives_close_suggestions() -> None:
    result = match_member("Phan Duc Anh", MEMBERS)
    assert isinstance(result, NotFound)
    assert [m.account_id for m in result.suggestions] == ["acc-duc"]


@pytest.mark.parametrize("query", ["Duc Pham Minh", "Pham Mihn Duc"])
def test_fuzzy_reordered_or_typo(query: str) -> None:
    result = match_member(query, MEMBERS)
    assert isinstance(result, Unique)
    assert result.member.account_id == "acc-duc"


def test_extra_words_are_not_a_match() -> None:
    assert not isinstance(match_member("Pham Duc Minh Anh", MEMBERS), Unique)


def test_empty_member_list() -> None:
    assert isinstance(match_member("Nam", []), NotFound)
