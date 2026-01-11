"""
LLM Pipeline for Meeting Summarization
Supports Google Gemini AI and Ollama for intelligent summarization.
"""

import asyncio
import json
import os
import re
from typing import List, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ActionItem:
    """An action item extracted from the meeting."""
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "Medium"


@dataclass
class MeetingSummary:
    """Complete meeting summary."""
    executive_summary: str
    key_discussion_points: List[str]
    decisions_made: List[str]
    action_items: List[ActionItem]
    confidence_score: float = 0.0
    raw_transcript: str = ""


class LLMPipeline:
    """LLM-based meeting summarization pipeline using Gemini or Ollama."""

    SYSTEM_PROMPT = """You are Sunny AI, a professional autonomous meeting assistant.

Your duties:
- Listen carefully and objectively.
- Never hallucinate facts.
- Extract only what was said.
- Prioritize clarity and brevity.
- Identify decisions and action items accurately.
- Write business-grade summaries.

Rules:
- No assumptions.
- No opinions.
- No exaggeration.
- Always be factual and structured.
- If information is unclear or not mentioned, say "Not explicitly discussed" rather than making up content."""

    def __init__(self, config: dict):
        sum_config = config.get("summarization", {})
        
        # Provider selection
        self.provider = sum_config.get("provider", "gemini")
        
        # Gemini settings
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", sum_config.get("gemini_api_key", ""))
        self.gemini_model = sum_config.get("gemini_model", "gemini-1.5-flash")
        
        # Ollama settings (fallback)
        self.ollama_base_url = sum_config.get("ollama_base_url", "http://localhost:11434")
        self.ollama_model = sum_config.get("ollama_model", "llama3")
        
        # Common settings
        self.max_tokens = sum_config.get("max_tokens", 2048)
        self.temperature = sum_config.get("temperature", 0.3)
        self.chunk_size = sum_config.get("chunk_size_tokens", 4000)
        self.overlap = sum_config.get("overlap_tokens", 200)
        
        # Initialize Gemini
        self._gemini_model = None
        if self.provider == "gemini" and self.gemini_api_key:
            self._init_gemini()

    def _init_gemini(self):
        """Initialize Google Gemini."""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            
            # Configure generation settings
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": 0.95,
            }
            
            # Safety settings - allow all content for meeting transcripts
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            self._gemini_model = genai.GenerativeModel(
                model_name=self.gemini_model,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=self.SYSTEM_PROMPT
            )
            
            logger.info(f"Gemini initialized with model: {self.gemini_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._gemini_model = None

    async def check_available(self) -> bool:
        """Check if the LLM provider is available."""
        if self.provider == "gemini":
            return self._gemini_model is not None
        else:
            # Check Ollama
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{self.ollama_base_url}/api/tags")
                    return response.status_code == 200
            except Exception:
                return False

    async def _call_gemini(self, prompt: str) -> str:
        """Make a call to Gemini API."""
        if not self._gemini_model:
            raise RuntimeError("Gemini not initialized")
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._gemini_model.generate_content(prompt)
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    async def _call_ollama(self, prompt: str) -> str:
        """Make a call to Ollama API."""
        import httpx
        
        payload = {
            "model": self.ollama_model,
            "prompt": f"{self.SYSTEM_PROMPT}\n\n{prompt}",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json().get("response", "")

    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider."""
        if self.provider == "gemini" and self._gemini_model:
            return await self._call_gemini(prompt)
        else:
            return await self._call_ollama(prompt)

    def _chunk_transcript(self, transcript: str) -> List[str]:
        """Split transcript into chunks for processing."""
        words = transcript.split()
        chunks = []
        
        chunk_words = self.chunk_size
        overlap_words = self.overlap
        
        i = 0
        while i < len(words):
            chunk_end = min(i + chunk_words, len(words))
            chunk = " ".join(words[i:chunk_end])
            chunks.append(chunk)
            i += chunk_words - overlap_words
            
            if chunk_end >= len(words):
                break

        return chunks

    async def summarize_transcript(self, transcript: str) -> MeetingSummary:
        """Generate a complete meeting summary from transcript."""
        logger.info(f"Starting meeting summarization with {self.provider}")
        
        # Check availability
        if not await self.check_available():
            if self.provider == "gemini":
                raise RuntimeError("Gemini API not available. Check your API key.")
            else:
                raise RuntimeError("Ollama not available. Start with: ollama serve")

        # Chunk the transcript if it's long
        chunks = self._chunk_transcript(transcript)
        logger.info(f"Processing {len(chunks)} transcript chunk(s)")

        if len(chunks) == 1:
            return await self._summarize_single(transcript)
        else:
            return await self._summarize_chunked(chunks, transcript)

    async def _summarize_single(self, transcript: str) -> MeetingSummary:
        """Summarize a single transcript chunk."""
        
        # Generate executive summary
        exec_summary = await self._generate_executive_summary(transcript)
        
        # Extract key points
        key_points = await self._extract_key_points(transcript)
        
        # Extract decisions
        decisions = await self._extract_decisions(transcript)
        
        # Extract action items
        action_items = await self._extract_action_items(transcript)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(exec_summary, key_points, decisions, action_items)

        return MeetingSummary(
            executive_summary=exec_summary,
            key_discussion_points=key_points,
            decisions_made=decisions,
            action_items=action_items,
            confidence_score=confidence,
            raw_transcript=transcript
        )

    async def _summarize_chunked(self, chunks: List[str], full_transcript: str) -> MeetingSummary:
        """Summarize multiple transcript chunks and combine."""
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            prompt = f"""Summarize this portion of a meeting transcript. Extract:
1. Main topics discussed
2. Any decisions mentioned
3. Any action items or tasks assigned

Transcript portion:
{chunk}

Provide a concise summary:"""
            
            summary = await self._call_llm(prompt)
            chunk_summaries.append(summary)

        combined_summary = "\n\n".join([
            f"[Part {i+1}]\n{s}" for i, s in enumerate(chunk_summaries)
        ])

        return await self._generate_final_summary(combined_summary, full_transcript)

    async def _generate_executive_summary(self, transcript: str) -> str:
        """Generate executive summary (max 200 words)."""
        prompt = f"""Based on this meeting transcript, write an executive summary.

Requirements:
- Maximum 200 words
- Capture the main purpose and outcomes of the meeting
- Be factual and objective
- Use professional business language

Transcript:
{transcript[:8000]}

Executive Summary:"""

        response = await self._call_llm(prompt)
        
        words = response.split()
        if len(words) > 200:
            response = " ".join(words[:200]) + "..."
        
        return response.strip()

    async def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract key discussion points."""
        prompt = f"""Extract the key discussion points from this meeting transcript.

Requirements:
- List 5-10 main topics or points discussed
- Each point should be a single, clear sentence
- Only include what was actually discussed
- Format as a numbered list

Transcript:
{transcript[:8000]}

Key Discussion Points:"""

        response = await self._call_llm(prompt)
        
        points = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line:
                cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)
                cleaned = re.sub(r'^[-•*]\s*', '', cleaned)
                if cleaned and len(cleaned) > 5:
                    points.append(cleaned)
        
        return points[:10]

    async def _extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions made during the meeting."""
        prompt = f"""Extract any decisions that were made during this meeting.

Requirements:
- Only include explicit decisions that were agreed upon
- Each decision should be a clear, actionable statement
- If no clear decisions were made, respond with "No explicit decisions recorded"
- Format as a numbered list

Transcript:
{transcript[:8000]}

Decisions Made:"""

        response = await self._call_llm(prompt)
        
        decisions = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and "no explicit decisions" not in line.lower():
                cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)
                cleaned = re.sub(r'^[-•*]\s*', '', cleaned)
                if cleaned and len(cleaned) > 5:
                    decisions.append(cleaned)
        
        return decisions

    async def _extract_action_items(self, transcript: str) -> List[ActionItem]:
        """Extract action items from the meeting."""
        prompt = f"""Extract action items from this meeting transcript.

For each action item, identify:
- Task: What needs to be done
- Owner: Who is responsible (if mentioned)
- Deadline: When it's due (if mentioned)

Format your response as JSON array:
[
  {{"task": "description", "owner": "name or null", "deadline": "date or null"}},
  ...
]

If no action items, return: []

Transcript:
{transcript[:8000]}

Action Items (JSON only, no other text):"""

        response = await self._call_llm(prompt)
        
        action_items = []
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                items = json.loads(json_match.group())
                for item in items:
                    if isinstance(item, dict) and item.get("task"):
                        action_items.append(ActionItem(
                            task=item.get("task", ""),
                            owner=item.get("owner"),
                            deadline=item.get("deadline"),
                            priority=item.get("priority", "Medium")
                        ))
        except json.JSONDecodeError:
            logger.warning("Could not parse action items as JSON, using text parsing")
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("[") and not line.startswith("]"):
                    cleaned = re.sub(r'^[\d]+[\.\)\-]\s*', '', line)
                    if cleaned and len(cleaned) > 5:
                        action_items.append(ActionItem(task=cleaned))
        
        return action_items

    async def _generate_final_summary(
        self, 
        combined_summaries: str, 
        full_transcript: str
    ) -> MeetingSummary:
        """Generate final summary from combined chunk summaries."""
        
        exec_prompt = f"""Based on these meeting summary parts, write a cohesive executive summary.

Requirements:
- Maximum 200 words
- Synthesize all parts into one coherent summary
- Be factual and professional

Summary Parts:
{combined_summaries}

Executive Summary:"""
        
        exec_summary = await self._call_llm(exec_prompt)
        words = exec_summary.split()
        if len(words) > 200:
            exec_summary = " ".join(words[:200]) + "..."

        key_points = await self._extract_key_points(combined_summaries)
        decisions = await self._extract_decisions(combined_summaries)
        action_items = await self._extract_action_items(combined_summaries)
        
        confidence = self._calculate_confidence(exec_summary, key_points, decisions, action_items)

        return MeetingSummary(
            executive_summary=exec_summary.strip(),
            key_discussion_points=key_points,
            decisions_made=decisions,
            action_items=action_items,
            confidence_score=confidence,
            raw_transcript=full_transcript
        )

    def _calculate_confidence(
        self,
        exec_summary: str,
        key_points: List[str],
        decisions: List[str],
        action_items: List[ActionItem]
    ) -> float:
        """Calculate confidence score for the summary."""
        score = 0.0
        
        if exec_summary and len(exec_summary) > 50:
            score += 0.3
        
        if key_points and len(key_points) >= 3:
            score += 0.3
        elif key_points:
            score += 0.15
        
        if decisions:
            score += 0.2
        
        if action_items:
            detailed_items = sum(1 for a in action_items if a.owner or a.deadline)
            if detailed_items > 0:
                score += 0.2
            else:
                score += 0.1
        
        return min(score, 1.0)

    async def close(self):
        """Cleanup resources."""
        pass
