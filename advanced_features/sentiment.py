"""
Sentiment & Emotion Analysis Module
Analyzes sentiment and emotional tone of meeting discussions.
"""

import asyncio
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EmotionalTone(Enum):
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    ENTHUSIASM = "enthusiasm"
    CONCERN = "concern"
    FRUSTRATION = "frustration"
    NEUTRAL = "neutral"


@dataclass
class SentimentSegment:
    """Sentiment analysis for a segment."""
    text: str
    sentiment: Sentiment
    confidence: float
    emotional_tones: List[EmotionalTone] = field(default_factory=list)
    speaker: Optional[str] = None
    start_time: float = 0
    end_time: float = 0


@dataclass
class SentimentResult:
    """Complete sentiment analysis result."""
    overall_sentiment: Sentiment = Sentiment.NEUTRAL
    overall_confidence: float = 0.0
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    segments: List[SentimentSegment] = field(default_factory=list)
    conflict_detected: bool = False
    agreement_level: float = 0.0
    key_emotional_moments: List[str] = field(default_factory=list)


class SentimentAnalyzer:
    """Analyzes sentiment and emotions in meeting transcripts."""

    # Sentiment keywords
    POSITIVE_WORDS = {
        'great', 'excellent', 'good', 'agree', 'yes', 'perfect', 'wonderful',
        'fantastic', 'amazing', 'love', 'happy', 'excited', 'pleased',
        'successful', 'achievement', 'progress', 'improvement', 'opportunity'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'disagree', 'no', 'problem', 'issue', 'concern',
        'worried', 'frustrated', 'disappointed', 'failed', 'failure', 'risk',
        'difficult', 'challenge', 'obstacle', 'delay', 'blocked'
    }
    
    AGREEMENT_PHRASES = [
        'i agree', 'that\'s right', 'exactly', 'absolutely', 'definitely',
        'good point', 'makes sense', 'sounds good', 'let\'s do it'
    ]
    
    DISAGREEMENT_PHRASES = [
        'i disagree', 'i don\'t think', 'not sure about', 'but', 'however',
        'on the other hand', 'that won\'t work', 'i\'m concerned'
    ]

    def __init__(self, config: dict, llm_pipeline=None):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("sentiment_enabled", True)
        self.use_llm = adv_config.get("sentiment_use_llm", True)
        
        self.llm = llm_pipeline
        self._transformer_model = None

    async def initialize(self) -> bool:
        """Initialize sentiment analysis models."""
        if not self.enabled:
            return False

        try:
            from transformers import pipeline
            
            self._transformer_model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU
            )
            logger.info("Sentiment analysis model loaded")
            return True
            
        except ImportError:
            logger.warning("Transformers not available, using keyword-based sentiment")
            return False
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            return False

    async def analyze(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> SentimentResult:
        """Analyze sentiment of the transcript."""
        if not self.enabled:
            return SentimentResult()

        logger.info("Starting sentiment analysis")

        try:
            # Analyze segments
            segments = await self._analyze_segments(transcript, transcript_segments)
            
            # Calculate overall sentiment
            overall = self._calculate_overall_sentiment(segments)
            
            # Detect conflicts and agreement
            conflict_detected, agreement_level = self._detect_conflict_agreement(transcript)
            
            # Find key emotional moments
            key_moments = self._find_key_moments(segments)
            
            result = SentimentResult(
                overall_sentiment=overall["sentiment"],
                overall_confidence=overall["confidence"],
                sentiment_distribution=overall["distribution"],
                segments=segments,
                conflict_detected=conflict_detected,
                agreement_level=agreement_level,
                key_emotional_moments=key_moments
            )
            
            logger.info(f"Sentiment analysis complete: {result.overall_sentiment.value}")
            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentResult()

    async def _analyze_segments(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> List[SentimentSegment]:
        """Analyze sentiment for each segment."""
        segments = []
        
        # Split transcript into chunks
        if transcript_segments:
            chunks = [
                {
                    "text": seg.get("text", ""),
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "speaker": seg.get("speaker")
                }
                for seg in transcript_segments
            ]
        else:
            # Split by sentences
            sentences = re.split(r'[.!?]+', transcript)
            chunks = [{"text": s.strip(), "start": 0, "end": 0} for s in sentences if s.strip()]
        
        for chunk in chunks:
            text = chunk["text"]
            if not text:
                continue
                
            sentiment, confidence = await self._analyze_text(text)
            tones = self._detect_emotional_tones(text)
            
            segments.append(SentimentSegment(
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                emotional_tones=tones,
                speaker=chunk.get("speaker"),
                start_time=chunk.get("start", 0),
                end_time=chunk.get("end", 0)
            ))
        
        return segments

    async def _analyze_text(self, text: str) -> tuple:
        """Analyze sentiment of a text segment."""
        if self._transformer_model:
            try:
                result = self._transformer_model(text[:512])[0]
                label = result["label"].lower()
                score = result["score"]
                
                if label == "positive":
                    return Sentiment.POSITIVE, score
                elif label == "negative":
                    return Sentiment.NEGATIVE, score
                else:
                    return Sentiment.NEUTRAL, score
            except Exception:
                pass
        
        # Fallback to keyword-based
        return self._keyword_sentiment(text)

    def _keyword_sentiment(self, text: str) -> tuple:
        """Keyword-based sentiment analysis."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)
        
        total = positive_count + negative_count
        if total == 0:
            return Sentiment.NEUTRAL, 0.5
        
        if positive_count > negative_count:
            confidence = positive_count / total
            return Sentiment.POSITIVE, confidence
        elif negative_count > positive_count:
            confidence = negative_count / total
            return Sentiment.NEGATIVE, confidence
        else:
            return Sentiment.NEUTRAL, 0.5

    def _detect_emotional_tones(self, text: str) -> List[EmotionalTone]:
        """Detect emotional tones in text."""
        tones = []
        text_lower = text.lower()
        
        # Check for agreement
        if any(phrase in text_lower for phrase in self.AGREEMENT_PHRASES):
            tones.append(EmotionalTone.AGREEMENT)
        
        # Check for disagreement
        if any(phrase in text_lower for phrase in self.DISAGREEMENT_PHRASES):
            tones.append(EmotionalTone.DISAGREEMENT)
        
        # Check for enthusiasm
        if '!' in text or any(w in text_lower for w in ['excited', 'amazing', 'fantastic']):
            tones.append(EmotionalTone.ENTHUSIASM)
        
        # Check for concern
        if any(w in text_lower for w in ['worried', 'concern', 'risk', 'careful']):
            tones.append(EmotionalTone.CONCERN)
        
        # Check for frustration
        if any(w in text_lower for w in ['frustrated', 'annoying', 'difficult', 'blocked']):
            tones.append(EmotionalTone.FRUSTRATION)
        
        if not tones:
            tones.append(EmotionalTone.NEUTRAL)
        
        return tones

    def _calculate_overall_sentiment(self, segments: List[SentimentSegment]) -> dict:
        """Calculate overall sentiment from segments."""
        if not segments:
            return {
                "sentiment": Sentiment.NEUTRAL,
                "confidence": 0.0,
                "distribution": {"positive": 0, "neutral": 100, "negative": 0}
            }
        
        counts = {Sentiment.POSITIVE: 0, Sentiment.NEUTRAL: 0, Sentiment.NEGATIVE: 0}
        total_confidence = 0
        
        for seg in segments:
            counts[seg.sentiment] += 1
            total_confidence += seg.confidence
        
        total = len(segments)
        distribution = {
            "positive": round((counts[Sentiment.POSITIVE] / total) * 100, 1),
            "neutral": round((counts[Sentiment.NEUTRAL] / total) * 100, 1),
            "negative": round((counts[Sentiment.NEGATIVE] / total) * 100, 1)
        }
        
        # Determine overall sentiment
        max_sentiment = max(counts, key=counts.get)
        avg_confidence = total_confidence / total
        
        return {
            "sentiment": max_sentiment,
            "confidence": avg_confidence,
            "distribution": distribution
        }

    def _detect_conflict_agreement(self, transcript: str) -> tuple:
        """Detect conflict and agreement levels."""
        text_lower = transcript.lower()
        
        agreement_count = sum(1 for p in self.AGREEMENT_PHRASES if p in text_lower)
        disagreement_count = sum(1 for p in self.DISAGREEMENT_PHRASES if p in text_lower)
        
        total = agreement_count + disagreement_count
        if total == 0:
            return False, 0.5
        
        agreement_level = agreement_count / total
        conflict_detected = disagreement_count > agreement_count
        
        return conflict_detected, agreement_level

    def _find_key_moments(self, segments: List[SentimentSegment]) -> List[str]:
        """Find key emotional moments."""
        key_moments = []
        
        for seg in segments:
            # Strong positive or negative
            if seg.confidence > 0.8 and seg.sentiment != Sentiment.NEUTRAL:
                moment = f"[{seg.sentiment.value.upper()}] {seg.text[:100]}..."
                key_moments.append(moment)
            
            # Conflict indicators
            if EmotionalTone.DISAGREEMENT in seg.emotional_tones:
                moment = f"[DISAGREEMENT] {seg.text[:100]}..."
                if moment not in key_moments:
                    key_moments.append(moment)
        
        return key_moments[:5]  # Limit to 5 key moments
