import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from backend.audio_analysis import analyze_audio


class AudioAnalysisTests(unittest.TestCase):
    def test_analyze_wav_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.wav"
            sample_rate = 16000
            duration_seconds = 0.25
            frames = []
            for index in range(int(sample_rate * duration_seconds)):
                value = int(12000 * math.sin(2 * math.pi * 440 * index / sample_rate))
                frames.append(struct.pack("<h", value))

            with wave.open(str(path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b"".join(frames))

            metrics = analyze_audio(path)

            self.assertGreater(metrics["duration_seconds"], 0)
            self.assertEqual(metrics["sample_rate_hz"], sample_rate)
            self.assertGreater(metrics["bitrate_kbps"], 0)
            self.assertIn(metrics["quality_estimate"], {"good", "fair", "poor"})


if __name__ == "__main__":
    unittest.main()
