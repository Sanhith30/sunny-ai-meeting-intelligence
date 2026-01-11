"""
FastAPI REST API Server
Provides HTTP interface for Sunny AI.
"""

import asyncio
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import structlog

logger = structlog.get_logger(__name__)


# Request/Response Models
class MeetingRequest(BaseModel):
    meeting_url: str
    recipient_email: EmailStr
    send_email: bool = True


class MeetingResponse(BaseModel):
    session_id: int
    status: str
    message: str


class MeetingStatus(BaseModel):
    session_id: int
    status: str
    platform: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[str] = None
    transcript_available: bool = False
    summary_available: bool = False
    pdf_path: Optional[str] = None
    email_sent: bool = False


class TranscriptResponse(BaseModel):
    session_id: int
    transcript: str
    duration_seconds: float


class SummaryResponse(BaseModel):
    session_id: int
    executive_summary: str
    key_points: List[str]
    decisions: List[str]
    action_items: List[dict]


# Global state (in production, use proper state management)
_app_state = {
    "controller": None,
    "active_sessions": {}
}


def create_app(controller=None) -> FastAPI:
    """Create FastAPI application."""
    
    app = FastAPI(
        title="Sunny AI",
        description="Autonomous Meeting Attending & Summarization Agent",
        version="1.0.0"
    )
    
    if controller:
        _app_state["controller"] = controller

    @app.get("/")
    async def root():
        """Health check endpoint."""
        return {
            "name": "Sunny AI",
            "status": "running",
            "version": "1.0.0"
        }

    @app.get("/health")
    async def health_check():
        """Detailed health check."""
        return {
            "status": "healthy",
            "components": {
                "api": "ok",
                "controller": "ok" if _app_state["controller"] else "not initialized"
            }
        }

    @app.post("/meetings/join", response_model=MeetingResponse)
    async def join_meeting(request: MeetingRequest, background_tasks: BackgroundTasks):
        """Join a meeting and start recording."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            # Start meeting session in background
            session_id = await controller.start_session(
                meeting_url=request.meeting_url,
                recipient_email=request.recipient_email,
                send_email=request.send_email
            )
            
            return MeetingResponse(
                session_id=session_id,
                status="joining",
                message="Meeting session started. Sunny AI is joining the meeting."
            )
            
        except Exception as e:
            logger.error(f"Failed to join meeting: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/meetings/{session_id}/status", response_model=MeetingStatus)
    async def get_meeting_status(session_id: int):
        """Get status of a meeting session."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            status = await controller.get_session_status(session_id)
            
            if not status:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return MeetingStatus(**status)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/meetings/{session_id}/stop")
    async def stop_meeting(session_id: int):
        """Stop a meeting session."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            await controller.stop_session(session_id)
            return {"status": "stopped", "session_id": session_id}
            
        except Exception as e:
            logger.error(f"Failed to stop meeting: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/meetings/{session_id}/transcript", response_model=TranscriptResponse)
    async def get_transcript(session_id: int):
        """Get meeting transcript."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            transcript = await controller.get_transcript(session_id)
            
            if not transcript:
                raise HTTPException(status_code=404, detail="Transcript not available")
            
            return TranscriptResponse(**transcript)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get transcript: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/meetings/{session_id}/summary", response_model=SummaryResponse)
    async def get_summary(session_id: int):
        """Get meeting summary."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            summary = await controller.get_summary(session_id)
            
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not available")
            
            return SummaryResponse(**summary)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/meetings/{session_id}/pdf")
    async def download_pdf(session_id: int):
        """Download meeting summary PDF."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            pdf_path = await controller.get_pdf_path(session_id)
            
            if not pdf_path or not Path(pdf_path).exists():
                raise HTTPException(status_code=404, detail="PDF not available")
            
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=Path(pdf_path).name
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get PDF: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/meetings/recent")
    async def get_recent_meetings(limit: int = 10):
        """Get recent meeting sessions."""
        controller = _app_state["controller"]
        
        if not controller:
            raise HTTPException(status_code=503, detail="Controller not initialized")
        
        try:
            meetings = await controller.get_recent_meetings(limit)
            return {"meetings": meetings}
            
        except Exception as e:
            logger.error(f"Failed to get recent meetings: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app
