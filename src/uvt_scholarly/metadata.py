# SPDX-FileCopyrightText: 2026 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from uvt_scholarly.identifiers import GoogleScholarID, ORCiD, ResearcherID, ScopusID
from uvt_scholarly.logging import make_logger
from uvt_scholarly.qs import UNIVERSITY_RANKING_ID, UniversityRanking

if TYPE_CHECKING:
    from collections.abc import Sequence

    from uvt_scholarly.publication import Category, Publication

log = make_logger(__name__)

LATEST_METADATA_VERSION = 1

# {{{ helpers


def _parse_period_v1(period: object) -> tuple[int, int]:
    if not isinstance(period, list) or len(period) != 2:
        raise ValueError(f"'period' is not a two-tuple: {period!r}")

    return int(period[0]), int(period[1])


# }}}


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

POSITION_TO_ID = {v: k for k, v in ID_TO_POSITION.items()}

# }}}


# {{{ Scope


@enum.unique
class Scope(enum.Enum):
    """Geographic scope of a role or activity."""

    International = enum.auto()
    National = enum.auto()
    Local = enum.auto()


ID_TO_SCOPE = {
    "international": Scope.International,
    "national": Scope.National,
    "local": Scope.Local,
}


# }}}


# {{{ JournalAffiliation


@enum.unique
class JournalPosition(enum.Enum):
    EditorInChief = enum.auto()
    Editor = enum.auto()
    BoardMember = enum.auto()
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


def _parse_journals_v1(
    entries: Sequence[dict[str, Any]],
) -> tuple[JournalAffiliation, ...]:
    return ()


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
    competition: Scope | None
    """The scope of the competition through which the grant was obtained."""
    period: tuple[int, int]
    """The period that the author was part of this grant."""
    url: str | None
    """A URL for the project or a link to the funder's page for this grant."""


ID_TO_GRANT_ROLE = {
    "director": GrantRole.Director,
    "member": GrantRole.Member,
}


def _parse_grants_v1(entries: Sequence[dict[str, Any]]) -> tuple[Grant, ...]:
    def parse_organization(organization: object) -> Organization:
        if isinstance(organization, str):
            return Organization(name=organization.strip())

        if isinstance(organization, dict) and (name := organization.get("name")):
            identifier = organization.get("identifier")
            return Organization(
                name=str(name).strip(),
                identifier=str(identifier).strip() if identifier else None,
            )

        raise ValueError(
            f"'organization' is not a valid organization: {organization!r}"
        )

    def parse_amount(amount: object) -> Money | None:
        if amount is None:
            return None

        if isinstance(amount, dict):
            return Money(
                value=float(amount["value"]),
                currency=str(amount.get("currency", "EUR")).upper(),
            )

        raise ValueError(f"'amount' is not a valid amount: {amount!r}")

    grants = []
    for i, d in enumerate(entries):
        title = d.get("title", d.get("name"))
        if not title:
            log.error("Grant '%d' has no title. Skipping...", i)
            continue

        title = str(title).strip()
        try:
            role = ID_TO_GRANT_ROLE[str(d.get("role", "member")).strip().lower()]
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
                        ID_TO_SCOPE[str(competition).strip().lower()]
                        if competition
                        else None
                    ),
                    period=_parse_period_v1(d["period"]),
                    url=url.strip() if (url := d.get("url")) else None,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.error("Failed to read grant %d: '%s'.", i, title, exc_info=exc)
            continue

    return tuple(grants)


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

    This is used for conference committees, organizing committees, keynote or
    invited talks. The scoring category and university ranking are mutually
    exclusive, depending on [kind][]: events use [category][], while
    universities use [ranking][].
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


def _parse_conference_committee_v1(
    entries: Sequence[dict[str, Any]],
) -> tuple[Event, ...]:
    return ()


def _parse_events_v1(entries: Sequence[dict[str, Any]]) -> tuple[Event, ...]:
    return ()


def _parse_keynotes_v1(entries: Sequence[dict[str, Any]]) -> tuple[Event, ...]:
    return ()


# }}}


# {{{ Role


@enum.unique
class RoleKind(enum.Enum):
    Visit = enum.auto()
    Team = enum.auto()
    Leadership = enum.auto()


ID_TO_ROLE_KIND = {
    "visit": RoleKind.Visit,
    "team": RoleKind.Team,
    "leadership": RoleKind.Leadership,
}


@dataclass(frozen=True, slots=True)
class Role:
    """A longer-lived role at an organization.

    This is used for visiting positions, research teams, and leadership
    positions in professional organizations.
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
    """The geographic scope of the role."""
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


def _parse_visiting_v1(entries: Sequence[dict[str, Any]]) -> tuple[Role, ...]:
    visiting = []
    for i, d in enumerate(entries):
        name = d.get("name")
        if not name:
            log.error("Visiting position %d has no name. Skipping...", i)
            continue

        name = str(name).strip()
        try:
            visiting.append(
                Role(
                    name=name,
                    kind=ID_TO_ROLE_KIND[str(d["kind"]).strip().lower()],
                    role=str(d["role"]).strip(),
                    country=d.get("country"),
                    ranking=(
                        UNIVERSITY_RANKING_ID[str(d["ranking"]).strip().lower()]
                        if d.get("ranking")
                        else None
                    ),
                    period=_parse_period_v1(d["period"]) if "period" in d else None,
                    duration_months=(
                        int(d["duration_months"]) if "duration_months" in d else None
                    ),
                    teaching_hours=(
                        int(d["teaching_hours"]) if "teaching_hours" in d else None
                    ),
                    url=d.get("url"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.error(
                "Failed to read visiting position %d: '%s'.", i, name, exc_info=exc
            )
            continue

    return tuple(visiting)


def _parse_teams_v1(entries: Sequence[dict[str, Any]]) -> tuple[Role, ...]:
    return ()


def _parse_leadership_v1(entries: Sequence[dict[str, Any]]) -> tuple[Role, ...]:
    return ()


# }}}


# {{{ DoctoralCommittee


@enum.unique
class DoctoralRole(enum.Enum):
    Supervisor = enum.auto()
    Member = enum.auto()
    Evaluator = enum.auto()


ID_TO_DOCTORAL_ROLE = {
    "supervisor": DoctoralRole.Supervisor,
    "member": DoctoralRole.Member,
    "evaluator": DoctoralRole.Evaluator,
}


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


def _parse_phd_evaluation_v1(
    entries: Sequence[dict[str, Any]],
) -> tuple[DoctoralCommittee, ...]:
    return ()


def _parse_phd_committee_v1(
    entries: Sequence[dict[str, Any]],
) -> tuple[DoctoralCommittee, ...]:
    committees = []
    for i, d in enumerate(entries):
        student = d.get("student")
        if not student:
            log.error("Doctoral committee entry %d has no student. Skipping...", i)
            continue

        student = str(student).strip()
        try:
            committees.append(
                DoctoralCommittee(
                    university=str(d["university"]).strip(),
                    role=ID_TO_DOCTORAL_ROLE[str(d["role"]).strip().lower()],
                    student=student,
                    year=int(d["year"]),
                    thesis=d.get("thesis"),
                    ranking=(
                        UNIVERSITY_RANKING_ID[str(d["ranking"]).strip().lower()]
                        if d.get("ranking")
                        else None
                    ),
                    doctoral_school_decision=d.get("doctoral_school_decision"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.error(
                "Failed to read doctoral committee %d: '%s'.", i, student, exc_info=exc
            )
            continue

    return tuple(committees)


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


def _parse_patents_v1(entries: Sequence[dict[str, Any]]) -> tuple[Patent, ...]:
    return ()


# }}}


# {{{ Software


@enum.unique
class SoftwareKind(enum.Enum):
    Package = enum.auto()
    Tool = enum.auto()
    Resource = enum.auto()
    Dataset = enum.auto()
    Other = enum.auto()


ID_TO_SOFTWARE_KIND = {
    "package": SoftwareKind.Package,
    "tool": SoftwareKind.Tool,
    "resource": SoftwareKind.Resource,
    "dataset": SoftwareKind.Dataset,
    "other": SoftwareKind.Other,
}


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


def _parse_software_v1(entries: Sequence[dict[str, Any]]) -> tuple[Software, ...]:
    software = []
    for i, d in enumerate(entries):
        name = d.get("name")
        if not name:
            log.error("Software entry %d has no name. Skipping...", i)
            continue

        name = str(name).strip()
        try:
            software.append(
                Software(
                    name=name,
                    kind=ID_TO_SOFTWARE_KIND[str(d["kind"]).strip().lower()],
                    authors=tuple(str(author).strip() for author in d["authors"]),
                    year=int(d["year"]) if "year" in d else None,
                    license=d.get("license"),
                    accesses=int(d["accesses"]) if "accesses" in d else None,
                    url=d.get("url"),
                    doi=d.get("doi"),
                    description=d.get("description"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.error("Failed to read software %d: '%s'.", i, name, exc_info=exc)
            continue

    return tuple(software)


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


def _parse_awards_v1(entries: Sequence[dict[str, Any]]) -> tuple[Award, ...]:
    return ()


# }}}


# {{{ Recommendation


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A recommendation letter."""

    position: str
    name: str
    university: str
    email: str


def _parse_recommendations_v1(
    entries: Sequence[dict[str, Any]],
) -> tuple[Recommendation, ...]:
    recommendations = []
    for i, d in enumerate(entries):
        name = d.get("name")
        if not name:
            log.error("Recommendation %d has no name. Skipping...", i)
            continue

        name = str(name).strip()
        try:
            recommendations.append(
                Recommendation(
                    position=str(d["position"]).strip(),
                    name=name,
                    university=str(d["university"]).strip(),
                    email=str(d["email"]).strip(),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.error("Failed to read recommendation %d: '%s'.", i, name, exc_info=exc)
            continue

    return tuple(recommendations)


# }}}


# {{{ HirschIndex


@dataclass(frozen=True, slots=True)
class HirschIndex:
    wos: int
    scopus: int
    google_scholar: int
    as_of: int


def _parse_hirsch_index_v1(data: dict[str, Any] | None) -> HirschIndex | None:
    if not data:
        return None

    if "as_of" not in data:
        raise ValueError("'HirschIndex' requires the 'as_of' field")

    return HirschIndex(
        wos=int(data.get("wos", 0)),
        scopus=int(data.get("scopus", 0)),
        google_scholar=int(data.get("google_scholar", 0)),
        as_of=int(data["as_of"]),
    )


# }}}


# {{{ Candidate


@dataclass(frozen=True, slots=True)
class Candidate:
    first_name: str
    last_name: str
    target: Position

    publications: tuple[Publication, ...]
    citations: tuple[Publication, ...]

    books: tuple[Publication, ...]
    proceedings: tuple[Publication, ...]
    courses: tuple[Publication, ...]
    journals: tuple[JournalAffiliation, ...]
    grants: tuple[Grant, ...]
    conference_committee: tuple[Event, ...]
    events: tuple[Event, ...]
    keynotes: tuple[Event, ...]
    visiting: tuple[Role, ...]
    teams: tuple[Role, ...]
    phd_evaluation: tuple[DoctoralCommittee, ...]
    phd_committee: tuple[DoctoralCommittee, ...]
    patents: tuple[Patent, ...]
    software: tuple[Software, ...]
    leadership: tuple[Role, ...]
    awards: tuple[Award, ...]
    recommendations: tuple[Recommendation, ...]

    email: str | None = None
    orcid: ORCiD | None = None
    researcher_id: ResearcherID | None = None
    scopus_id: ScopusID | None = None
    google_scholar_id: GoogleScholarID | None = None
    hirsch: HirschIndex | None = None


# }}}


# {{{ read_candidate


def _parse_books_v1(entries: Sequence[dict[str, Any]]) -> tuple[Publication, ...]:
    return ()


def _parse_proceedings_v1(entries: Sequence[dict[str, Any]]) -> tuple[Publication, ...]:
    return ()


def _parse_courses_v1(entries: Sequence[dict[str, Any]]) -> tuple[Publication, ...]:
    return ()


def _read_candidate_v1(
    candidate: dict[str, Any], cwd: pathlib.Path | None = None
) -> Candidate:
    if cwd is None:
        cwd = pathlib.Path.cwd()

    def resolve_path(filename: str) -> pathlib.Path:
        path = pathlib.Path(filename)
        return path if path.is_absolute() else cwd / path

    # {{{ parse candidate metadata

    # FIXME: move this to separate function

    first_name = candidate.get("first_name", "#FirstName#")
    last_name = candidate.get("last_name", "#LastName#")
    target_raw = str(candidate.get("target", "assi")).strip().lower()
    email = candidate.get("email", "candidate@example.com")
    orcid_raw = candidate.get("orcid")
    researcher_id_raw = candidate.get("researcher_id")
    scopus_id_raw = candidate.get("scopus_id")
    google_scholar_id_raw = candidate.get("google_scholar_id")

    try:
        target = ID_TO_POSITION[target_raw]
    except KeyError:
        target = Position.Assistant

    orcid = None
    if orcid_raw is not None:
        orcid = ORCiD.from_string(orcid_raw)

    researcher_id = None
    if researcher_id_raw is not None:
        researcher_id = ResearcherID.from_string(researcher_id_raw)

    scopus_id = None
    if scopus_id_raw is not None:
        scopus_id = ScopusID.from_string(scopus_id_raw)

    google_scholar_id = None
    if google_scholar_id_raw is not None:
        google_scholar_id = GoogleScholarID.from_string(google_scholar_id_raw)

    # }}}

    # {{{ parse sources

    # FIXME: move this to separate function

    from uvt_scholarly.wos import read_pubs

    sources = candidate.get("sources", {})

    publications = []
    for entries in sources.get("publications", []):
        source = entries.get("source")
        if source == "wos":
            for filename in entries.get("files", []):
                path = resolve_path(filename)
                if not path.exists():
                    log.error("File does not exist: '%s'.", path)
                    continue

                publications.extend(read_pubs(path))
        else:
            raise ValueError(f"unknown source type: {source!r}")

    citations = []
    for entries in sources.get("citations", []):
        source = entries.get("source")
        if source == "wos":
            for filename in entries.get("files", []):
                path = resolve_path(filename)
                if not path.exists():
                    log.error("File does not exist: '%s'.", path)
                    continue

                citations.extend(read_pubs(path, include_citations=True))
        else:
            raise ValueError(f"unknown source type: {source!r}")

    # }}}

    return Candidate(
        first_name=first_name,
        last_name=last_name,
        target=target,
        email=email,
        orcid=orcid,
        researcher_id=researcher_id,
        scopus_id=scopus_id,
        google_scholar_id=google_scholar_id,
        hirsch=_parse_hirsch_index_v1(candidate.get("hirsch")),
        publications=tuple(publications),
        citations=tuple(citations),
        books=_parse_books_v1(candidate.get("books", [])),
        proceedings=_parse_proceedings_v1(candidate.get("proceedings", [])),
        courses=_parse_courses_v1(candidate.get("courses", [])),
        journals=_parse_journals_v1(candidate.get("journals", [])),
        grants=_parse_grants_v1(candidate.get("grants", [])),
        conference_committee=_parse_conference_committee_v1(
            candidate.get("conference_committee", [])
        ),
        events=_parse_events_v1(candidate.get("events", [])),
        keynotes=_parse_keynotes_v1(candidate.get("keynotes", [])),
        visiting=_parse_visiting_v1(candidate.get("visiting", [])),
        teams=_parse_teams_v1(candidate.get("teams", [])),
        phd_evaluation=_parse_phd_evaluation_v1(candidate.get("phd_evaluation", [])),
        phd_committee=_parse_phd_committee_v1(candidate.get("phd_committee", [])),
        patents=_parse_patents_v1(candidate.get("patents", [])),
        software=_parse_software_v1(candidate.get("software", [])),
        leadership=_parse_leadership_v1(candidate.get("leadership", [])),
        awards=_parse_awards_v1(candidate.get("awards", [])),
        recommendations=_parse_recommendations_v1(candidate.get("recommendations", [])),
    )


def read_candidate(
    filename: pathlib.Path,
    *,
    cwd: pathlib.Path | None = None,
) -> Candidate:
    if not filename.exists():
        raise FileNotFoundError(filename)

    if cwd is None:
        cwd = filename.parent

    import tomllib

    with open(filename, "rb") as fp:
        data = tomllib.load(fp)

    # FIXME: add a json schema and check it here

    version = data.get("metadata", {}).get("version", LATEST_METADATA_VERSION)
    if version == 1:
        return _read_candidate_v1(data.get("candidate", {}), cwd=cwd)
    else:
        raise ValueError(
            f"candidate file has unsupported version '{version}': '{filename}'"
        )


# }}}
