"""
Audio Capture Module
Handles system audio capture during meetings.
"""

import asyncio
import wave
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"
    chunk_duration_seconds: int = 30


class AudioCapture:
    """Captures system audio during meetings."""

    def __init__(self, config: dict):
        audio_config = config.get("audio", {})
        self.sample_rate = audio_config.get("sample_rate", 16000)
        self.channels = audio_config.get("channels", 1)
        self.format = audio_config.get("format", "wav")
        self.chunk_duration = audio_config.get("chunk_duration_seconds", 30)
        
        self.output_dir = Path(config.get("general", {}).get("output_dir", "./outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._recording = False
        self._audio_data = []
        self._stream: Optional[sd.InputStream] = None
        self._current_file: Optional[Path] = None

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        if self._recording:
            self._audio_data.append(indata.copy())

    async def start_recording(self, filename: Optional[str] = None) -> Path:
        """Start recording audio."""
        if self._recording:
            logger.warning("Recording already in progress")
            return self._current_file

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_audio_{timestamp}.{self.format}"

        self._current_file = self.output_dir / filename
        self._audio_data = []
        self._recording = True

        try:
            # Get default input device
            device_info = sd.query_devices(kind='input')
            logger.info(f"Using audio device: {device_info['name']}")

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                dtype=np.float32
            )
            self._stream.start()
            logger.info(f"Started recording to {self._current_file}")
            
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
            self._recording = False
            raise

        return self._current_file

    async def stop_recording(self) -> Optional[Path]:
        """Stop recording and save audio file."""
        if not self._recording:
            logger.warning("No recording in progress")
            return None

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._audio_data:
            logger.warning("No audio data captured")
            return None

        try:
            # Concatenate all audio chunks
            audio_array = np.concatenate(self._audio_data, axis=0)
            
            # Save to file
            sf.write(
                str(self._current_file),
                audio_array,
                self.sample_rate,
                format=self.format.upper()
            )
            
            logger.info(f"Saved recording to {self._current_file}")
            return self._current_file
            
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return None

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    async def get_audio_chunks(self) -> list:
        """Get recorded audio in chunks for processing."""
        if not self._audio_data:
            return []

        audio_array = np.concatenate(self._audio_data, axis=0)
        chunk_samples = self.chunk_duration * self.sample_rate
        
        chunks = []
        for i in range(0, len(audio_array), chunk_samples):
            chunk = audio_array[i:i + chunk_samples]
            chunks.append(chunk)
        
        return chunks

    def get_duration_seconds(self) -> float:
        """Get current recording duration in seconds."""
        if not self._audio_data:
            return 0.0
        
        total_samples = sum(chunk.shape[0] for chunk in self._audio_data)
        return total_samples / self.sample_rate
