"""
Whisper Speech-to-Text Engine
Handles audio transcription using OpenAI Whisper (open-source).
"""

import asyncio
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import timedelta
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TranscriptionSegment:
    """A single segment of transcribed text."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str
    confidence: float = 1.0
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str
    segments: List[TranscriptionSegment] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0
    
    def get_timestamped_text(self) -> str:
        """Get text with timestamps."""
        lines = []
        for seg in self.segments:
            timestamp = str(timedelta(seconds=int(seg.start)))
            speaker_prefix = f"[{seg.speaker}] " if seg.speaker else ""
            lines.append(f"[{timestamp}] {speaker_prefix}{seg.text}")
        return "\n".join(lines)


class WhisperEngine:
    """Speech-to-text engine using Whisper."""

    def __init__(self, config: dict):
        trans_config = config.get("transcription", {})
        self.model_size = trans_config.get("model_size", "medium")
        self.language = trans_config.get("language", "en")
        self.device = trans_config.get("device", "cpu")
        self.compute_type = trans_config.get("compute_type", "int8")
        
        self._model = None
        self._use_faster_whisper = True

    async def load_model(self) -> None:
        """Load the Whisper model."""
        logger.info(f"Loading Whisper model: {self.model_size}")
        
        try:
            # Try faster-whisper first (more efficient)
            from faster_whisper import WhisperModel
            
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            self._use_faster_whisper = True
            logger.info("Loaded faster-whisper model")
            
        except ImportError:
            # Fall back to standard whisper
            import whisper
            
            self._model = whisper.load_model(self.model_size, device=self.device)
            self._use_faster_whisper = False
            logger.info("Loaded standard whisper model")

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
        if not self._model:
            await self.load_model()

        logger.info(f"Transcribing: {audio_path}")
        
        try:
            if self._use_faster_whisper:
                return await self._transcribe_faster_whisper(audio_path)
            else:
                return await self._transcribe_standard_whisper(audio_path)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def _transcribe_faster_whisper(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe using faster-whisper."""
        loop = asyncio.get_event_loop()
        
        def _transcribe():
            segments, info = self._model.transcribe(
                str(audio_path),
                language=self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            return list(segments), info

        segments, info = await loop.run_in_executor(None, _transcribe)
        
        transcription_segments = []
        full_text_parts = []
        
        for seg in segments:
            transcription_segments.append(TranscriptionSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                confidence=seg.avg_logprob if hasattr(seg, 'avg_logprob') else 1.0
            ))
            full_text_parts.append(seg.text.strip())

        # Apply basic speaker segmentation
        transcription_segments = self._apply_speaker_heuristics(transcription_segments)

        return TranscriptionResult(
            text=" ".join(full_text_parts),
            segments=transcription_segments,
            language=info.language if hasattr(info, 'language') else self.language,
            duration=info.duration if hasattr(info, 'duration') else 0.0
        )

    async def _transcribe_standard_whisper(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe using standard whisper."""
        loop = asyncio.get_event_loop()
        
        def _transcribe():
            return self._model.transcribe(
                str(audio_path),
                language=self.language,
                verbose=False
            )

        result = await loop.run_in_executor(None, _transcribe)
        
        transcription_segments = []
        
        for seg in result.get("segments", []):
            transcription_segments.append(TranscriptionSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
                confidence=seg.get("avg_logprob", 0.0)
            ))

        # Apply basic speaker segmentation
        transcription_segments = self._apply_speaker_heuristics(transcription_segments)

        return TranscriptionResult(
            text=result.get("text", "").strip(),
            segments=transcription_segments,
            language=result.get("language", self.language),
            duration=transcription_segments[-1].end if transcription_segments else 0.0
        )

    def _apply_speaker_heuristics(
        self, 
        segments: List[TranscriptionSegment]
    ) -> List[TranscriptionSegment]:
        """Apply basic speaker segmentation heuristics."""
        if not segments:
            return segments

        current_speaker = "Speaker 1"
        speaker_count = 1
        
        # Heuristic: Long pauses (>2s) or significant changes might indicate speaker change
        for i, seg in enumerate(segments):
            if i > 0:
                gap = seg.start - segments[i-1].end
                
                # If there's a significant pause, might be a new speaker
                if gap > 2.0:
                    # Simple alternating speaker assignment
                    speaker_count = (speaker_count % 4) + 1
                    current_speaker = f"Speaker {speaker_count}"
            
            seg.speaker = current_speaker

        return segments

    async def transcribe_chunks(
        self, 
        audio_chunks: List[np.ndarray],
        sample_rate: int = 16000
    ) -> TranscriptionResult:
        """Transcribe audio chunks directly from memory."""
        if not self._model:
            await self.load_model()

        all_segments = []
        full_text_parts = []
        time_offset = 0.0

        for chunk in audio_chunks:
            # Save chunk to temp file (whisper requires file input)
            import tempfile
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, chunk, sample_rate)
                chunk_result = await self.transcribe(Path(f.name))
                
                # Adjust timestamps
                for seg in chunk_result.segments:
                    seg.start += time_offset
                    seg.end += time_offset
                    all_segments.append(seg)
                
                full_text_parts.append(chunk_result.text)
                time_offset += len(chunk) / sample_rate

        return TranscriptionResult(
            text=" ".join(full_text_parts),
            segments=all_segments,
            language=self.language,
            duration=time_offset
        )
