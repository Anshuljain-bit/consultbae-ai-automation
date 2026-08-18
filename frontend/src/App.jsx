import { useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  FileAudio,
  Headphones,
  Mic,
  Play,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Square,
  Trash2,
  Upload,
} from "lucide-react";

const emptyForm = { name: "", phone: "" };

function formatDuration(seconds) {
  if (seconds == null) return "-";
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60).toString().padStart(2, "0");
  const rest = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${rest}`;
}

function formatSampleRate(value) {
  if (!value) return "-";
  return `${Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 1)} kHz`;
}

function formatBitrate(value) {
  if (!value) return "-";
  return `${Math.round(value)} kbps`;
}

function formatLoudness(value) {
  if (value == null) return "-";
  return `${Number(value).toFixed(1)} dB`;
}

function qualityTone(quality) {
  if (quality === "good") return "good";
  if (quality === "poor") return "poor";
  return "fair";
}

function microphoneErrorMessage(error) {
  if (window.isSecureContext === false) {
    return "Microphone recording requires localhost or HTTPS. Open the app at http://127.0.0.1:5173.";
  }
  if (error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError") {
    return "Microphone access is blocked. Allow the microphone for this site in the browser address bar, then reload.";
  }
  if (error?.name === "NotFoundError" || error?.name === "DevicesNotFoundError") {
    return "No microphone was found. Connect or enable a microphone, or upload an audio file instead.";
  }
  if (error?.name === "NotReadableError" || error?.name === "TrackStartError") {
    return "The microphone is busy or blocked by another app. Close other recording apps and try again.";
  }
  return "Browser recording could not start. Allow microphone access or upload an audio file instead.";
}

export default function App() {
  const [activeTab, setActiveTab] = useState("submit");
  const [form, setForm] = useState(emptyForm);
  const [audioFile, setAudioFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [query, setQuery] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  async function loadSubmissions() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/submissions");
      if (!response.ok) throw new Error("Could not load submissions.");
      setSubmissions(await response.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSubmissions();
  }, []);

  useEffect(() => {
    return () => stopTracks();
  }, []);

  const filteredSubmissions = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return submissions;
    return submissions.filter((item) =>
      [item.name, item.phone, item.original_filename, item.quality_estimate]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(needle))
    );
  }, [query, submissions]);

  function stopTracks() {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }

  function chooseFile(file) {
    if (!file) return;
    setAudioFile(file);
    setStatus(`${file.name} ready`);
    setError("");
  }

  async function startRecording() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("Browser recording is not available here. Upload an audio file instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const file = new File([blob], `recording-${Date.now()}.webm`, { type: blob.type || "audio/webm" });
        chooseFile(file);
        stopTracks();
      };
      recorder.start();
      setRecording(true);
      setRecordSeconds(0);
      timerRef.current = window.setInterval(() => setRecordSeconds((value) => value + 1), 1000);
    } catch (err) {
      setError(microphoneErrorMessage(err));
      stopTracks();
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    setRecording(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setStatus("");
    if (!audioFile) {
      setError("Choose or record an audio file before submitting.");
      return;
    }
    setSubmitting(true);
    try {
      const body = new FormData();
      body.append("name", form.name);
      body.append("phone", form.phone);
      body.append("audio", audioFile, audioFile.name);
      const response = await fetch("/api/submissions", { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Submission failed.");
      setStatus("Submission stored");
      setForm(emptyForm);
      setAudioFile(null);
      setActiveTab("submissions");
      await loadSubmissions();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteSubmission(item) {
    const confirmed = window.confirm(`Delete submission from ${item.name}? This removes the stored audio file too.`);
    if (!confirmed) return;

    setDeletingId(item.id);
    setError("");
    setStatus("");
    try {
      const response = await fetch(`/api/submissions/${item.id}`, { method: "DELETE" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || "Could not delete submission.");
      setSubmissions((current) => current.filter((submission) => submission.id !== item.id));
      setStatus("Submission deleted");
    } catch (err) {
      setError(err.message);
      window.alert(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Headphones aria-hidden="true" size={32} strokeWidth={1.8} />
          <span>Audio Intake</span>
        </div>
        <nav className="tabs" aria-label="Primary">
          <button className={activeTab === "submit" ? "active" : ""} onClick={() => setActiveTab("submit")}>
            <Upload size={17} aria-hidden="true" />
            Submit
          </button>
          <button className={activeTab === "submissions" ? "active" : ""} onClick={() => setActiveTab("submissions")}>
            <SlidersHorizontal size={17} aria-hidden="true" />
            Submissions
          </button>
        </nav>
        <div className="top-actions">
          <button title="Refresh submissions" onClick={loadSubmissions}>
            <RefreshCw size={19} aria-hidden="true" />
          </button>
        </div>
      </header>

      <main className="workspace">
        {activeTab === "submit" && (
          <section className="intake-panel" aria-labelledby="submit-heading">
            <form className="submission-form" onSubmit={handleSubmit}>
              <div className="form-copy">
                <h1 id="submit-heading">Submit Audio</h1>
              </div>
              <div className="field-grid">
                <label>
                  <span>Name</span>
                  <input
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                    placeholder="Enter name"
                    autoComplete="name"
                    required
                  />
                </label>
                <label>
                  <span>Phone</span>
                  <input
                    value={form.phone}
                    onChange={(event) => setForm({ ...form, phone: event.target.value })}
                    placeholder="Enter phone number"
                    autoComplete="tel"
                    required
                  />
                </label>
              </div>
              <button className="primary-action" type="submit" disabled={submitting || recording}>
                <Upload size={18} aria-hidden="true" />
                {submitting ? "Submitting..." : "Submit Audio"}
              </button>
            </form>

            <div
              className={`drop-zone ${dragging ? "dragging" : ""}`}
              onDragEnter={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                chooseFile(event.dataTransfer.files?.[0]);
              }}
            >
              <div className="upload-side">
                <Upload size={34} aria-hidden="true" />
                <strong>Drag and drop audio file here</strong>
                <span>MP3, WAV, M4A or browser recording</span>
                <label className="secondary-button">
                  <FileAudio size={18} aria-hidden="true" />
                  Choose File
                  <input type="file" accept="audio/*" onChange={(event) => chooseFile(event.target.files?.[0])} />
                </label>
              </div>
              <div className="divider" aria-hidden="true">
                OR
              </div>
              <div className="record-side">
                <Mic size={34} aria-hidden="true" />
                <strong>Record audio</strong>
                <span>{recording ? formatDuration(recordSeconds) : "Max 10 minutes"}</span>
                {recording ? (
                  <button className="outline-action danger" type="button" onClick={stopRecording}>
                    <Square size={15} aria-hidden="true" />
                    Stop Recording
                  </button>
                ) : (
                  <button className="outline-action" type="button" onClick={startRecording}>
                    <span className="record-dot" />
                    Start Recording
                  </button>
                )}
              </div>
            </div>
            <StatusLine audioFile={audioFile} status={status} error={error} />
          </section>
        )}

        <section className="table-panel" aria-labelledby="submissions-heading">
          <div className="table-header">
            <h2 id="submissions-heading">Submissions</h2>
            <div className="table-tools">
              <label className="search-box">
                <Search size={19} aria-hidden="true" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search submissions..."
                />
              </label>
              <button title="Refresh submissions" onClick={loadSubmissions}>
                <RefreshCw size={19} aria-hidden="true" className={loading ? "spin" : ""} />
              </button>
            </div>
          </div>
          {activeTab === "submissions" && (status || error) && (
            <div className={`table-message ${error ? "error" : ""}`}>{error || status}</div>
          )}
          <SubmissionsTable submissions={filteredSubmissions} deletingId={deletingId} onDelete={handleDeleteSubmission} />
        </section>
      </main>
    </div>
  );
}

function StatusLine({ audioFile, status, error }) {
  if (!audioFile && !status && !error) return null;
  return (
    <div className={`status-line ${error ? "error" : ""}`}>
      {error ? null : <CheckCircle2 size={18} aria-hidden="true" />}
      <span>{error || status || `${audioFile.name} ready`}</span>
    </div>
  );
}

function SubmissionsTable({ submissions, deletingId, onDelete }) {
  if (submissions.length === 0) {
    return (
      <div className="empty-state">
        <FileAudio size={28} aria-hidden="true" />
        <span>No submissions found.</span>
      </div>
    );
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Phone</th>
            <th>Audio</th>
            <th>Duration</th>
            <th>Sample Rate</th>
            <th>Bitrate</th>
            <th>Loudness</th>
            <th>Quality</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {submissions.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.phone}</td>
              <td className="audio-cell">
                <a className="play-link" href={item.audio_url} target="_blank" rel="noreferrer" title="Open audio">
                  <Play size={15} aria-hidden="true" />
                </a>
                <audio controls preload="none" src={item.audio_url}>
                  Audio playback is unavailable in this browser.
                </audio>
              </td>
              <td>{formatDuration(item.duration_seconds)}</td>
              <td>{formatSampleRate(item.sample_rate_khz ?? (item.sample_rate_hz ? item.sample_rate_hz / 1000 : null))}</td>
              <td>{formatBitrate(item.bitrate_kbps)}</td>
              <td>{formatLoudness(item.loudness_db)}</td>
              <td>
                <span className={`quality ${qualityTone(item.quality_estimate)}`}>
                  <span aria-hidden="true" />
                  {item.quality_estimate || "unknown"}
                </span>
              </td>
              <td className="action-cell">
                <button
                  className="delete-button"
                  type="button"
                  title="Delete submission"
                  aria-label={`Delete submission from ${item.name}`}
                  disabled={deletingId === item.id}
                  onClick={() => onDelete(item)}
                >
                  <Trash2 size={17} aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
