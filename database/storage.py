"""
Database Storage Module
SQLite-based storage for transcripts and meeting data.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import aiosqlite
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MeetingRecord:
    """Database record for a meeting."""
    id: Optional[int] = None
    meeting_url: str = ""
    platform: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    audio_file: Optional[str] = None
    transcript: Optional[str] = None
    summary_json: Optional[str] = None
    pdf_path: Optional[str] = None
    email_sent: bool = False
    email_recipient: Optional[str] = None
    created_at: Optional[str] = None


class MeetingStorage:
    """SQLite storage for meeting data."""

    def __init__(self, db_path: str = "./data/meetings.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL DEFAULT 0,
                    audio_file TEXT,
                    transcript TEXT,
                    summary_json TEXT,
                    pdf_path TEXT,
                    email_sent INTEGER DEFAULT 0,
                    email_recipient TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_meetings_platform 
                ON meetings(platform)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_meetings_created 
                ON meetings(created_at)
            """)
            
            await db.commit()
        
        self._initialized = True
        logger.info(f"Database initialized: {self.db_path}")

    async def save_meeting(self, record: MeetingRecord) -> int:
        """Save a meeting record."""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO meetings (
                    meeting_url, platform, start_time, end_time,
                    duration_seconds, audio_file, transcript, summary_json,
                    pdf_path, email_sent, email_recipient
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.meeting_url,
                record.platform,
                record.start_time,
                record.end_time,
                record.duration_seconds,
                record.audio_file,
                record.transcript,
                record.summary_json,
                record.pdf_path,
                1 if record.email_sent else 0,
                record.email_recipient
            ))
            await db.commit()
            
            record.id = cursor.lastrowid
            logger.info(f"Saved meeting record: {record.id}")
            return record.id

    async def update_meeting(self, record: MeetingRecord) -> None:
        """Update an existing meeting record."""
        if not record.id:
            raise ValueError("Record ID required for update")
        
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE meetings SET
                    meeting_url = ?,
                    platform = ?,
                    start_time = ?,
                    end_time = ?,
                    duration_seconds = ?,
                    audio_file = ?,
                    transcript = ?,
                    summary_json = ?,
                    pdf_path = ?,
                    email_sent = ?,
                    email_recipient = ?
                WHERE id = ?
            """, (
                record.meeting_url,
                record.platform,
                record.start_time,
                record.end_time,
                record.duration_seconds,
                record.audio_file,
                record.transcript,
                record.summary_json,
                record.pdf_path,
                1 if record.email_sent else 0,
                record.email_recipient,
                record.id
            ))
            await db.commit()
            logger.info(f"Updated meeting record: {record.id}")

    async def get_meeting(self, meeting_id: int) -> Optional[MeetingRecord]:
        """Get a meeting by ID."""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM meetings WHERE id = ?",
                (meeting_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return MeetingRecord(
                    id=row['id'],
                    meeting_url=row['meeting_url'],
                    platform=row['platform'],
                    start_time=row['start_time'],
                    end_time=row['end_time'],
                    duration_seconds=row['duration_seconds'],
                    audio_file=row['audio_file'],
                    transcript=row['transcript'],
                    summary_json=row['summary_json'],
                    pdf_path=row['pdf_path'],
                    email_sent=bool(row['email_sent']),
                    email_recipient=row['email_recipient'],
                    created_at=row['created_at']
                )
            return None

    async def get_recent_meetings(self, limit: int = 10) -> List[MeetingRecord]:
        """Get recent meetings."""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM meetings ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            
            return [
                MeetingRecord(
                    id=row['id'],
                    meeting_url=row['meeting_url'],
                    platform=row['platform'],
                    start_time=row['start_time'],
                    end_time=row['end_time'],
                    duration_seconds=row['duration_seconds'],
                    audio_file=row['audio_file'],
                    transcript=row['transcript'],
                    summary_json=row['summary_json'],
                    pdf_path=row['pdf_path'],
                    email_sent=bool(row['email_sent']),
                    email_recipient=row['email_recipient'],
                    created_at=row['created_at']
                )
                for row in rows
            ]

    async def delete_meeting(self, meeting_id: int) -> bool:
        """Delete a meeting record."""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM meetings WHERE id = ?",
                (meeting_id,)
            )
            await db.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted meeting record: {meeting_id}")
            return deleted
