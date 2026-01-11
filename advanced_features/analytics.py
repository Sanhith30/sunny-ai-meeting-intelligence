"""
Meeting Analytics Module
Generates comprehensive meeting statistics and metrics.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SpeakerStats:
    """Statistics for a single speaker."""
    speaker_id: str
    speaking_time_seconds: float = 0
    speaking_percentage: float = 0
    word_count: int = 0
    segment_count: int = 0
    avg_segment_duration: float = 0


@dataclass
class MeetingMetrics:
    """Comprehensive meeting metrics."""
    # Basic metrics
    meeting_id: Optional[int] = None
    platform: str = ""
    date: Optional[datetime] = None
    duration_seconds: float = 0
    duration_formatted: str = ""
    
    # Speaker metrics
    num_speakers: int = 0
    speaker_stats: List[SpeakerStats] = field(default_factory=list)
    most_active_speaker: Optional[str] = None
    
    # Content metrics
    total_words: int = 0
    words_per_minute: float = 0
    num_topics: int = 0
    num_decisions: int = 0
    num_action_items: int = 0
    
    # Sentiment metrics
    overall_sentiment: str = "neutral"
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    conflict_detected: bool = False
    agreement_level: float = 0
    
    # Engagement metrics
    participation_balance: float = 0  # 0-1, higher = more balanced
    silence_percentage: float = 0
    
    # Quality metrics
    transcription_confidence: float = 0
    summary_confidence: float = 0


class MeetingAnalytics:
    """Generates meeting analytics and metrics."""

    def __init__(self, config: dict):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("analytics_enabled", True)

    def generate_metrics(
        self,
        duration_seconds: float,
        transcript: str = "",
        transcript_segments: List[dict] = None,
        diarization_result: Any = None,
        topic_result: Any = None,
        sentiment_result: Any = None,
        action_items_result: Any = None,
        summary: Any = None,
        platform: str = "",
        meeting_date: datetime = None
    ) -> MeetingMetrics:
        """Generate comprehensive meeting metrics."""
        if not self.enabled:
            return MeetingMetrics()

        logger.info("Generating meeting analytics")

        metrics = MeetingMetrics(
            platform=platform,
            date=meeting_date or datetime.now(),
            duration_seconds=duration_seconds,
            duration_formatted=self._format_duration(duration_seconds)
        )

        # Basic content metrics
        if transcript:
            metrics.total_words = len(transcript.split())
            if duration_seconds > 0:
                metrics.words_per_minute = (metrics.total_words / duration_seconds) * 60

        # Speaker metrics
        if diarization_result and hasattr(diarization_result, 'speaker_stats'):
            metrics.num_speakers = diarization_result.num_speakers
            metrics.speaker_stats = self._calculate_speaker_stats(
                diarization_result.speaker_stats,
                duration_seconds
            )
            if metrics.speaker_stats:
                metrics.most_active_speaker = max(
                    metrics.speaker_stats,
                    key=lambda x: x.speaking_time_seconds
                ).speaker_id
                metrics.participation_balance = self._calculate_balance(metrics.speaker_stats)

        # Topic metrics
        if topic_result and hasattr(topic_result, 'total_topics'):
            metrics.num_topics = topic_result.total_topics

        # Sentiment metrics
        if sentiment_result:
            if hasattr(sentiment_result, 'overall_sentiment'):
                metrics.overall_sentiment = sentiment_result.overall_sentiment.value
            if hasattr(sentiment_result, 'sentiment_distribution'):
                metrics.sentiment_distribution = sentiment_result.sentiment_distribution
            if hasattr(sentiment_result, 'conflict_detected'):
                metrics.conflict_detected = sentiment_result.conflict_detected
            if hasattr(sentiment_result, 'agreement_level'):
                metrics.agreement_level = sentiment_result.agreement_level

        # Action items metrics
        if action_items_result and hasattr(action_items_result, 'total_items'):
            metrics.num_action_items = action_items_result.total_items

        # Summary metrics
        if summary:
            if hasattr(summary, 'decisions_made'):
                metrics.num_decisions = len(summary.decisions_made)
            if hasattr(summary, 'confidence_score'):
                metrics.summary_confidence = summary.confidence_score

        logger.info(f"Analytics generated: {metrics.num_speakers} speakers, "
                   f"{metrics.num_topics} topics, {metrics.num_action_items} action items")
        
        return metrics

    def _calculate_speaker_stats(
        self,
        speaker_times: Dict[str, float],
        total_duration: float
    ) -> List[SpeakerStats]:
        """Calculate detailed speaker statistics."""
        stats = []
        
        for speaker_id, speaking_time in speaker_times.items():
            percentage = (speaking_time / total_duration * 100) if total_duration > 0 else 0
            
            stats.append(SpeakerStats(
                speaker_id=speaker_id,
                speaking_time_seconds=speaking_time,
                speaking_percentage=round(percentage, 1)
            ))
        
        # Sort by speaking time
        stats.sort(key=lambda x: x.speaking_time_seconds, reverse=True)
        
        return stats

    def _calculate_balance(self, speaker_stats: List[SpeakerStats]) -> float:
        """Calculate participation balance (0-1, higher = more balanced)."""
        if not speaker_stats or len(speaker_stats) < 2:
            return 1.0
        
        percentages = [s.speaking_percentage for s in speaker_stats]
        
        # Perfect balance would be equal percentages
        ideal = 100 / len(percentages)
        
        # Calculate deviation from ideal
        total_deviation = sum(abs(p - ideal) for p in percentages)
        max_deviation = 2 * (100 - ideal)  # Maximum possible deviation
        
        balance = 1 - (total_deviation / max_deviation) if max_deviation > 0 else 1.0
        
        return round(balance, 2)

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

    def format_analytics_report(self, metrics: MeetingMetrics) -> str:
        """Format metrics as a text report."""
        lines = [
            "MEETING ANALYTICS REPORT",
            "=" * 50,
            "",
            "BASIC INFORMATION",
            "-" * 30,
            f"Platform: {metrics.platform or 'Unknown'}",
            f"Date: {metrics.date.strftime('%Y-%m-%d %H:%M') if metrics.date else 'Unknown'}",
            f"Duration: {metrics.duration_formatted}",
            "",
            "PARTICIPATION",
            "-" * 30,
            f"Number of Speakers: {metrics.num_speakers}",
            f"Most Active Speaker: {metrics.most_active_speaker or 'Unknown'}",
            f"Participation Balance: {metrics.participation_balance:.0%}",
        ]
        
        if metrics.speaker_stats:
            lines.append("")
            lines.append("Speaker Breakdown:")
            for stat in metrics.speaker_stats:
                lines.append(f"  • {stat.speaker_id}: {stat.speaking_percentage:.1f}% "
                           f"({self._format_duration(stat.speaking_time_seconds)})")
        
        lines.extend([
            "",
            "CONTENT",
            "-" * 30,
            f"Total Words: {metrics.total_words:,}",
            f"Words per Minute: {metrics.words_per_minute:.1f}",
            f"Topics Discussed: {metrics.num_topics}",
            f"Decisions Made: {metrics.num_decisions}",
            f"Action Items: {metrics.num_action_items}",
            "",
            "SENTIMENT",
            "-" * 30,
            f"Overall Tone: {metrics.overall_sentiment.title()}",
            f"Conflict Detected: {'Yes' if metrics.conflict_detected else 'No'}",
            f"Agreement Level: {metrics.agreement_level:.0%}",
        ])
        
        if metrics.sentiment_distribution:
            lines.append("Sentiment Distribution:")
            for sentiment, pct in metrics.sentiment_distribution.items():
                lines.append(f"  • {sentiment.title()}: {pct:.1f}%")
        
        lines.extend([
            "",
            "QUALITY",
            "-" * 30,
            f"Summary Confidence: {metrics.summary_confidence:.0%}",
            "",
            "=" * 50
        ])
        
        return '\n'.join(lines)

    def to_dict(self, metrics: MeetingMetrics) -> Dict[str, Any]:
        """Convert metrics to dictionary for storage."""
        return {
            "meeting_id": metrics.meeting_id,
            "platform": metrics.platform,
            "date": metrics.date.isoformat() if metrics.date else None,
            "duration_seconds": metrics.duration_seconds,
            "duration_formatted": metrics.duration_formatted,
            "num_speakers": metrics.num_speakers,
            "most_active_speaker": metrics.most_active_speaker,
            "total_words": metrics.total_words,
            "words_per_minute": metrics.words_per_minute,
            "num_topics": metrics.num_topics,
            "num_decisions": metrics.num_decisions,
            "num_action_items": metrics.num_action_items,
            "overall_sentiment": metrics.overall_sentiment,
            "sentiment_distribution": metrics.sentiment_distribution,
            "conflict_detected": metrics.conflict_detected,
            "agreement_level": metrics.agreement_level,
            "participation_balance": metrics.participation_balance,
            "summary_confidence": metrics.summary_confidence,
            "speaker_stats": [
                {
                    "speaker_id": s.speaker_id,
                    "speaking_time_seconds": s.speaking_time_seconds,
                    "speaking_percentage": s.speaking_percentage
                }
                for s in metrics.speaker_stats
            ]
        }
