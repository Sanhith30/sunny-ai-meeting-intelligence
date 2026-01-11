"""
Topic Segmentation Module
Splits meeting transcript into semantic topics with timestamps.
"""

import asyncio
import re
from typing import List, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TopicSegment:
    """A topic segment from the meeting."""
    title: str
    start_time: float
    end_time: float
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    transcript_excerpt: str = ""


@dataclass
class TopicSegmentationResult:
    """Complete topic segmentation result."""
    topics: List[TopicSegment] = field(default_factory=list)
    total_topics: int = 0


class TopicSegmenter:
    """Segments meeting transcript into semantic topics."""

    def __init__(self, config: dict, llm_pipeline=None):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("topic_segmentation_enabled", True)
        self.min_topic_duration = adv_config.get("min_topic_duration_seconds", 60)
        self.max_topics = adv_config.get("max_topics", 10)
        
        self.llm = llm_pipeline

    async def segment_topics(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> TopicSegmentationResult:
        """Segment transcript into topics."""
        if not self.enabled:
            return TopicSegmentationResult()

        logger.info("Starting topic segmentation")

        if not transcript or len(transcript.strip()) < 100:
            logger.warning("Transcript too short for topic segmentation")
            return TopicSegmentationResult()

        try:
            # Use LLM to identify topics
            topics = await self._identify_topics_llm(transcript, transcript_segments)
            
            result = TopicSegmentationResult(
                topics=topics,
                total_topics=len(topics)
            )
            
            logger.info(f"Topic segmentation complete: {result.total_topics} topics")
            return result

        except Exception as e:
            logger.error(f"Topic segmentation failed: {e}")
            return TopicSegmentationResult()

    async def _identify_topics_llm(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> List[TopicSegment]:
        """Use LLM to identify and segment topics."""
        if not self.llm:
            return self._identify_topics_heuristic(transcript, transcript_segments)

        prompt = f"""Analyze this meeting transcript and identify distinct topics discussed.

For each topic, provide:
1. A short title (3-6 words)
2. Approximate start and end positions in the transcript (as percentage 0-100)
3. A brief summary (1-2 sentences)

Format your response as:
TOPIC 1: [Title]
START: [percentage]%
END: [percentage]%
SUMMARY: [summary]

TOPIC 2: [Title]
...

Transcript:
{transcript[:6000]}

Identify up to {self.max_topics} main topics:"""

        try:
            response = await self.llm._call_llm(prompt)
            topics = self._parse_topic_response(response, transcript, transcript_segments)
            return topics
        except Exception as e:
            logger.error(f"LLM topic identification failed: {e}")
            return self._identify_topics_heuristic(transcript, transcript_segments)

    def _parse_topic_response(
        self,
        response: str,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> List[TopicSegment]:
        """Parse LLM response into TopicSegment objects."""
        topics = []
        
        # Calculate total duration from segments
        total_duration = 0
        if transcript_segments:
            total_duration = max(seg.get("end", 0) for seg in transcript_segments)
        
        # Parse response
        topic_blocks = re.split(r'TOPIC \d+:', response, flags=re.IGNORECASE)
        
        for block in topic_blocks[1:]:  # Skip first empty split
            if not block.strip():
                continue
                
            # Extract title (first line)
            lines = block.strip().split('\n')
            title = lines[0].strip() if lines else "Untitled Topic"
            
            # Extract start/end percentages
            start_pct = 0
            end_pct = 100
            summary = ""
            
            for line in lines:
                line_lower = line.lower()
                if 'start:' in line_lower:
                    match = re.search(r'(\d+)', line)
                    if match:
                        start_pct = int(match.group(1))
                elif 'end:' in line_lower:
                    match = re.search(r'(\d+)', line)
                    if match:
                        end_pct = int(match.group(1))
                elif 'summary:' in line_lower:
                    summary = line.split(':', 1)[1].strip() if ':' in line else ""
            
            # Convert percentages to timestamps
            start_time = (start_pct / 100) * total_duration if total_duration else 0
            end_time = (end_pct / 100) * total_duration if total_duration else 0
            
            # Extract transcript excerpt
            transcript_len = len(transcript)
            excerpt_start = int((start_pct / 100) * transcript_len)
            excerpt_end = int((end_pct / 100) * transcript_len)
            excerpt = transcript[excerpt_start:excerpt_end][:500]
            
            topics.append(TopicSegment(
                title=title,
                start_time=start_time,
                end_time=end_time,
                summary=summary,
                transcript_excerpt=excerpt
            ))
        
        return topics[:self.max_topics]

    def _identify_topics_heuristic(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> List[TopicSegment]:
        """Fallback heuristic-based topic identification."""
        topics = []
        
        # Simple approach: split by long pauses or paragraph breaks
        paragraphs = transcript.split('\n\n')
        
        if len(paragraphs) < 2:
            # Single topic
            topics.append(TopicSegment(
                title="Meeting Discussion",
                start_time=0,
                end_time=0,
                summary="Full meeting transcript",
                transcript_excerpt=transcript[:500]
            ))
        else:
            # Create topics from paragraphs
            chunk_size = max(1, len(paragraphs) // self.max_topics)
            
            for i in range(0, len(paragraphs), chunk_size):
                chunk = '\n\n'.join(paragraphs[i:i + chunk_size])
                
                # Generate simple title from first few words
                words = chunk.split()[:10]
                title = ' '.join(words[:5]) + "..." if len(words) > 5 else ' '.join(words)
                
                topics.append(TopicSegment(
                    title=f"Topic {len(topics) + 1}: {title}",
                    start_time=0,
                    end_time=0,
                    summary="",
                    transcript_excerpt=chunk[:500]
                ))
        
        return topics[:self.max_topics]

    def format_topic_timeline(self, result: TopicSegmentationResult) -> str:
        """Format topics as a timeline string."""
        lines = ["TOPIC TIMELINE", "=" * 40]
        
        for i, topic in enumerate(result.topics, 1):
            start_str = self._format_timestamp(topic.start_time)
            end_str = self._format_timestamp(topic.end_time)
            
            lines.append(f"\n{i}. {topic.title}")
            lines.append(f"   Time: {start_str} – {end_str}")
            if topic.summary:
                lines.append(f"   Summary: {topic.summary}")
        
        return '\n'.join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
