"""
Meeting Recorder Module
Orchestrates the meeting joining and recording process.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from .joiner import MeetingJoiner, MeetingPlatform
from .audio import AudioCapture

logger = structlog.get_logger(__name__)


class RecordingState(Enum):
    IDLE = "idle"
    JOINING = "joining"
    IN_MEETING = "in_meeting"
    RECORDING = "recording"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class MeetingSession:
    meeting_url: str
    platform: MeetingPlatform
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    audio_file: Optional[Path] = None
    state: RecordingState = RecordingState.IDLE
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class MeetingRecorder:
    """Orchestrates meeting joining and audio recording."""

    def __init__(self, config: dict):
        self.config = config
        self.joiner = MeetingJoiner(config)
        self.audio_capture = AudioCapture(config)
        self.session: Optional[MeetingSession] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._on_meeting_end: Optional[Callable] = None
        
        meeting_config = config.get("meeting", {})
        self.max_duration = meeting_config.get("max_duration_minutes", 180) * 60
        self.end_detection_interval = meeting_config.get("end_detection_interval_seconds", 10)

    def set_meeting_end_callback(self, callback: Callable) -> None:
        """Set callback to be called when meeting ends."""
        self._on_meeting_end = callback

    async def start_session(self, meeting_url: str) -> MeetingSession:
        """Start a new meeting session."""
        platform = self.joiner.detect_platform(meeting_url)
        
        self.session = MeetingSession(
            meeting_url=meeting_url,
            platform=platform,
            state=RecordingState.JOINING
        )
        
        logger.info(f"Starting session for {platform.value} meeting")

        try:
            # Join the meeting
            joined = await self.joiner.join_meeting(meeting_url)
            
            if not joined:
                self.session.state = RecordingState.ERROR
                self.session.error_message = "Failed to join meeting"
                return self.session

            self.session.state = RecordingState.IN_MEETING
            self.session.start_time = datetime.now()
            
            # Start audio recording
            audio_file = await self.audio_capture.start_recording()
            self.session.audio_file = audio_file
            self.session.state = RecordingState.RECORDING
            
            # Start monitoring for meeting end
            self._monitoring_task = asyncio.create_task(self._monitor_meeting())
            
            logger.info("Meeting session started successfully")
            return self.session

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            self.session.state = RecordingState.ERROR
            self.session.error_message = str(e)
            return self.session

    async def _monitor_meeting(self) -> None:
        """Monitor meeting status and detect when it ends."""
        start_time = datetime.now()
        
        while self.session and self.session.state == RecordingState.RECORDING:
            await asyncio.sleep(self.end_detection_interval)
            
            # Check max duration
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= self.max_duration:
                logger.info("Max meeting duration reached")
                await self.end_session()
                break
            
            # Check if meeting has ended (browser-based detection)
            if self.joiner.page:
                try:
                    meeting_ended = await self._check_meeting_ended()
                    if meeting_ended:
                        logger.info("Meeting end detected")
                        await self.end_session()
                        break
                except Exception as e:
                    logger.warning(f"Error checking meeting status: {e}")

    async def _check_meeting_ended(self) -> bool:
        """Check if the meeting has ended based on page content."""
        if not self.joiner.page:
            return True

        try:
            # Google Meet end indicators
            meet_ended = await self.joiner.page.query_selector('[data-call-ended="true"]')
            if meet_ended:
                return True

            # Check for "You left the meeting" or similar text
            page_content = await self.joiner.page.content()
            end_indicators = [
                "you left the meeting",
                "meeting has ended",
                "call ended",
                "the meeting has been ended",
                "host has ended the meeting"
            ]
            
            for indicator in end_indicators:
                if indicator in page_content.lower():
                    return True

            return False
            
        except Exception:
            return False

    async def end_session(self) -> MeetingSession:
        """End the current meeting session."""
        if not self.session:
            logger.warning("No active session to end")
            return None

        logger.info("Ending meeting session")
        
        # Cancel monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Stop audio recording
        if self.audio_capture.is_recording:
            await self.audio_capture.stop_recording()

        # Leave meeting and close browser
        await self.joiner.leave_meeting()

        # Update session
        self.session.end_time = datetime.now()
        self.session.state = RecordingState.ENDED
        
        # Calculate duration
        if self.session.start_time:
            duration = (self.session.end_time - self.session.start_time).total_seconds()
            self.session.metadata["duration_seconds"] = duration
            self.session.metadata["duration_formatted"] = self._format_duration(duration)

        # Trigger callback
        if self._on_meeting_end:
            await self._on_meeting_end(self.session)

        logger.info(f"Session ended. Duration: {self.session.metadata.get('duration_formatted', 'N/A')}")
        return self.session

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    @property
    def is_active(self) -> bool:
        """Check if a session is currently active."""
        return self.session is not None and self.session.state == RecordingState.RECORDING
