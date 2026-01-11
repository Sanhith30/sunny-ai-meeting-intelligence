"""
Speaker Diarization Module
Detects and labels speakers in audio using pyannote.audio.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SpeakerSegment:
    """A segment of speech from a specific speaker."""
    speaker: str
    start: float
    end: float
    text: str = ""
    confidence: float = 1.0


@dataclass
class DiarizationResult:
    """Complete diarization result."""
    segments: List[SpeakerSegment] = field(default_factory=list)
    num_speakers: int = 0
    speaker_stats: Dict[str, float] = field(default_factory=dict)


class SpeakerDiarizer:
    """Speaker diarization using pyannote.audio."""

    def __init__(self, config: dict):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("diarization_enabled", True)
        self.hf_token = adv_config.get("huggingface_token", "")
        self.min_speakers = adv_config.get("min_speakers", 1)
        self.max_speakers = adv_config.get("max_speakers", 10)
        
        self._pipeline = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the diarization pipeline."""
        if not self.enabled:
            logger.info("Speaker diarization is disabled")
            return False

        try:
            from pyannote.audio import Pipeline
            import torch

            # Use CPU if CUDA not available
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load pretrained pipeline (updated API - use token instead of use_auth_token)
            if self.hf_token:
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=self.hf_token
                )
            else:
                # Try without token (may fail for gated models)
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1"
                )
            self._pipeline.to(device)
            
            self._initialized = True
            logger.info(f"Speaker diarization initialized on {device}")
            return True
            
        except ImportError:
            logger.warning("pyannote.audio not installed. Using fallback diarization.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize diarization: {e}")
            return False

    async def diarize(self, audio_path: Path) -> DiarizationResult:
        """Perform speaker diarization on audio file."""
        if not self.enabled:
            return DiarizationResult()

        logger.info(f"Starting speaker diarization: {audio_path}")

        if self._pipeline and self._initialized:
            return await self._diarize_pyannote(audio_path)
        else:
            return await self._diarize_fallback(audio_path)

    async def _diarize_pyannote(self, audio_path: Path) -> DiarizationResult:
        """Diarize using pyannote.audio pipeline."""
        loop = asyncio.get_event_loop()

        def _run_diarization():
            diarization = self._pipeline(
                str(audio_path),
                min_speakers=self.min_speakers,
                max_speakers=self.max_speakers
            )
            return diarization

        try:
            diarization = await loop.run_in_executor(None, _run_diarization)
            
            segments = []
            speaker_times = {}
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    speaker=speaker,
                    start=turn.start,
                    end=turn.end
                )
                segments.append(segment)
                
                # Track speaking time
                duration = turn.end - turn.start
                speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

            # Sort by start time
            segments.sort(key=lambda x: x.start)
            
            # Rename speakers to Speaker 1, Speaker 2, etc.
            speaker_map = {}
            for i, speaker in enumerate(sorted(speaker_times.keys())):
                speaker_map[speaker] = f"Speaker {i + 1}"
            
            for seg in segments:
                seg.speaker = speaker_map.get(seg.speaker, seg.speaker)
            
            renamed_stats = {
                speaker_map.get(k, k): v 
                for k, v in speaker_times.items()
            }

            result = DiarizationResult(
                segments=segments,
                num_speakers=len(speaker_times),
                speaker_stats=renamed_stats
            )
            
            logger.info(f"Diarization complete: {result.num_speakers} speakers detected")
            return result

        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return await self._diarize_fallback(audio_path)

    async def _diarize_fallback(self, audio_path: Path) -> DiarizationResult:
        """Fallback diarization using simple heuristics."""
        logger.info("Using fallback speaker diarization")
        
        # This is a simple fallback that doesn't actually diarize
        # It just creates placeholder segments
        return DiarizationResult(
            segments=[],
            num_speakers=0,
            speaker_stats={}
        )

    def align_with_transcript(
        self,
        diarization: DiarizationResult,
        transcript_segments: List[dict]
    ) -> List[SpeakerSegment]:
        """Align diarization with transcript segments."""
        if not diarization.segments or not transcript_segments:
            return []

        aligned_segments = []
        
        for trans_seg in transcript_segments:
            trans_start = trans_seg.get("start", 0)
            trans_end = trans_seg.get("end", 0)
            trans_text = trans_seg.get("text", "")
            
            # Find overlapping diarization segment
            best_speaker = "Unknown"
            best_overlap = 0
            
            for diar_seg in diarization.segments:
                # Calculate overlap
                overlap_start = max(trans_start, diar_seg.start)
                overlap_end = min(trans_end, diar_seg.end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = diar_seg.speaker
            
            aligned_segments.append(SpeakerSegment(
                speaker=best_speaker,
                start=trans_start,
                end=trans_end,
                text=trans_text
            ))

        return aligned_segments

    def get_speaker_transcript(
        self,
        aligned_segments: List[SpeakerSegment]
    ) -> str:
        """Generate speaker-labeled transcript."""
        lines = []
        
        for seg in aligned_segments:
            timestamp = self._format_timestamp(seg.start)
            lines.append(f"[{timestamp}] {seg.speaker}: {seg.text}")
        
        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
