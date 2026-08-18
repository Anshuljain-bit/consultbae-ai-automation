import unittest

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from backend.db import Base
from backend.ingest import NormalizedRecord, apply_record
from backend.models import Person, PersonEmail, PersonPhone


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)()


def record(row_number, name, email=None, phone=None, city="Noida", issues=None):
    return NormalizedRecord(
        source_name="test_source",
        source_row_number=row_number,
        raw={"row": row_number},
        name=name,
        normalized_name=name.lower(),
        email=email,
        phone=phone,
        city_raw=city,
        city_canonical=city,
        skills=["python"],
        issues=issues or [],
    )


class MatchingTests(unittest.TestCase):
    def test_exact_email_merges_people_and_adds_phone(self):
        session = make_session()
        first, first_strategy = apply_record(
            session,
            record(2, "Asha Rao", email="asha@example.com", phone="+919000000001"),
        )
        second, second_strategy = apply_record(
            session,
            record(3, "Asha Rao", email="asha@example.com", phone="+919000000002"),
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(first_strategy, "new_person")
        self.assertEqual(second_strategy, "exact_email")
        self.assertEqual(session.scalar(select(func.count(Person.id))), 1)
        self.assertEqual(session.scalar(select(func.count(PersonPhone.id))), 2)

    def test_exact_phone_merges_alternate_emails(self):
        session = make_session()
        first, _ = apply_record(
            session,
            record(2, "Nikhil Chopra", email="nikhil@example.com", phone="+919000000070"),
        )
        second, strategy = apply_record(
            session,
            record(3, "Nikhil Chopra", email="alt.nikhil@example.com", phone="+919000000070"),
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(strategy, "exact_phone")
        emails = session.scalars(select(PersonEmail.email).order_by(PersonEmail.email)).all()
        self.assertEqual(emails, ["alt.nikhil@example.com", "nikhil@example.com"])

    def test_name_city_does_not_merge_phone_conflict(self):
        session = make_session()
        first, _ = apply_record(session, record(2, "Arjun Mehta", phone="+919000000131"))
        second, strategy = apply_record(session, record(3, "Arjun Mehta", phone="+919000000999"))

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(strategy, "new_person")
        self.assertEqual(session.scalar(select(func.count(Person.id))), 2)


if __name__ == "__main__":
    unittest.main()
