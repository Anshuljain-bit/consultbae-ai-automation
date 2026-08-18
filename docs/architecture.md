# Architecture

## Components

- `backend/ingest.py`: reads the three CSV sources, normalizes fields, matches people, and writes MySQL records.
- `backend/normalize.py`: shared cleaning and parsing helpers.
- `backend/models.py`: SQLAlchemy schema for canonical people, identifiers, skills, source lineage, and audio submissions.
- `backend/app.py`: Flask API for health checks, audio submission CRUD, playback, and static frontend serving.
- `backend/audio_analysis.py`: audio metadata extraction through FFmpeg/ffprobe, with a WAV fallback.
- `frontend/`: React/Vite user interface for audio submission and review.
- `task2-n8n/`: manual workflow export location for Task 2.

## Data Flow

```text
data/raw/*.csv
  |
  v
source-specific row readers
  |
  v
normalization helpers
  |
  v
matching rules
  |
  v
people / emails / phones / skills / source_records
```

Task 3 uses the same database:

```text
React form or recorder
  |
  v
POST /api/submissions
  |
  +--> save audio to uploads/
  +--> analyze audio metadata
  +--> find or create person by phone
  `--> write audio_submissions row
```

## Database

MySQL is the primary database. SQLAlchemy creates the schema from `backend/models.py`; `task1-data-merging/sql/schema.sql` is a human-readable MySQL reference.

Primary tables:

- `people`
- `person_emails`
- `person_phones`
- `skills`
- `person_skills`
- `source_records`
- `audio_submissions`

## Task 1 Pipeline

Each source has a reader that maps source-specific columns into a `NormalizedRecord`. The pipeline handles whitespace, casing, email casing, Indian phone formats, city aliases, mixed CTC scale, rates, dates, booleans, and skill lists.

The matching order is exact email, exact phone, unique name plus canonical city, then new person. Raw lineage and issue notes are stored in `source_records`.

## Task 2 Integration Point

`task2-n8n/workflow.json` is reserved for the author's real n8n export. A duplicate-check workflow should query `person_emails` and `person_phones` before creating an alert or allowing a new record to continue.

## Task 3 Audio Processing

The backend writes uploaded audio to `uploads/`, extracts metadata, creates or links a person by normalized phone, and persists an `audio_submissions` row. The frontend lists submissions and streams audio through `/api/audio/<id>`.

## Task 4 Reporting

The report in `task4-data-quality/data_quality_report.md` is based on actual source CSV inspection and pipeline behavior. It does not invent findings beyond the provided files.

## Task 5 Production Architecture

For 5,000 workers, the local upload path should be replaced by direct-to-object-storage uploads, asynchronous analysis workers, idempotency keys, campaign-level duplicate rules, monitoring, and retry/dead-letter handling.
