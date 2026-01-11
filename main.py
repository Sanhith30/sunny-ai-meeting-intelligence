#!/usr/bin/env python3
"""
Sunny AI - Autonomous Meeting Attending & Summarization Agent
Main entry point for the application.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import load_config, get_default_config
from utils.logger import setup_logging
from controller import SunnyAIController
import structlog

logger = structlog.get_logger(__name__)


async def run_single_meeting(
    meeting_url: str,
    recipient_email: str,
    config: dict,
    send_email: bool = True
) -> None:
    """Run a single meeting session."""
    
    controller = SunnyAIController(config)
    
    try:
        await controller.initialize()
        
        print("\n" + "="*60)
        print("☀️  SUNNY AI - Autonomous Meeting Assistant")
        print("="*60)
        print(f"\n📍 Meeting URL: {meeting_url}")
        print(f"📧 Recipient: {recipient_email}")
        print(f"📤 Send Email: {'Yes' if send_email else 'No'}")
        print("\n" + "-"*60)
        print("Starting meeting session...")
        print("-"*60 + "\n")
        
        # Start session
        session_id = await controller.start_session(
            meeting_url=meeting_url,
            recipient_email=recipient_email,
            send_email=send_email
        )
        
        print(f"✅ Session started (ID: {session_id})")
        print("🤖 Sunny AI is joining the meeting...")
        print("\nPress Ctrl+C to stop the session manually.\n")
        
        # Monitor session
        last_status = None
        while True:
            await asyncio.sleep(5)
            
            status = await controller.get_session_status(session_id)
            if status and status["status"] != last_status:
                last_status = status["status"]
                _print_status_update(status)
            
            if status and status["status"] in ["completed", "error", "stopped"]:
                break
        
        # Print final results
        if status["status"] == "completed":
            _print_completion_summary(controller, session_id, status)
        elif status["status"] == "error":
            print(f"\n❌ Session ended with error")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopping session...")
        await controller.stop_session(session_id)
        print("Session stopped by user.")
        
    finally:
        await controller.cleanup()


def _print_status_update(status: dict) -> None:
    """Print status update."""
    status_icons = {
        "starting": "🔄",
        "joining": "🚪",
        "recording": "🎙️",
        "processing": "⚙️",
        "transcribing": "📝",
        "summarizing": "🧠",
        "generating_pdf": "📄",
        "sending_email": "📧",
        "completed": "✅",
        "error": "❌",
        "stopped": "⏹️"
    }
    
    icon = status_icons.get(status["status"], "•")
    print(f"{icon} Status: {status['status'].replace('_', ' ').title()}")


def _print_completion_summary(controller, session_id: int, status: dict) -> None:
    """Print completion summary."""
    print("\n" + "="*60)
    print("✅ MEETING SESSION COMPLETED")
    print("="*60)
    
    if status.get("platform"):
        print(f"📍 Platform: {status['platform'].replace('_', ' ').title()}")
    if status.get("duration"):
        print(f"⏱️  Duration: {status['duration']}")
    if status.get("pdf_path"):
        print(f"📄 PDF Report: {status['pdf_path']}")
    if status.get("email_sent"):
        print(f"📧 Email: Sent successfully")
    
    print("="*60 + "\n")


async def run_api_server(config: dict, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI server."""
    import uvicorn
    from api.server import create_app
    
    controller = SunnyAIController(config)
    await controller.initialize()
    
    app = create_app(controller)
    
    print("\n" + "="*60)
    print("☀️  SUNNY AI - API Server")
    print("="*60)
    print(f"\n🌐 Server running at http://{host}:{port}")
    print(f"📚 API docs at http://{host}:{port}/docs")
    print("\nPress Ctrl+C to stop the server.\n")
    
    config_uvicorn = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config_uvicorn)
    
    try:
        await server.serve()
    finally:
        await controller.cleanup()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sunny AI - Autonomous Meeting Attending & Summarization Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Join a meeting and send summary to email
  python main.py --url "https://meet.google.com/abc-defg-hij" --email "user@example.com"
  
  # Join without sending email
  python main.py --url "https://zoom.us/j/123456789" --email "user@example.com" --no-email
  
  # Run API server
  python main.py --server --port 8000
  
  # Use custom config
  python main.py --config custom_config.yaml --url "..." --email "..."
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        help="Meeting URL (Zoom or Google Meet)"
    )
    parser.add_argument(
        "--email", "-e",
        help="Recipient email address"
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Don't send email after processing"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--server", "-s",
        action="store_true",
        help="Run as API server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        print("Using default configuration...")
        config = get_default_config()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run appropriate mode
    if args.server:
        asyncio.run(run_api_server(config, args.host, args.port))
    elif args.url and args.email:
        asyncio.run(run_single_meeting(
            meeting_url=args.url,
            recipient_email=args.email,
            config=config,
            send_email=not args.no_email
        ))
    else:
        parser.print_help()
        print("\n❌ Error: Either --server or both --url and --email are required.")
        sys.exit(1)


if __name__ == "__main__":
    main()
