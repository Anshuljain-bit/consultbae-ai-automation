# Engineering Decisions

## Database Choice

MySQL is used because the project already includes a MySQL Docker Compose service and the SQLAlchemy configuration defaults to a MySQL connection string. Keeping MySQL avoids an unnecessary database migration and matches the assignment requirement to use a relational database.

## Entity Matching

The matching strategy uses exact normalized email first, exact normalized phone second, and exact normalized name plus canonical city only when one safe candidate exists.

This favors precision over recall. A broad fuzzy matcher could merge more rows, but the provided data includes same-name collision risk such as `Arjun Mehta` in Noida with different phone numbers.

## Normalization

Normalization is centralized in `backend/normalize.py` so ingestion and the audio app use the same name and phone logic. Phone numbers are normalized to Indian E.164-style values when possible because the supplied data uses local 10-digit numbers, `91` prefixes, `+91` prefixes, hyphens, and leading zeroes.

`Current CTC` values below `1000` are treated as lakh-style values and converted to annual rupee-like amounts. Larger values are kept as already-annual values. This is documented as an assumption because the CSV does not include a unit column.

## Source Lineage

Every usable imported row writes a `source_records` record with source name, source row number, match strategy, raw JSON, and issue notes. This makes the merge explainable and reviewable.

## Audio Processing

FFmpeg/ffprobe is used when available because browser recordings and uploads may be WebM, MP3, M4A, or WAV. The Python WAV fallback keeps simple WAV analysis available even when FFmpeg is not installed.

## Application Framework

Flask is used for the API because the backend surface is small: ingestion, upload handling, submission listing, and playback. React/Vite is used for the frontend because browser recording and a richer submissions table are easier to maintain in a small client app than in server-rendered forms.

## Task 2 Placeholder

The repository includes a clearly marked Task 2 location but does not claim completion. The author will replace `task2-n8n/workflow.json` with the actual exported workflow.
