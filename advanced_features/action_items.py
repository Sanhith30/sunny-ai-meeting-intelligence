"""
Action Item Extraction Engine
Extracts tasks, owners, and deadlines from meeting transcripts.
"""

import asyncio
import re
import json
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ActionItem:
    """An action item extracted from the meeting."""
    id: int = 0
    task: str = ""
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "Medium"
    status: str = "Pending"
    context: str = ""
    confidence: float = 1.0
    source_timestamp: float = 0


@dataclass
class ActionItemResult:
    """Complete action item extraction result."""
    items: List[ActionItem] = field(default_factory=list)
    total_items: int = 0
    items_with_owners: int = 0
    items_with_deadlines: int = 0


class ActionItemExtractor:
    """Extracts action items from meeting transcripts."""

    # Action keywords
    ACTION_KEYWORDS = [
        'will', 'should', 'need to', 'have to', 'must', 'going to',
        'action item', 'task', 'todo', 'to do', 'follow up', 'follow-up',
        'take care of', 'responsible for', 'assigned to', 'deadline',
        'by next', 'by end of', 'complete by', 'finish by'
    ]
    
    # Time expressions
    TIME_PATTERNS = [
        (r'by (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', 'next_weekday'),
        (r'by end of (week|month|day|quarter)', 'end_of'),
        (r'by (\d{1,2}/\d{1,2}(?:/\d{2,4})?)', 'date'),
        (r'by (tomorrow|next week|next month)', 'relative'),
        (r'within (\d+) (days?|weeks?|months?)', 'within'),
        (r'(asap|immediately|urgent)', 'urgent')
    ]

    def __init__(self, config: dict, llm_pipeline=None):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("action_items_enabled", True)
        self.use_llm = adv_config.get("action_items_use_llm", True)
        
        self.llm = llm_pipeline

    async def extract(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> ActionItemResult:
        """Extract action items from transcript."""
        if not self.enabled:
            return ActionItemResult()

        logger.info("Starting action item extraction")

        try:
            if self.llm and self.use_llm:
                items = await self._extract_with_llm(transcript)
            else:
                items = self._extract_with_patterns(transcript, transcript_segments)
            
            # Assign IDs
            for i, item in enumerate(items, 1):
                item.id = i
            
            # Calculate stats
            items_with_owners = sum(1 for item in items if item.owner)
            items_with_deadlines = sum(1 for item in items if item.deadline)
            
            result = ActionItemResult(
                items=items,
                total_items=len(items),
                items_with_owners=items_with_owners,
                items_with_deadlines=items_with_deadlines
            )
            
            logger.info(f"Extracted {result.total_items} action items")
            return result

        except Exception as e:
            logger.error(f"Action item extraction failed: {e}")
            return ActionItemResult()

    async def _extract_with_llm(self, transcript: str) -> List[ActionItem]:
        """Extract action items using LLM."""
        prompt = f"""Extract all action items from this meeting transcript.

For each action item, identify:
- Task: What needs to be done (clear, actionable description)
- Owner: Who is responsible (name if mentioned, otherwise null)
- Deadline: When it's due (if mentioned, otherwise null)
- Priority: High/Medium/Low based on urgency indicators

Return as JSON array:
[
  {{"task": "description", "owner": "name or null", "deadline": "date or null", "priority": "High/Medium/Low", "context": "brief context"}},
  ...
]

If no action items found, return: []

Transcript:
{transcript[:8000]}

Action Items (JSON only):"""

        try:
            response = await self.llm._call_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_with_patterns(transcript, None)

    def _parse_llm_response(self, response: str) -> List[ActionItem]:
        """Parse LLM response into ActionItem objects."""
        items = []
        
        try:
            # Find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                
                for item_data in data:
                    if isinstance(item_data, dict) and item_data.get("task"):
                        items.append(ActionItem(
                            task=item_data.get("task", ""),
                            owner=item_data.get("owner"),
                            deadline=item_data.get("deadline"),
                            priority=item_data.get("priority", "Medium"),
                            context=item_data.get("context", ""),
                            confidence=0.9
                        ))
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON")
        
        return items

    def _extract_with_patterns(
        self,
        transcript: str,
        transcript_segments: List[dict] = None
    ) -> List[ActionItem]:
        """Extract action items using pattern matching."""
        items = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check for action keywords
            has_action = any(kw in sentence_lower for kw in self.ACTION_KEYWORDS)
            
            if has_action:
                item = self._parse_action_sentence(sentence)
                if item and item.task:
                    items.append(item)
        
        # Deduplicate similar items
        items = self._deduplicate_items(items)
        
        return items

    def _parse_action_sentence(self, sentence: str) -> Optional[ActionItem]:
        """Parse a sentence to extract action item details."""
        sentence_lower = sentence.lower()
        
        # Extract owner (look for names or pronouns)
        owner = None
        owner_patterns = [
            r'(\w+) will\b',
            r'(\w+) should\b',
            r'(\w+) needs? to\b',
            r'assigned to (\w+)',
            r'(\w+) is responsible'
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                potential_owner = match.group(1)
                # Filter out common non-name words
                if potential_owner.lower() not in ['i', 'we', 'you', 'they', 'it', 'someone', 'everyone']:
                    owner = potential_owner.title()
                    break
        
        # Extract deadline
        deadline = None
        for pattern, pattern_type in self.TIME_PATTERNS:
            match = re.search(pattern, sentence_lower)
            if match:
                deadline = self._parse_deadline(match.group(0), pattern_type)
                break
        
        # Determine priority
        priority = "Medium"
        if any(w in sentence_lower for w in ['urgent', 'asap', 'immediately', 'critical']):
            priority = "High"
        elif any(w in sentence_lower for w in ['when possible', 'eventually', 'low priority']):
            priority = "Low"
        
        # Clean up task description
        task = sentence.strip()
        
        # Remove common prefixes
        for prefix in ['action item:', 'task:', 'todo:', 'to do:']:
            if task.lower().startswith(prefix):
                task = task[len(prefix):].strip()
        
        if len(task) < 10:
            return None
        
        return ActionItem(
            task=task,
            owner=owner,
            deadline=deadline,
            priority=priority,
            confidence=0.7
        )

    def _parse_deadline(self, deadline_str: str, pattern_type: str) -> str:
        """Parse deadline string into a formatted date."""
        today = datetime.now()
        
        if pattern_type == 'urgent':
            return "ASAP"
        
        if pattern_type == 'relative':
            if 'tomorrow' in deadline_str:
                return (today + timedelta(days=1)).strftime("%Y-%m-%d")
            elif 'next week' in deadline_str:
                return (today + timedelta(weeks=1)).strftime("%Y-%m-%d")
            elif 'next month' in deadline_str:
                return (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        if pattern_type == 'end_of':
            if 'week' in deadline_str:
                days_until_friday = (4 - today.weekday()) % 7
                return (today + timedelta(days=days_until_friday)).strftime("%Y-%m-%d")
            elif 'month' in deadline_str:
                next_month = today.replace(day=28) + timedelta(days=4)
                return next_month.replace(day=1) - timedelta(days=1)
        
        # Return original string if can't parse
        return deadline_str

    def _deduplicate_items(self, items: List[ActionItem]) -> List[ActionItem]:
        """Remove duplicate or very similar action items."""
        if not items:
            return items
        
        unique_items = []
        seen_tasks = set()
        
        for item in items:
            # Normalize task for comparison
            normalized = re.sub(r'\s+', ' ', item.task.lower().strip())
            
            # Check if similar task already exists
            is_duplicate = False
            for seen in seen_tasks:
                # Simple similarity check
                if normalized in seen or seen in normalized:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
                seen_tasks.add(normalized)
        
        return unique_items

    def format_action_items_table(self, result: ActionItemResult) -> str:
        """Format action items as a text table."""
        if not result.items:
            return "No action items identified."
        
        lines = [
            "ACTION ITEMS",
            "=" * 80,
            f"{'#':<3} {'Task':<40} {'Owner':<15} {'Deadline':<12} {'Priority':<8}",
            "-" * 80
        ]
        
        for item in result.items:
            task = item.task[:37] + "..." if len(item.task) > 40 else item.task
            owner = item.owner or "TBD"
            deadline = item.deadline or "TBD"
            
            lines.append(
                f"{item.id:<3} {task:<40} {owner:<15} {deadline:<12} {item.priority:<8}"
            )
        
        lines.append("-" * 80)
        lines.append(f"Total: {result.total_items} items | "
                    f"With owners: {result.items_with_owners} | "
                    f"With deadlines: {result.items_with_deadlines}")
        
        return '\n'.join(lines)
