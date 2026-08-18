from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any


def _tool_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        executable = f"{name}.exe"
        for candidate in base.glob(f"Gyan.FFmpeg_*/*/bin/{executable}"):
            if candidate.exists():
                return str(candidate)
    return None


def _quality(duration: float | None, sample_rate: int | None, bitrate: float | None, loudness: float | None) -> tuple[str, str]:
    problems: list[str] = []
    if duration is not None and duration < 1:
        problems.append("very short recording")
    if sample_rate is not None and sample_rate < 16000:
        problems.append("low sample rate")
    if bitrate is not None and bitrate < 48:
        problems.append("low bitrate")
    if loudness is not None:
        if loudness < -35:
            problems.append("very quiet")
        if loudness > -3:
            problems.append("possible clipping")

    if len(problems) >= 2:
        quality = "poor"
    elif problems:
        quality = "fair"
    else:
        quality = "good"

    if loudness is None:
        noise = "unknown"
    elif loudness < -32:
        noise = "high low-signal risk"
    elif bitrate is not None and bitrate < 64:
        noise = "compression risk"
    else:
        noise = "low obvious risk"
    return quality, noise


def _ffprobe(path: Path, ffprobe_path: str) -> dict[str, Any]:
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration,bit_rate",
        "-show_entries",
        "stream=codec_type,sample_rate,bit_rate,duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _ffmpeg_loudness(path: Path, ffmpeg_path: str) -> float | None:
    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    command = [ffmpeg_path, "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", null_sink]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", result.stderr)
    if not match:
        return None
    return float(match.group(1))


def _analyze_with_ffmpeg(path: Path, ffmpeg_path: str, ffprobe_path: str) -> dict[str, Any]:
    data = _ffprobe(path, ffprobe_path)
    streams = data.get("streams", [])
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    format_info = data.get("format", {})

    duration_text = format_info.get("duration") or audio_stream.get("duration")
    bitrate_text = format_info.get("bit_rate") or audio_stream.get("bit_rate")
    duration = float(duration_text) if duration_text else None
    sample_rate = int(audio_stream["sample_rate"]) if audio_stream.get("sample_rate") else None
    bitrate = round(float(bitrate_text) / 1000, 2) if bitrate_text else None
    loudness = _ffmpeg_loudness(path, ffmpeg_path)
    quality, noise = _quality(duration, sample_rate, bitrate, loudness)
    return {
        "duration_seconds": duration,
        "sample_rate_khz": round(sample_rate / 1000, 3) if sample_rate else None,
        "sample_rate_hz": sample_rate,
        "bitrate_kbps": bitrate,
        "loudness_db": loudness,
        "quality_estimate": quality,
        "noise_estimate": noise,
        "analysis_notes": "analyzed with ffprobe and ffmpeg volumedetect",
    }


def _analyze_wav_fallback(path: Path) -> dict[str, Any]:
    import audioop

    with wave.open(str(path), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        duration = frame_count / float(sample_rate) if sample_rate else None
        frames = wav_file.readframes(frame_count)

    if duration and duration > 0:
        bitrate = round((path.stat().st_size * 8) / duration / 1000, 2)
    else:
        bitrate = None

    rms = audioop.rms(frames, sample_width) if frames else 0
    peak = float(2 ** (8 * sample_width - 1))
    loudness = round(20 * math.log10(rms / peak), 2) if rms > 0 else -96.0
    quality, noise = _quality(duration, sample_rate, bitrate, loudness)
    return {
        "duration_seconds": duration,
        "sample_rate_khz": round(sample_rate / 1000, 3) if sample_rate else None,
        "sample_rate_hz": sample_rate,
        "bitrate_kbps": bitrate,
        "loudness_db": loudness,
        "quality_estimate": quality,
        "noise_estimate": noise,
        "analysis_notes": "analyzed with WAV fallback; install FFmpeg for webm/mp3/m4a",
    }


def analyze_audio(path: str | Path) -> dict[str, Any]:
    audio_path = Path(path)
    ffprobe_path = _tool_path("ffprobe")
    ffmpeg_path = _tool_path("ffmpeg")
    if ffprobe_path and ffmpeg_path:
        return _analyze_with_ffmpeg(audio_path, ffmpeg_path, ffprobe_path)
    try:
        return _analyze_wav_fallback(audio_path)
    except wave.Error as exc:
        raise RuntimeError("FFmpeg is required for this audio format. Install ffmpeg or upload a WAV file.") from exc
