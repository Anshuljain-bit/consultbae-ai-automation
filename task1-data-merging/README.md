# Task 1 - Data Merging

## Objective

Merge three CSV datasets into one clean MySQL database while resolving duplicate people across systems that do not share a universal ID.

## Inputs

Raw files are stored in `data/raw/`:

- `source1_naukri_applicants.csv`
- `source2_gig_workers.csv`
- `source3_cbnexus_contacts.csv`

## Implementation

The ingestion code lives in `backend/`:

- `backend/ingest.py`: source-specific ingestion, record repair, matching, and upsert flow.
- `backend/normalize.py`: field normalization and parsing helpers.
- `backend/models.py`: SQLAlchemy models for people, identifiers, skills, source lineage, and audio submissions.
- `task1-data-merging/sql/schema.sql`: MySQL reference schema.

## Matching Rules

1. Exact normalized email.
2. Exact normalized phone.
3. Exact normalized name plus canonical city only when there is exactly one safe candidate.
4. New canonical person otherwise.

The pipeline avoids loose fuzzy matching because the source data includes same-name and same-city collisions.

## Run

```powershell
docker compose up -d mysql
python -m backend.ingest --reset
```

If local port `3306` is already occupied, set `MYSQL_PORT=3307` and use `DATABASE_URL=mysql+pymysql://consultbae:consultbae@127.0.0.1:3307/consultbae_assignment`.

Use explicit paths if replacing the bundled CSVs:

```powershell
python -m backend.ingest --reset --source1 C:\path\source1.csv --source2 C:\path\source2.csv --source3 C:\path\source3.csv
```

## Verified Result

Using the bundled CSVs, the ingestion summary is:

```json
{
  "people": 55,
  "emails": 56,
  "phones": 45,
  "skills": 15,
  "source_records": 103,
  "records_with_issue_notes": 1,
  "match_strategies": {
    "new_person": 55,
    "exact_email": 17,
    "exact_phone": 26,
    "name_city_unique": 5
  }
}
```
