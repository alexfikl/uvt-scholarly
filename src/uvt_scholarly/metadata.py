# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uvt_scholarly.logging import make_logger

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

    from uvt_scholarly.publication import Category, Publication

log = make_logger(__name__)


# {{{ Position


@enum.unique
class Position(enum.Enum):
    Professor = enum.auto()
    AssociateProfessor = enum.auto()
    AssistantProfessor = enum.auto()
    Assistant = enum.auto()

    SeniorResearcher = enum.auto()
    Researcher = enum.auto()
    JuniorResearcher = enum.auto()


POSITION_NAME = {
    # academic
    Position.Professor: "Profesor Universitar",  # spell: disable
    Position.AssociateProfessor: "Conferențiar",
    Position.AssistantProfessor: "Lector",
    Position.Assistant: "Asistent Universitar",
    # research
    Position.SeniorResearcher: "Cercetător Științific I",
    Position.Researcher: "Cercetător Științific II",
    Position.JuniorResearcher: "Cercetător Științific III",
}

POSITION_SHORT_NAME = {
    Position.Professor: "Prof. Dr.",
    Position.AssociateProfessor: "Conf. Dr.",
    Position.AssistantProfessor: "Lect. Dr.",
    Position.Assistant: "Ass.",
    # research
    Position.SeniorResearcher: "C.S. I",
    Position.Researcher: "C.S. II",
    Position.JuniorResearcher: "C.S. III",
}

ID_TO_POSITION = {
    "prof": Position.Professor,
    "conf": Position.AssociateProfessor,
    "lect": Position.AssistantProfessor,
    "assi": Position.Assistant,
    "cs1": Position.SeniorResearcher,
    "cs2": Position.Researcher,
    "cs3": Position.JuniorResearcher,
}

# }}}


# {{{ Categories


@enum.unique
class PublisherCategory(enum.Enum):
    """SENSE category of a book publisher."""

    A = enum.auto()
    B = enum.auto()
    C = enum.auto()
    D = enum.auto()
    E = enum.auto()
    Unlisted = enum.auto()


@enum.unique
class UniversityRanking(enum.Enum):
    """Ranking bucket of a university, as used by the CS standards."""

    Top20 = enum.auto()
    Top100 = enum.auto()
    Top200 = enum.auto()
    Top500 = enum.auto()
    Above500 = enum.auto()


@enum.unique
class Scope(enum.Enum):
    """Geographic or institutional scope of a role or activity."""

    International = enum.auto()
    National = enum.auto()
    Institutional = enum.auto()


@enum.unique
class CompetitionScope(enum.Enum):
    """Scope of the competition through which a grant was obtained."""

    International = enum.auto()
    National = enum.auto()


# }}}


# {{{ JournalAffiliation


@enum.unique
class JournalPosition(enum.Enum):
    Director = enum.auto()
    Editor = enum.auto()
    Member = enum.auto()
    GuestEditor = enum.auto()


@dataclass(frozen=True, slots=True)
class JournalAffiliation:
    """An editorial role at a journal."""

    journal: str
    role: JournalPosition
    category: Category
    year: int | None = None
    issn: str | None = None
    url: str | None = None


# }}}


# {{{ Grant


@enum.unique
class GrantRole(enum.Enum):
    Director = enum.auto()
    Member = enum.auto()


@dataclass(frozen=True, slots=True)
class Organization:
    """A named organization, optionally with a unique identifier."""

    name: str
    identifier: str | None = None


@dataclass(frozen=True, slots=True)
class Money:
    """A monetary amount."""

    value: float
    currency: str = "EUR"


@dataclass(frozen=True, slots=True)
class Grant:
    """A grant that an author was part of."""

    title: str
    """The full title of the grant (this can contain an acronym)."""
    role: GrantRole
    """The role of the author in the grant."""
    funder: Organization
    """The organization that funded the grant."""
    identifier: str | None
    """The contract or grant number used by the funder."""
    amount: Money | None
    """The amount that entered the institution."""
    competition: CompetitionScope | None
    """The scope of the competition through which the grant was obtained."""
    period: tuple[int, int]
    """The period that the author was part of this grant."""
    url: str | None
    """A URL for the project or a link to the funder's page for this grant."""


# }}}


# {{{ Event


@enum.unique
class EventKind(enum.Enum):
    Conference = enum.auto()
    Workshop = enum.auto()
    Symposium = enum.auto()
    SummerSchool = enum.auto()
    University = enum.auto()
    Other = enum.auto()


@enum.unique
class EventRole(enum.Enum):
    Director = enum.auto()
    OrganizingCommittee = enum.auto()
    ProgramCommittee = enum.auto()
    ScientificCommittee = enum.auto()
    Keynote = enum.auto()
    Invited = enum.auto()
    Professor = enum.auto()


@dataclass(frozen=True, slots=True)
class Event:
    """An event participation that is not covered by [Role][].

    This is used for conference committees (d.vi), organizing committees (d.vii),
    and keynote/invited talks (d.viii). The scoring category and university
    ranking are mutually exclusive, depending on [kind][]:
    events use [category][], while universities use [ranking][].
    """

    name: str
    """The event name, or the host university for university visits."""
    kind: EventKind
    """The kind of event."""
    role: EventRole
    """The role of the candidate at the event."""
    year: int
    """The year in which the event took place."""
    category: Category | None = None
    """The forum category, for conference-like events."""
    ranking: UniversityRanking | None = None
    """The university ranking, for university-hosted events."""
    title: str | None = None
    """The title of the talk, for keynotes and invited talks."""
    location: str | None = None
    """The location of the event."""
    url: str | None = None
    """A URL with more information about the event or talk."""


# }}}


# {{{ Role


@enum.unique
class RoleKind(enum.Enum):
    Visit = enum.auto()
    Team = enum.auto()
    Leadership = enum.auto()


@dataclass(frozen=True, slots=True)
class Role:
    """A longer-lived role at an organization.

    This is used for visiting positions (d.ix), research teams (d.x), and
    leadership positions in professional organizations (d.xv).
    """

    name: str
    """The university, team, or organization name."""
    kind: RoleKind
    """The kind of role."""
    role: str
    """The title of the role, e.g. ``"visiting"``, ``"leader"``, or
    ``"president"``.
    """
    scope: Scope | None = None
    """The geographic or institutional scope of the role."""
    ranking: UniversityRanking | None = None
    """The university ranking, for visiting positions."""
    country: str | None = None
    """The country of the host university, for visiting positions."""
    period: tuple[int, int] | None = None
    """The period in which the role was held."""
    duration_months: int | None = None
    """The duration of the role in months."""
    teaching_hours: int | None = None
    """Teaching hours that can be converted to months, for short visits."""
    team_size: int | None = None
    """The number of people in the team, for research teams."""
    evidence: str | None = None
    """Evidence for the role, e.g. an accreditation or school decision."""
    url: str | None = None
    """A URL with more information about the role."""


# }}}


# {{{ DoctoralCommittee


@enum.unique
class DoctoralRole(enum.Enum):
    Supervisor = enum.auto()
    Member = enum.auto()
    Evaluator = enum.auto()


@dataclass(frozen=True, slots=True)
class DoctoralCommittee:
    """A role in a doctoral evaluation or supervision committee."""

    university: str
    role: DoctoralRole
    student: str
    year: int
    thesis: str | None = None
    ranking: UniversityRanking | None = None
    doctoral_school_decision: str | None = None


# }}}


# {{{ Patent


@enum.unique
class PatentStatus(enum.Enum):
    Active = enum.auto()
    Granted = enum.auto()
    Filed = enum.auto()
    Expired = enum.auto()
    Unknown = enum.auto()


@dataclass(frozen=True, slots=True)
class Patent:
    title: str
    inventors: tuple[str, ...]
    year: int
    status: PatentStatus
    identifier: str | None = None
    office: str | None = None
    url: str | None = None
    description: str | None = None


# }}}


# {{{ Software


@enum.unique
class SoftwareKind(enum.Enum):
    Package = enum.auto()
    Tool = enum.auto()
    Resource = enum.auto()
    Dataset = enum.auto()
    Other = enum.auto()


@dataclass(frozen=True, slots=True)
class Software:
    name: str
    kind: SoftwareKind
    authors: tuple[str, ...]
    year: int | None = None
    license: str | None = None
    accesses: int | None = None
    url: str | None = None
    doi: str | None = None
    description: str | None = None


# }}}


# {{{ Award


@dataclass(frozen=True, slots=True)
class Award:
    title: str
    year: int
    organization: str | None = None
    points: float | None = None
    url: str | None = None
    description: str | None = None


# }}}


# {{{ Recommendation


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A C5 recommendation letter."""

    position: str
    name: str
    university: str
    email: str


# }}}


# {{{ Sources


@dataclass(frozen=True, slots=True)
class Source:
    source: str
    """The source format, e.g. ``"wos"`` or ``"bib"``."""
    files: tuple[str, ...]
    """The files that make up this source."""


@dataclass(frozen=True, slots=True)
class Sources:
    publications: Sequence[Source] = ()
    citations: Sequence[Source] = ()


# }}}


# {{{ HirschIndex


@dataclass(frozen=True, slots=True)
class HirschIndex:
    wos: int | None = None
    scopus: int | None = None
    google_scholar: int | None = None
    as_of: int | None = None


# }}}


# {{{ Candidate


@dataclass(frozen=True, slots=True)
class Candidate:
    first_name: str
    last_name: str
    target: Position

    sources: Sources
    publications: Sequence[Publication]
    citations: Sequence[Publication]

    books: Sequence[Publication]
    proceedings: Sequence[Publication]
    courses: Sequence[Publication]
    journals: Sequence[JournalAffiliation]
    grants: Sequence[Grant]
    conference_committee: Sequence[Event]
    events: Sequence[Event]
    keynotes: Sequence[Event]
    visiting: Sequence[Role]
    teams: Sequence[Role]
    phd_evaluation: Sequence[DoctoralCommittee]
    phd_committee: Sequence[DoctoralCommittee]
    patents: Sequence[Patent]
    software: Sequence[Software]
    leadership: Sequence[Role]
    awards: Sequence[Award]
    recommendations: Sequence[Recommendation]

    hirsch: HirschIndex | None = None
    email: str | None = None
    orcid: str | None = None
    researcher_id: str | None = None
    scopus_id: str | None = None
    google_scholar_id: str | None = None
    aliases: tuple[str, ...] = ()


# }}}


# {{{ read_candidate


def read_candidate(filename: pathlib.Path) -> None:
    if not filename.exists():
        raise FileNotFoundError(filename)


# }}}


# {{{ read_grants


def read_grants(filename: pathlib.Path) -> Sequence[Grant]:
    if not filename.exists():
        raise FileNotFoundError(filename)

    import tomllib

    with open(filename, "rb") as fp:
        data = tomllib.load(fp)

    grants_data = data.get("grants")
    if grants_data is None:
        grants_data = data.get("candidate", {}).get("grants")

    if grants_data is None:
        raise KeyError(f"key 'grants' not found in file: {filename}")

    def parse_period(period: Sequence[int]) -> tuple[int, int]:
        if not isinstance(period, list) or len(period) != 2:
            raise KeyError(f"'period' is not a two-tuple: {period!r}")

        return int(period[0]), int(period[1])

    def parse_organization(organization: object) -> Organization:
        if isinstance(organization, str):
            return Organization(name=organization.strip())

        if isinstance(organization, dict) and (name := organization.get("name")):
            identifier = organization.get("identifier")
            return Organization(
                name=str(name).strip(),
                identifier=str(identifier).strip() if identifier else None,
            )

        raise KeyError(f"'organization' is not a valid organization: {organization!r}")

    def parse_amount(amount: object) -> Money | None:
        if amount is None:
            return None

        if isinstance(amount, dict):
            return Money(
                value=float(amount["value"]),
                currency=str(amount.get("currency", "EUR")).upper(),
            )

        raise KeyError(f"'amount' is not a valid amount: {amount!r}")

    grant_roles = {
        "director": GrantRole.Director,
        "member": GrantRole.Member,
    }
    competition_scopes = {
        "international": CompetitionScope.International,
        "national": CompetitionScope.National,
    }

    grants = []
    for i, d in enumerate(grants_data):
        title = d.get("title", d.get("name"))
        if not title:
            log.error("Grant '%d' has no title. Skipping...", i)
            continue

        title = title.strip()
        try:
            role = grant_roles[str(d.get("role", "member")).strip().lower()]
            competition = d.get("competition")
            identifier = d.get("identifier", d.get("contract"))
            grants.append(
                Grant(
                    title=title,
                    role=role,
                    funder=parse_organization(d["funder"]),
                    identifier=str(identifier).strip() if identifier else None,
                    amount=parse_amount(d.get("amount")),
                    competition=(
                        competition_scopes[str(competition).strip().lower()]
                        if competition
                        else None
                    ),
                    period=parse_period(d["period"]),
                    url=url.strip() if (url := d.get("url")) else None,
                )
            )
        except KeyError as exc:
            log.error("Failed to read grant %d: '%s'.", i, title, exc_info=exc)
            continue

    return tuple(grants)


# }}}
