"""
Sunny AI Web Application
Beautiful web interface for the meeting assistant.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn
import structlog

from utils.config import load_config, get_default_config
from utils.logger import setup_logging
from controller import SunnyAIController

logger = structlog.get_logger(__name__)

# Environment
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Initialize app
app = FastAPI(
    title="Sunny AI",
    description="Autonomous Meeting Assistant",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Disable docs in production
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Security Middleware
if IS_PRODUCTION:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# CORS - configure for your domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Global controller
controller: Optional[SunnyAIController] = None
config: dict = {}


# Request Models
class MeetingRequest(BaseModel):
    meeting_url: str
    recipient_email: EmailStr
    send_email: bool = True


class MeetingResponse(BaseModel):
    session_id: int
    status: str
    message: str


class ApiKeyRequest(BaseModel):
    api_key: str


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    global controller
    
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    llm_available = False
    
    if controller:
        llm_available = await controller.summarizer.check_available()
    
    return {
        "status": "healthy",
        "service": "Sunny AI",
        "timestamp": datetime.now().isoformat(),
        "gemini_configured": gemini_configured,
        "llm_available": llm_available,
        "provider": config.get("summarization", {}).get("provider", "gemini")
    }


@app.post("/api/config/apikey")
async def set_api_key(request: ApiKeyRequest):
    """Set the Gemini API key."""
    global controller, config
    
    # Only reinitialize if key is different or not set
    current_key = os.getenv("GEMINI_API_KEY", "")
    if current_key == request.api_key:
        return {"status": "success", "message": "API key already configured"}
    
    os.environ["GEMINI_API_KEY"] = request.api_key
    
    # Reinitialize controller with new key
    if controller:
        await controller.cleanup()
    
    controller = SunnyAIController(config)
    await controller.initialize()
    
    # Check if it works
    available = await controller.summarizer.check_available()
    
    if available:
        return {"status": "success", "message": "API key configured successfully"}
    else:
        return {"status": "error", "message": "API key invalid or Gemini unavailable"}


@app.post("/api/meetings/join", response_model=MeetingResponse)
async def join_meeting(request: MeetingRequest):
    """Join a meeting and start recording."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    try:
        session_id = await controller.start_session(
            meeting_url=request.meeting_url,
            recipient_email=request.recipient_email,
            send_email=request.send_email
        )
        
        return MeetingResponse(
            session_id=session_id,
            status="joining",
            message="Sunny AI is joining the meeting"
        )
    except Exception as e:
        logger.error(f"Failed to join meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meetings/{session_id}/status")
async def get_status(session_id: int):
    """Get meeting session status."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    status = await controller.get_session_status(session_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return status


@app.post("/api/meetings/{session_id}/stop")
async def stop_meeting(session_id: int):
    """Stop a meeting session."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    try:
        await controller.stop_session(session_id)
        return {"status": "stopped", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meetings/{session_id}/transcript")
async def get_transcript(session_id: int):
    """Get meeting transcript."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    transcript = await controller.get_transcript(session_id)
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")
    
    return transcript


@app.get("/api/meetings/{session_id}/summary")
async def get_summary(session_id: int):
    """Get meeting summary."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    summary = await controller.get_summary(session_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not available")
    
    return summary


@app.get("/api/meetings/{session_id}/pdf")
async def download_pdf(session_id: int):
    """Download meeting summary PDF."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    pdf_path = await controller.get_pdf_path(session_id)
    
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not available")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name
    )


@app.get("/api/meetings/recent")
async def get_recent():
    """Get recent meetings."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    meetings = await controller.get_recent_meetings(10)
    return {"meetings": meetings}


# Advanced Features API Endpoints
# ================================

@app.get("/api/meetings/{session_id}/analytics")
async def get_analytics(session_id: int):
    """Get meeting analytics."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    analytics = await controller.get_analytics(session_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not available")
    
    return analytics


@app.get("/api/meetings/{session_id}/diarization")
async def get_diarization(session_id: int):
    """Get speaker diarization results."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    diarization = await controller.get_diarization(session_id)
    
    if not diarization:
        raise HTTPException(status_code=404, detail="Diarization not available")
    
    return diarization


@app.get("/api/meetings/{session_id}/topics")
async def get_topics(session_id: int):
    """Get topic segmentation results."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    topics = await controller.get_topics(session_id)
    
    if not topics:
        raise HTTPException(status_code=404, detail="Topics not available")
    
    return topics


@app.get("/api/meetings/{session_id}/sentiment")
async def get_sentiment(session_id: int):
    """Get sentiment analysis results."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    sentiment = await controller.get_sentiment(session_id)
    
    if not sentiment:
        raise HTTPException(status_code=404, detail="Sentiment analysis not available")
    
    return sentiment


@app.get("/api/meetings/{session_id}/action-items")
async def get_action_items(session_id: int):
    """Get extracted action items."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    action_items = await controller.get_action_items(session_id)
    
    if not action_items:
        raise HTTPException(status_code=404, detail="Action items not available")
    
    return action_items


@app.get("/api/meetings/{session_id}/followup-email")
async def get_followup_email(session_id: int):
    """Get generated follow-up email."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    email = await controller.get_followup_email(session_id)
    
    if not email:
        raise HTTPException(status_code=404, detail="Follow-up email not available")
    
    return email


class MemorySearchRequest(BaseModel):
    query: str
    n_results: int = 5
    doc_type: Optional[str] = None


@app.post("/api/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Search meeting memory."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    results = await controller.search_memory(
        query=request.query,
        n_results=request.n_results,
        doc_type=request.doc_type
    )
    
    return {"results": results}


class MemoryQuestionRequest(BaseModel):
    question: str


@app.post("/api/memory/ask")
async def ask_memory(request: MemoryQuestionRequest):
    """Ask a question about past meetings using RAG."""
    global controller
    
    if not controller:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    answer = await controller.ask_memory(request.question)
    
    return {"question": request.question, "answer": answer}


@app.on_event("startup")
async def startup():
    """Initialize controller on startup."""
    global controller, config
    
    setup_logging("INFO")
    
    try:
        config = load_config("config.yaml")
    except FileNotFoundError:
        config = get_default_config()
    
    controller = SunnyAIController(config)
    await controller.initialize()
    
    logger.info("Sunny AI Web Server started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global controller
    
    if controller:
        await controller.cleanup()
    
    logger.info("Sunny AI Web Server stopped")


def main():
    """Run the web server."""
    print("\n" + "="*60)
    print("☀️  SUNNY AI - Web Interface")
    print("="*60)
    
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    
    if IS_PRODUCTION:
        print(f"\n🚀 Running in PRODUCTION mode")
        print(f"🌐 Server: http://{host}:{port}")
    else:
        print(f"\n🌐 Open your browser at: http://localhost:{port}")
        print(f"📚 API documentation at: http://localhost:{port}/docs")
    
    print("\nPress Ctrl+C to stop the server.\n")
    
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=not IS_PRODUCTION,
        workers=workers if IS_PRODUCTION else 1,
        log_level="warning" if IS_PRODUCTION else "info",
        access_log=not IS_PRODUCTION
    )


if __name__ == "__main__":
    main()
