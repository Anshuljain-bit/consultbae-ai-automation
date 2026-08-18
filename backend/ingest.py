from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from backend.config import DEFAULT_SOURCE1, DEFAULT_SOURCE2, DEFAULT_SOURCE3
    from backend.db import Base, engine, session_scope
    from backend.models import Person, PersonEmail, PersonPhone, PersonSkill, Skill, SourceRecord
    from backend.normalize import (
        clean_string,
        display_name,
        is_blank,
        jsonable,
        normalize_city,
        normalize_email,
        normalize_name,
        normalize_phone,
        parse_bool,
        parse_ctc,
        parse_date,
        parse_float,
        parse_int,
        parse_rate,
        split_skills,
    )
else:
    from .config import DEFAULT_SOURCE1, DEFAULT_SOURCE2, DEFAULT_SOURCE3
    from .db import Base, engine, session_scope
    from .models import Person, PersonEmail, PersonPhone, PersonSkill, Skill, SourceRecord
    from .normalize import (
        clean_string,
        display_name,
        is_blank,
        jsonable,
        normalize_city,
        normalize_email,
        normalize_name,
        normalize_phone,
        parse_bool,
        parse_ctc,
        parse_date,
        parse_float,
        parse_int,
        parse_rate,
        split_skills,
    )


@dataclass
class NormalizedRecord:
    source_name: str
    source_row_number: int
    raw: dict[str, Any]
    name: str
    normalized_name: str
    email: str | None = None
    phone: str | None = None
    city_raw: str | None = None
    city_canonical: str | None = None
    skills: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


def looks_shifted_source2(row: pd.Series) -> bool:
    return (
        normalize_email(row.get("worker_name")) is not None
        and clean_string(row.get("rate")) is not None
        and parse_rate(row.get("location")) != (None, None)
    )


def clean_raw(row: pd.Series) -> dict[str, Any]:
    return {str(key): jsonable(value) for key, value in row.to_dict().items()}


def source1_records(path: Path) -> Iterable[NormalizedRecord]:
    df = pd.read_csv(path)
    for index, row in df.iterrows():
        row_number = index + 2
        name = display_name(row.get("Full Name"))
        normalized = normalize_name(name)
        city_raw, city_canonical = normalize_city(row.get("City"))
        issues = []
        if not normalized:
            issues.append("missing name")
        email = normalize_email(row.get("Email"))
        if not email:
            issues.append("invalid or missing email")
        phone = normalize_phone(row.get("Phone"))
        if not phone:
            issues.append("invalid or missing phone")
        applied_date = parse_date(row.get("Applied Date"))
        if applied_date is None:
            issues.append("unparseable applied date")
        if not normalized:
            continue
        yield NormalizedRecord(
            source_name="source1_naukri_applicants",
            source_row_number=row_number,
            raw=clean_raw(row),
            name=name or normalized,
            normalized_name=normalized,
            email=email,
            phone=phone,
            city_raw=city_raw,
            city_canonical=city_canonical,
            skills=split_skills(row.get("Skills")),
            fields={
                "experience_years": parse_float(row.get("Experience (Years)")),
                "current_ctc": parse_ctc(row.get("Current CTC")),
                "applied_date": applied_date,
            },
            issues=issues,
        )


def source2_records(path: Path) -> Iterable[NormalizedRecord]:
    df = pd.read_csv(path)
    for index, row in df.iterrows():
        row_number = index + 2
        issues = []
        if all(is_blank(value) for value in row.to_dict().values()):
            continue
        if looks_shifted_source2(row):
            original = row.copy()
            row = pd.Series(
                {
                    "email_id": original.get("worker_name"),
                    "worker_name": original.get("rate"),
                    "rate": original.get("location"),
                    "location": original.get("status"),
                    "status": original.get("skill_tags"),
                    "skill_tags": original.get("email_id"),
                }
            )
            issues.append("repaired shifted source2 row")

        name = display_name(row.get("worker_name"))
        normalized = normalize_name(name)
        city_raw, city_canonical = normalize_city(row.get("location"))
        email = normalize_email(row.get("email_id"))
        rate_amount, rate_period = parse_rate(row.get("rate"))
        if not normalized:
            issues.append("missing worker name")
        if not email:
            issues.append("invalid or missing email")
        if rate_amount is None:
            issues.append("unparseable rate")
        if not city_canonical:
            issues.append("missing location")
        if not normalized:
            continue
        yield NormalizedRecord(
            source_name="source2_gig_workers",
            source_row_number=row_number,
            raw=clean_raw(row),
            name=name or normalized,
            normalized_name=normalized,
            email=email,
            city_raw=city_raw,
            city_canonical=city_canonical,
            skills=split_skills(row.get("skill_tags")),
            fields={
                "gig_rate_amount": rate_amount,
                "gig_rate_period": rate_period,
                "gig_status": clean_string(row.get("status")).lower() if clean_string(row.get("status")) else None,
            },
            issues=issues,
        )


def source3_records(path: Path) -> Iterable[NormalizedRecord]:
    df = pd.read_csv(path)
    for index, row in df.iterrows():
        row_number = index + 2
        issues = []
        if str(row.get("Name")).strip().lower() == "name":
            continue
        name = display_name(row.get("Name"))
        normalized = normalize_name(name)
        phone = normalize_phone(row.get("Phone Number"))
        city_raw, city_canonical = normalize_city(row.get("City"))
        verified = parse_bool(row.get("Verified"))
        if not normalized:
            issues.append("missing name")
        if not phone:
            issues.append("invalid or missing phone")
        if verified is None:
            issues.append("unparseable verified flag")
        if not normalized:
            continue
        yield NormalizedRecord(
            source_name="source3_cbnexus_contacts",
            source_row_number=row_number,
            raw=clean_raw(row),
            name=name or normalized,
            normalized_name=normalized,
            phone=phone,
            city_raw=city_raw,
            city_canonical=city_canonical,
            fields={
                "cb_verified": verified,
                "projects_completed": parse_int(row.get("Projects Completed")),
            },
            issues=issues,
        )


def find_person(session: Session, record: NormalizedRecord) -> tuple[Person | None, str]:
    if record.email:
        email_match = session.scalar(select(PersonEmail).where(PersonEmail.email == record.email))
        if email_match:
            return email_match.person, "exact_email"

    if record.phone:
        phone_match = session.scalar(select(PersonPhone).where(PersonPhone.phone_e164 == record.phone))
        if phone_match:
            return phone_match.person, "exact_phone"

    if record.normalized_name and record.city_canonical:
        candidates = session.scalars(
            select(Person).where(
                Person.normalized_name == record.normalized_name,
                Person.city_canonical == record.city_canonical,
            )
        ).all()
        viable = []
        for candidate in candidates:
            if record.phone and candidate.primary_phone and candidate.primary_phone != record.phone:
                continue
            viable.append(candidate)
        if len(viable) == 1:
            return viable[0], "name_city_unique"
        if len(candidates) > 1:
            record.issues.append(f"ambiguous name+city candidates: {[candidate.id for candidate in candidates]}")

    return None, "new_person"


def choose_better_name(existing: str, incoming: str) -> str:
    if len(incoming) > len(existing):
        return incoming
    return existing


def upsert_identifier(session: Session, model: type[PersonEmail] | type[PersonPhone], field: str, person: Person, value: str, issues: list[str]) -> None:
    existing = session.scalar(select(model).where(getattr(model, field) == value))
    if existing:
        if existing.person_id != person.id:
            issues.append(f"identifier conflict for {value}: already belongs to person {existing.person_id}")
        return
    session.add(model(person_id=person.id, **{field: value}))


def get_or_create_skill(session: Session, name: str) -> Skill:
    skill = session.scalar(select(Skill).where(Skill.name == name))
    if skill:
        return skill
    skill = Skill(name=name)
    session.add(skill)
    session.flush()
    return skill


def apply_record(session: Session, record: NormalizedRecord) -> tuple[Person, str]:
    person, strategy = find_person(session, record)
    if person is None:
        person = Person(
            full_name=record.name,
            normalized_name=record.normalized_name,
            primary_email=record.email,
            primary_phone=record.phone,
            city_raw=record.city_raw,
            city_canonical=record.city_canonical,
        )
        session.add(person)
        session.flush()
    else:
        person.full_name = choose_better_name(person.full_name, record.name)
        if record.email and not person.primary_email:
            person.primary_email = record.email
        if record.phone and not person.primary_phone:
            person.primary_phone = record.phone
        if record.city_canonical and not person.city_canonical:
            person.city_raw = record.city_raw
            person.city_canonical = record.city_canonical

    if record.email:
        upsert_identifier(session, PersonEmail, "email", person, record.email, record.issues)
    if record.phone:
        upsert_identifier(session, PersonPhone, "phone_e164", person, record.phone, record.issues)

    for field_name, value in record.fields.items():
        if value is not None and getattr(person, field_name, None) is None:
            setattr(person, field_name, value)

    for skill_name in record.skills:
        skill = get_or_create_skill(session, skill_name)
        exists = session.scalar(
            select(PersonSkill).where(
                PersonSkill.person_id == person.id,
                PersonSkill.skill_id == skill.id,
            )
        )
        if not exists:
            session.add(PersonSkill(person_id=person.id, skill_id=skill.id))

    session.add(
        SourceRecord(
            person_id=person.id,
            source_name=record.source_name,
            source_row_number=record.source_row_number,
            match_strategy=strategy,
            issue_notes="; ".join(record.issues) if record.issues else None,
            raw_json=json.dumps(record.raw, default=str),
        )
    )
    session.flush()
    return person, strategy


def iter_all_records(paths: dict[str, Path]) -> Iterable[NormalizedRecord]:
    yield from source1_records(paths["source1"])
    yield from source2_records(paths["source2"])
    yield from source3_records(paths["source3"])


def scalar_count(session: Session, stmt: Select) -> int:
    value = session.scalar(stmt)
    return int(value or 0)


def ingest(paths: dict[str, Path], reset: bool = False) -> dict[str, Any]:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    strategies: dict[str, int] = {}
    issue_count = 0
    with session_scope() as session:
        for record in iter_all_records(paths):
            _, strategy = apply_record(session, record)
            strategies[strategy] = strategies.get(strategy, 0) + 1
            if record.issues:
                issue_count += 1

        summary = {
            "people": scalar_count(session, select(func.count(Person.id))),
            "emails": scalar_count(session, select(func.count(PersonEmail.id))),
            "phones": scalar_count(session, select(func.count(PersonPhone.id))),
            "skills": scalar_count(session, select(func.count(Skill.id))),
            "source_records": scalar_count(session, select(func.count(SourceRecord.id))),
            "records_with_issue_notes": issue_count,
            "match_strategies": strategies,
        }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest ConsultBae CSV sources into MySQL.")
    parser.add_argument("--source1", type=Path, default=DEFAULT_SOURCE1)
    parser.add_argument("--source2", type=Path, default=DEFAULT_SOURCE2)
    parser.add_argument("--source3", type=Path, default=DEFAULT_SOURCE3)
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables before ingesting.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {"source1": args.source1, "source2": args.source2, "source3": args.source3}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing input file(s): {missing}")
    summary = ingest(paths, reset=args.reset)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
