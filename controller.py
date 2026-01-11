"""
Sunny AI Controller
Main orchestration module that coordinates all components.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import asdict
import structlog

from meeting_bot.recorder import MeetingRecorder, MeetingSession, RecordingState
from transcription.whisper_engine import WhisperEngine, TranscriptionResult
from summarization.llm_pipeline import LLMPipeline, MeetingSummary
from pdf.pdf_generator import PDFGenerator
from email_sender.gmail_sender import GmailSender
from database.storage import MeetingStorage, MeetingRecord

# Advanced Features
from advanced_features import (
    SpeakerDiarizer,
    TopicSegmenter,
    SentimentAnalyzer,
    ActionItemExtractor,
    MeetingAnalytics,
    FollowupEmailGenerator,
    MeetingMemory
)

logger = structlog.get_logger(__name__)


class SunnyAIController:
    """Main controller for Sunny AI operations."""

    def __init__(self, config: dict):
        self.config = config
        
        # Initialize core components
        self.recorder = MeetingRecorder(config)
        self.transcriber = WhisperEngine(config)
        self.summarizer = LLMPipeline(config)
        self.pdf_generator = PDFGenerator(config)
        self.email_sender = GmailSender(config)
        self.storage = MeetingStorage()
        
        # Initialize advanced features
        self.diarizer = SpeakerDiarizer(config)
        self.topic_segmenter = TopicSegmenter(config, self.summarizer)
        self.sentiment_analyzer = SentimentAnalyzer(config, self.summarizer)
        self.action_extractor = ActionItemExtractor(config, self.summarizer)
        self.analytics = MeetingAnalytics(config)
        self.followup_generator = FollowupEmailGenerator(config, self.summarizer)
        self.memory = MeetingMemory(config)
        
        # Session tracking
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._session_counter = 0

    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing Sunny AI Controller")
        
        # Initialize database
        await self.storage.initialize()
        
        # Check LLM availability
        llm_available = await self.summarizer.check_available()
        if not llm_available:
            provider = self.config.get("summarization", {}).get("provider", "gemini")
            if provider == "gemini":
                logger.warning("Gemini API not available. Check your GEMINI_API_KEY.")
            else:
                logger.warning("Ollama not available. Summarization will fail.")
        else:
            logger.info(f"LLM provider ready: {self.summarizer.provider}")
        
        # Initialize advanced features
        adv_config = self.config.get("advanced_features", {})
        
        if adv_config.get("diarization_enabled", True):
            await self.diarizer.initialize()
        
        if adv_config.get("sentiment_enabled", True):
            await self.sentiment_analyzer.initialize()
        
        if adv_config.get("rag_memory_enabled", True):
            await self.memory.initialize()
        
        logger.info("Sunny AI Controller initialized")

    async def start_session(
        self,
        meeting_url: str,
        recipient_email: str,
        send_email: bool = True
    ) -> int:
        """Start a new meeting session."""
        
        self._session_counter += 1
        session_id = self._session_counter
        
        logger.info(f"Starting session {session_id}", meeting_url=meeting_url)
        
        # Create session record
        self._sessions[session_id] = {
            "id": session_id,
            "meeting_url": meeting_url,
            "recipient_email": recipient_email,
            "send_email": send_email,
            "status": "starting",
            "meeting_session": None,
            "transcript": None,
            "summary": None,
            "pdf_path": None,
            "db_record_id": None
        }
        
        # Start the meeting process in background
        asyncio.create_task(self._run_session(session_id))
        
        return session_id

    async def _run_session(self, session_id: int) -> None:
        """Run the complete meeting session workflow."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        try:
            # Step 1: Join meeting and record
            session["status"] = "joining"
            logger.info(f"Session {session_id}: Joining meeting")
            
            meeting_session = await self.recorder.start_session(session["meeting_url"])
            session["meeting_session"] = meeting_session
            
            if meeting_session.state == RecordingState.ERROR:
                session["status"] = "error"
                session["error"] = meeting_session.error_message
                logger.error(f"Session {session_id}: Failed to join meeting")
                return
            
            session["status"] = "recording"
            logger.info(f"Session {session_id}: Recording started")
            
            # Wait for meeting to end
            while self.recorder.is_active:
                await asyncio.sleep(5)
            
            # Step 2: Process recording
            session["status"] = "processing"
            await self._process_recording(session_id)
            
        except Exception as e:
            logger.error(f"Session {session_id} error: {e}")
            session["status"] = "error"
            session["error"] = str(e)

    async def _process_recording(self, session_id: int) -> None:
        """Process the recorded audio with advanced features."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        meeting_session: MeetingSession = session["meeting_session"]
        
        if not meeting_session.audio_file or not meeting_session.audio_file.exists():
            logger.error(f"Session {session_id}: No audio file found")
            session["status"] = "error"
            session["error"] = "No audio file recorded"
            return
        
        try:
            # Step 2: Transcribe audio
            session["status"] = "transcribing"
            logger.info(f"Session {session_id}: Transcribing audio")
            
            transcript_result = await self.transcriber.transcribe(meeting_session.audio_file)
            session["transcript"] = transcript_result
            
            # Get transcript segments for advanced processing
            transcript_segments = getattr(transcript_result, 'segments', [])
            
            # Step 3: Speaker Diarization
            session["status"] = "diarizing"
            logger.info(f"Session {session_id}: Speaker diarization")
            
            diarization_result = await self.diarizer.diarize(meeting_session.audio_file)
            session["diarization"] = diarization_result
            
            # Align diarization with transcript
            if diarization_result.segments and transcript_segments:
                aligned_segments = self.diarizer.align_with_transcript(
                    diarization_result, transcript_segments
                )
                session["aligned_segments"] = aligned_segments
            
            # Step 4: Topic Segmentation
            session["status"] = "segmenting_topics"
            logger.info(f"Session {session_id}: Topic segmentation")
            
            topic_result = await self.topic_segmenter.segment_topics(
                transcript_result.text, transcript_segments
            )
            session["topics"] = topic_result
            
            # Step 5: Sentiment Analysis
            session["status"] = "analyzing_sentiment"
            logger.info(f"Session {session_id}: Sentiment analysis")
            
            sentiment_result = await self.sentiment_analyzer.analyze(
                transcript_result.text, transcript_segments
            )
            session["sentiment"] = sentiment_result
            
            # Step 6: Generate summary
            session["status"] = "summarizing"
            logger.info(f"Session {session_id}: Generating summary")
            
            summary = await self.summarizer.summarize_transcript(transcript_result.text)
            session["summary"] = summary
            
            # Step 7: Extract Action Items (enhanced)
            session["status"] = "extracting_actions"
            logger.info(f"Session {session_id}: Extracting action items")
            
            action_result = await self.action_extractor.extract(
                transcript_result.text, transcript_segments
            )
            session["action_items"] = action_result
            
            # Step 8: Generate Analytics
            session["status"] = "generating_analytics"
            logger.info(f"Session {session_id}: Generating analytics")
            
            duration_seconds = meeting_session.metadata.get("duration_seconds", 0)
            metrics = self.analytics.generate_metrics(
                duration_seconds=duration_seconds,
                transcript=transcript_result.text,
                transcript_segments=transcript_segments,
                diarization_result=diarization_result,
                topic_result=topic_result,
                sentiment_result=sentiment_result,
                action_items_result=action_result,
                summary=summary,
                platform=meeting_session.platform.value,
                meeting_date=meeting_session.start_time
            )
            session["analytics"] = metrics
            
            # Step 9: Generate PDF (enhanced)
            session["status"] = "generating_pdf"
            logger.info(f"Session {session_id}: Generating PDF")
            
            pdf_path = self.pdf_generator.generate_report(
                summary=summary,
                platform=meeting_session.platform.value,
                duration=meeting_session.metadata.get("duration_formatted", "Unknown"),
                meeting_date=meeting_session.start_time,
                diarization=diarization_result,
                topics=topic_result,
                sentiment=sentiment_result,
                action_items=action_result,
                analytics=metrics
            )
            session["pdf_path"] = pdf_path
            
            # Step 10: Save to database
            db_record = MeetingRecord(
                meeting_url=session["meeting_url"],
                platform=meeting_session.platform.value,
                start_time=meeting_session.start_time.isoformat() if meeting_session.start_time else None,
                end_time=meeting_session.end_time.isoformat() if meeting_session.end_time else None,
                duration_seconds=meeting_session.metadata.get("duration_seconds", 0),
                audio_file=str(meeting_session.audio_file),
                transcript=transcript_result.text,
                summary_json=json.dumps({
                    "executive_summary": summary.executive_summary,
                    "key_points": summary.key_discussion_points,
                    "decisions": summary.decisions_made,
                    "action_items": [asdict(a) for a in summary.action_items],
                    "analytics": self.analytics.to_dict(metrics) if metrics else None
                }),
                pdf_path=str(pdf_path)
            )
            
            record_id = await self.storage.save_meeting(db_record)
            session["db_record_id"] = record_id
            
            # Step 11: Store in RAG Memory
            if self.memory._initialized:
                session["status"] = "storing_memory"
                logger.info(f"Session {session_id}: Storing in memory")
                
                await self.memory.store_meeting(
                    meeting_id=record_id,
                    transcript=transcript_result.text,
                    summary=summary,
                    decisions=summary.decisions_made,
                    action_items=action_result.items if action_result else None,
                    metadata={
                        "platform": meeting_session.platform.value,
                        "duration": duration_seconds
                    }
                )
            
            # Step 12: Generate Follow-up Email
            session["status"] = "generating_followup"
            logger.info(f"Session {session_id}: Generating follow-up email")
            
            followup_email = await self.followup_generator.generate(
                summary=summary,
                action_items=action_result,
                meeting_date=meeting_session.start_time,
                meeting_title=f"{meeting_session.platform.value.title()} Meeting"
            )
            session["followup_email"] = followup_email
            
            # Step 13: Send email
            if session["send_email"]:
                session["status"] = "sending_email"
                logger.info(f"Session {session_id}: Sending email")
                
                try:
                    await self.email_sender.send_summary(
                        recipient_email=session["recipient_email"],
                        pdf_path=pdf_path,
                        platform=meeting_session.platform.value,
                        meeting_date=meeting_session.start_time
                    )
                    
                    # Update database record
                    db_record.id = record_id
                    db_record.email_sent = True
                    db_record.email_recipient = session["recipient_email"]
                    await self.storage.update_meeting(db_record)
                    
                except Exception as e:
                    logger.error(f"Failed to send email: {e}")
            
            session["status"] = "completed"
            logger.info(f"Session {session_id}: Completed successfully")
            
        except Exception as e:
            logger.error(f"Session {session_id} processing error: {e}")
            session["status"] = "error"
            session["error"] = str(e)


    async def stop_session(self, session_id: int) -> None:
        """Stop an active session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session["status"] == "recording":
            await self.recorder.end_session()
        
        session["status"] = "stopped"
        logger.info(f"Session {session_id}: Stopped")

    async def get_session_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a session."""
        session = self._sessions.get(session_id)
        if not session:
            # Try to load from database
            if session_id <= 0:
                return None
            
            record = await self.storage.get_meeting(session_id)
            if record:
                return {
                    "session_id": record.id,
                    "status": "completed",
                    "platform": record.platform,
                    "start_time": record.start_time,
                    "duration": f"{record.duration_seconds:.0f}s",
                    "transcript_available": bool(record.transcript),
                    "summary_available": bool(record.summary_json),
                    "pdf_path": record.pdf_path,
                    "email_sent": record.email_sent
                }
            return None
        
        meeting_session = session.get("meeting_session")
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "platform": meeting_session.platform.value if meeting_session else None,
            "start_time": meeting_session.start_time.isoformat() if meeting_session and meeting_session.start_time else None,
            "duration": meeting_session.metadata.get("duration_formatted") if meeting_session else None,
            "transcript_available": session.get("transcript") is not None,
            "summary_available": session.get("summary") is not None,
            "pdf_path": str(session.get("pdf_path")) if session.get("pdf_path") else None,
            "email_sent": session.get("status") == "completed" and session.get("send_email", False)
        }

    async def get_transcript(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get transcript for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("transcript"):
            transcript: TranscriptionResult = session["transcript"]
            return {
                "session_id": session_id,
                "transcript": transcript.text,
                "duration_seconds": transcript.duration
            }
        
        # Try database
        record = await self.storage.get_meeting(session_id)
        if record and record.transcript:
            return {
                "session_id": session_id,
                "transcript": record.transcript,
                "duration_seconds": record.duration_seconds
            }
        
        return None

    async def get_summary(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get summary for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("summary"):
            summary: MeetingSummary = session["summary"]
            return {
                "session_id": session_id,
                "executive_summary": summary.executive_summary,
                "key_points": summary.key_discussion_points,
                "decisions": summary.decisions_made,
                "action_items": [asdict(a) for a in summary.action_items]
            }
        
        # Try database
        record = await self.storage.get_meeting(session_id)
        if record and record.summary_json:
            summary_data = json.loads(record.summary_json)
            return {
                "session_id": session_id,
                **summary_data
            }
        
        return None

    async def get_pdf_path(self, session_id: int) -> Optional[str]:
        """Get PDF path for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("pdf_path"):
            return str(session["pdf_path"])
        
        # Try database
        record = await self.storage.get_meeting(session_id)
        if record and record.pdf_path:
            return record.pdf_path
        
        return None

    async def get_recent_meetings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent meeting records."""
        records = await self.storage.get_recent_meetings(limit)
        
        return [
            {
                "id": r.id,
                "meeting_url": r.meeting_url,
                "platform": r.platform,
                "start_time": r.start_time,
                "duration_seconds": r.duration_seconds,
                "email_sent": r.email_sent,
                "created_at": r.created_at
            }
            for r in records
        ]

    async def get_analytics(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get analytics for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("analytics"):
            return self.analytics.to_dict(session["analytics"])
        
        return None

    async def get_diarization(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get speaker diarization for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("diarization"):
            diar = session["diarization"]
            return {
                "num_speakers": diar.num_speakers,
                "speaker_stats": diar.speaker_stats,
                "segments": [
                    {
                        "speaker": s.speaker,
                        "start": s.start,
                        "end": s.end,
                        "text": s.text
                    }
                    for s in diar.segments[:50]  # Limit segments
                ]
            }
        
        return None

    async def get_topics(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get topic segmentation for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("topics"):
            topics = session["topics"]
            return {
                "total_topics": topics.total_topics,
                "topics": [
                    {
                        "title": t.title,
                        "start_time": t.start_time,
                        "end_time": t.end_time,
                        "summary": t.summary
                    }
                    for t in topics.topics
                ]
            }
        
        return None

    async def get_sentiment(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get sentiment analysis for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("sentiment"):
            sent = session["sentiment"]
            return {
                "overall_sentiment": sent.overall_sentiment.value,
                "overall_confidence": sent.overall_confidence,
                "sentiment_distribution": sent.sentiment_distribution,
                "conflict_detected": sent.conflict_detected,
                "agreement_level": sent.agreement_level,
                "key_moments": sent.key_emotional_moments
            }
        
        return None

    async def get_action_items(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get extracted action items for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("action_items"):
            items = session["action_items"]
            return {
                "total_items": items.total_items,
                "items_with_owners": items.items_with_owners,
                "items_with_deadlines": items.items_with_deadlines,
                "items": [
                    {
                        "id": i.id,
                        "task": i.task,
                        "owner": i.owner,
                        "deadline": i.deadline,
                        "priority": i.priority,
                        "status": i.status
                    }
                    for i in items.items
                ]
            }
        
        return None

    async def get_followup_email(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get generated follow-up email for a session."""
        session = self._sessions.get(session_id)
        
        if session and session.get("followup_email"):
            email = session["followup_email"]
            return {
                "subject": email.subject,
                "body_text": email.body_text,
                "body_html": email.body_html,
                "action_items_included": email.action_items_included
            }
        
        return None

    async def search_memory(
        self,
        query: str,
        n_results: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search meeting memory."""
        if not self.memory._initialized:
            return []
        
        results = await self.memory.search(query, n_results, doc_type)
        
        return [
            {
                "meeting_id": r.document.meeting_id,
                "doc_type": r.document.doc_type,
                "content": r.snippet,
                "score": r.score
            }
            for r in results
        ]

    async def ask_memory(self, question: str) -> str:
        """Ask a question about past meetings using RAG."""
        if not self.memory._initialized:
            return "Meeting memory is not available."
        
        return await self.memory.query_with_llm(question, self.summarizer)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up Sunny AI Controller")
        
        # Stop any active recordings
        if self.recorder.is_active:
            await self.recorder.end_session()
        
        # Close HTTP clients
        await self.summarizer.close()
        
        logger.info("Cleanup completed")
