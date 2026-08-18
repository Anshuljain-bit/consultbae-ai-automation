# ConsultBae - AI Automation Take-Home Assignment

## Overview

ConsultBae operates multiple systems with overlapping people data. This project merges three messy CSV sources into one canonical people database, documents the data-quality issues, and provides a mini audio intake application that stores worker submissions and extracts audio metadata.

Task 2 is intentionally left as a manual n8n workflow upload location. The workflow JSON has not been fabricated.

## Problem Statement

The assignment asks for:

- Task 1: Merge three CSV datasets into one clean database without a shared universal ID.
- Task 2: Add one n8n/Make/Zapier automation export.
- Task 3: Build a small audio collection app with stored submissions and extracted audio properties.
- Task 4: Report the actual data-quality issues found in the three datasets.
- Task 5: Explain how the audio app would scale to 5,000 gig workers over one weekend.

## Solution Overview

The implementation keeps the working app simple: a Python Flask API, MySQL database, CSV ingestion pipeline, and React/Vite frontend.

```text
CSV Sources
  |
  v
Data Ingestion
  |
  v
Cleaning and Normalization
  |
  v
Entity Matching
  |
  v
Unified MySQL Database
  |
  +----------------------+----------------------+
                         |                      |
                         v                      v
                  n8n Workflow Slot       Audio Intake App
                         |                      |
                         v                      v
                  Manual JSON Upload      Audio Metadata
                                                |
                                                v
                                         Submissions Table
```

## Tasks

### Task 1 - Data Merging

The ingestion pipeline reads the three CSV files in `data/raw/`, normalizes names, emails, phones, cities, dates, rates, status values, booleans, and skill tags, then writes canonical people and lineage rows to MySQL.

Matching strategy:

- Exact normalized email.
- Exact normalized phone.
- Exact normalized name plus canonical city only when one safe candidate exists.
- New person otherwise.

The implementation avoids broad fuzzy matching because the supplied data includes same-name and same-city collision risk.

### Task 2 - n8n Automation

Task 2 is documented in `task2-n8n/`. The workflow JSON will be added manually by the author at `task2-n8n/workflow.json`. The current file is a placeholder that clearly marks the workflow as pending.

### Task 3 - Audio Collection App

The app accepts a worker name, phone number, and either an uploaded audio file or browser recording. The backend validates the request, stores the audio under `uploads/`, links or creates a person by normalized phone, extracts metadata, and stores an `audio_submissions` row.

The submissions view lists each item with playback plus duration, sample rate, bitrate, loudness, quality estimate, and noise-risk estimate.

### Task 4 - Data Quality Report

The canonical report is `task4-data-quality/data_quality_report.md`. It covers identifier gaps, formatting inconsistencies, malformed rows, duplicate records, matching challenges, and limitations based only on the provided datasets.

### Task 5 - Scalability

The optional scalability analysis is `task5-scalability/scalability_plan.md`. It covers upload traffic, object storage, queues, duplicate submissions, database load, retries, monitoring, security, and cost controls.

## Tech Stack

- Python 3.12
- Flask and Flask-CORS
- SQLAlchemy
- MySQL 8 through Docker Compose
- PyMySQL
- pandas
- python-dotenv
- React 18
- Vite
- lucide-react
- FFmpeg/ffprobe for production audio formats, with a WAV fallback

## Project Structure

```text
.
|-- backend/                  # Flask API, SQLAlchemy models, ingestion, audio analysis
|-- data/
|   |-- raw/                  # Source CSV files
|   `-- processed/            # Reserved for generated exports
|-- docs/
|   |-- architecture.md
|   |-- decisions.md
|   `-- stuck-log.md
|-- frontend/                 # React/Vite audio intake UI
|-- screenshots/              # Demo screenshots or links can be added here
|-- task1-data-merging/
|   |-- README.md
|   `-- sql/schema.sql
|-- task2-n8n/
|   |-- README.md
|   |-- workflow.json         # Pending manual replacement
|   `-- screenshots/
|-- task3-audio-app/
|   `-- README.md
|-- task4-data-quality/
|   `-- data_quality_report.md
|-- task5-scalability/
|   `-- scalability_plan.md
|-- uploads/.gitkeep          # Uploaded audio files are ignored
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- requirements.txt
`-- README.md
```

## Setup

```powershell
git clone <repository-url>
cd consultbae-ai-automation
Copy-Item .env.example .env
docker compose up -d mysql
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If port `3306` is already in use, set `MYSQL_PORT=3307` in `.env` and update `DATABASE_URL` to use port `3307` before running Docker Compose.

Initialize the database and run Task 1:

```powershell
python -m backend.ingest --reset
```

Run the Task 3 backend:

```powershell
python -m backend.app
```

Run the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

For MP3, M4A, and browser-recorded WebM analysis, install FFmpeg so `ffprobe` and `ffmpeg` are available on `PATH`. WAV files can be analyzed by the Python fallback.

```powershell
winget install --id Gyan.FFmpeg -e
```

## Environment Variables

`.env.example` documents the local configuration:

- `DATABASE_URL`: SQLAlchemy connection string for MySQL.
- `MYSQL_PORT`: host port used by Docker Compose for the local MySQL container.
- `UPLOAD_DIR`: local upload directory for Task 3.
- `MAX_UPLOAD_MB`: maximum accepted audio upload size.
- `FLASK_HOST` and `FLASK_PORT`: Flask bind settings.

Do not commit a real `.env` file.

## Running The Project

```powershell
# Recreate the database and ingest bundled CSVs
python -m backend.ingest --reset

# Run backend API
python -m backend.app

# Run frontend
cd frontend
npm run dev

# Run tests
python -m unittest discover -s tests
```

To import Task 2 later, replace `task2-n8n/workflow.json` with the exported n8n JSON and import it from the n8n editor.

## Database Schema

Important tables:

- `people`: canonical person records.
- `person_emails`: unique normalized email identifiers.
- `person_phones`: unique normalized phone identifiers.
- `skills` and `person_skills`: normalized many-to-many skill tags.
- `source_records`: raw row lineage, source row numbers, match strategy, and issue notes.
- `audio_submissions`: uploaded audio files and extracted metadata.

The SQL reference schema is in `task1-data-merging/sql/schema.sql`; SQLAlchemy models live in `backend/models.py`.

## Data Matching Strategy

The pipeline uses strong identifiers first. Email and phone matches are exact after normalization. Name plus city is used only when it points to exactly one existing candidate and there is no phone conflict. This prioritizes precision over risky merges.

Verified ingest summary from the bundled CSVs:

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

## Data Quality Findings

The datasets include missing shared IDs, mixed phone formats, city aliases, uppercase emails, a blank row, a shifted malformed row, a repeated header row, mixed date formats, mixed CTC scale, mixed rate units, duplicate identities, and same-name collision risk. See `task4-data-quality/data_quality_report.md`.

## Known Limitations

- Task 2 is pending until the author adds the real n8n export.
- The demo app stores audio on local disk; production should use object storage.
- Audio metadata extraction depends on FFmpeg for WebM, MP3, and M4A.
- Duplicate audio submissions are not campaign-scoped because the current schema has no campaign/task table.
- The stuck log is a template because this folder did not include meaningful Git history to reconstruct personal debugging steps.

## Stuck Log

`docs/stuck-log.md` contains a structured template for the author to fill in with actual challenges, searches, AI suggestions, rejected ideas, and final solutions. No personal debugging history has been invented.

## Scalability

See `task5-scalability/scalability_plan.md` for the optional weekend launch analysis.

## Demo

- Screen recording: `[Video link will be added]`
- n8n workflow: `[Task 2 workflow will be added manually]`

## Assignment Checklist

- [x] Task 1 completed
- [ ] Task 2 n8n workflow added
- [x] Task 3 completed
- [x] Task 4 completed
- [x] Task 5 completed
- [x] README completed
- [ ] Stuck log completed by author
- [ ] Demo video recorded
- [ ] Final repository reviewed by author
