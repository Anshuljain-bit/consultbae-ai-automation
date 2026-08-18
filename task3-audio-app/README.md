# Task 3 - Mini Audio Collection App

## Objective

Collect an audio sample from a worker, store the submission, extract audio metadata, and provide a second view for reviewing submissions.

## Implementation

- Backend: Flask API in `backend/app.py`.
- Database models: `backend/models.py`.
- Audio metadata extraction: `backend/audio_analysis.py`.
- Frontend: React/Vite app in `frontend/`.
- Upload storage: `uploads/`, with actual audio files ignored by Git.

## User Flow

1. Enter name and phone number.
2. Upload an audio file or record in the browser.
3. Submit the recording.
4. Backend validates input and stores the file.
5. Backend links or creates a person by normalized phone.
6. Backend extracts duration, sample rate, bitrate, loudness, quality estimate, and noise-risk estimate.
7. Review submissions in the table view with playback.

## Run

```powershell
docker compose up -d mysql
python -m backend.app
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Audio Support

FFmpeg/ffprobe is recommended for WebM, MP3, and M4A. WAV files can be analyzed by the Python fallback if FFmpeg is unavailable.

## Limitations

- Local uploads are suitable for the assignment demo, not production scale.
- Duplicate audio submissions are not campaign-scoped in the current schema.
- Browser recording support depends on the user's browser and microphone permissions.
