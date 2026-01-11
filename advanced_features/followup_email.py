"""
Follow-up Email Generator Module
Generates professional follow-up emails based on meeting summaries.
"""

import asyncio
from typing import List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class FollowupEmail:
    """Generated follow-up email."""
    subject: str
    body_text: str
    body_html: str
    recipients_suggested: List[str]
    action_items_included: int


class FollowupEmailGenerator:
    """Generates professional follow-up emails from meeting summaries."""

    def __init__(self, config: dict, llm_pipeline=None):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("followup_email_enabled", True)
        self.company_name = adv_config.get("company_name", "")
        self.sender_name = adv_config.get("sender_name", "Sunny AI")
        
        self.llm = llm_pipeline

    async def generate(
        self,
        summary: Any,
        action_items: Any = None,
        meeting_date: datetime = None,
        meeting_title: str = "",
        attendees: List[str] = None
    ) -> FollowupEmail:
        """Generate a follow-up email from meeting summary."""
        if not self.enabled:
            return FollowupEmail(
                subject="",
                body_text="",
                body_html="",
                recipients_suggested=[],
                action_items_included=0
            )

        logger.info("Generating follow-up email")

        try:
            if self.llm:
                return await self._generate_with_llm(
                    summary, action_items, meeting_date, meeting_title, attendees
                )
            else:
                return self._generate_template(
                    summary, action_items, meeting_date, meeting_title, attendees
                )
        except Exception as e:
            logger.error(f"Follow-up email generation failed: {e}")
            return self._generate_template(
                summary, action_items, meeting_date, meeting_title, attendees
            )

    async def _generate_with_llm(
        self,
        summary: Any,
        action_items: Any,
        meeting_date: datetime,
        meeting_title: str,
        attendees: List[str]
    ) -> FollowupEmail:
        """Generate email using LLM."""
        # Prepare context
        exec_summary = summary.executive_summary if hasattr(summary, 'executive_summary') else ""
        key_points = summary.key_discussion_points if hasattr(summary, 'key_discussion_points') else []
        decisions = summary.decisions_made if hasattr(summary, 'decisions_made') else []
        
        items_list = []
        if action_items and hasattr(action_items, 'items'):
            items_list = action_items.items

        date_str = meeting_date.strftime("%B %d, %Y") if meeting_date else "today"
        
        prompt = f"""Write a professional follow-up email for a meeting.

Meeting Details:
- Title: {meeting_title or 'Team Meeting'}
- Date: {date_str}
- Attendees: {', '.join(attendees) if attendees else 'Team members'}

Executive Summary:
{exec_summary}

Key Discussion Points:
{chr(10).join(f'- {p}' for p in key_points[:5])}

Decisions Made:
{chr(10).join(f'- {d}' for d in decisions[:5]) if decisions else '- No formal decisions recorded'}

Action Items:
{chr(10).join(f'- {item.task} (Owner: {item.owner or "TBD"}, Due: {item.deadline or "TBD"})' for item in items_list[:10]) if items_list else '- No action items'}

Write a professional, concise follow-up email that:
1. Thanks attendees for their participation
2. Summarizes key outcomes
3. Lists action items with owners and deadlines
4. Ends with next steps

Format:
SUBJECT: [subject line]

BODY:
[email body]"""

        response = await self.llm._call_llm(prompt)
        
        # Parse response
        subject = "Meeting Follow-up"
        body = response
        
        if "SUBJECT:" in response:
            parts = response.split("BODY:", 1)
            subject_part = parts[0].replace("SUBJECT:", "").strip()
            subject = subject_part.split('\n')[0].strip()
            body = parts[1].strip() if len(parts) > 1 else response

        # Generate HTML version
        body_html = self._text_to_html(body)

        return FollowupEmail(
            subject=subject,
            body_text=body,
            body_html=body_html,
            recipients_suggested=attendees or [],
            action_items_included=len(items_list)
        )

    def _generate_template(
        self,
        summary: Any,
        action_items: Any,
        meeting_date: datetime,
        meeting_title: str,
        attendees: List[str]
    ) -> FollowupEmail:
        """Generate email using template."""
        date_str = meeting_date.strftime("%B %d, %Y") if meeting_date else datetime.now().strftime("%B %d, %Y")
        title = meeting_title or "Team Meeting"
        
        # Extract data
        exec_summary = summary.executive_summary if hasattr(summary, 'executive_summary') else "Meeting summary not available."
        key_points = summary.key_discussion_points if hasattr(summary, 'key_discussion_points') else []
        decisions = summary.decisions_made if hasattr(summary, 'decisions_made') else []
        
        items_list = []
        if action_items and hasattr(action_items, 'items'):
            items_list = action_items.items

        # Build email body
        body_lines = [
            f"Hi Team,",
            "",
            f"Thank you for attending the {title} on {date_str}. Below is a summary of our discussion and next steps.",
            "",
            "SUMMARY",
            "-" * 40,
            exec_summary,
            ""
        ]

        if key_points:
            body_lines.extend([
                "KEY DISCUSSION POINTS",
                "-" * 40
            ])
            for point in key_points[:5]:
                body_lines.append(f"• {point}")
            body_lines.append("")

        if decisions:
            body_lines.extend([
                "DECISIONS MADE",
                "-" * 40
            ])
            for decision in decisions[:5]:
                body_lines.append(f"✓ {decision}")
            body_lines.append("")

        if items_list:
            body_lines.extend([
                "ACTION ITEMS",
                "-" * 40
            ])
            for item in items_list[:10]:
                owner = item.owner or "TBD"
                deadline = item.deadline or "TBD"
                body_lines.append(f"• {item.task}")
                body_lines.append(f"  Owner: {owner} | Due: {deadline}")
            body_lines.append("")

        body_lines.extend([
            "Please review the action items assigned to you and reach out if you have any questions.",
            "",
            "Best regards,",
            self.sender_name,
            "",
            "---",
            "This email was automatically generated by Sunny AI Meeting Assistant."
        ])

        body_text = '\n'.join(body_lines)
        body_html = self._text_to_html(body_text)
        
        subject = f"Follow-up: {title} - {date_str}"

        return FollowupEmail(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            recipients_suggested=attendees or [],
            action_items_included=len(items_list)
        )

    def _text_to_html(self, text: str) -> str:
        """Convert plain text email to HTML."""
        # Escape HTML
        html = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert line breaks
        html = html.replace('\n', '<br>\n')
        
        # Style headers
        html = html.replace('SUMMARY<br>', '<h3 style="color: #2d3748; margin-top: 20px;">Summary</h3>')
        html = html.replace('KEY DISCUSSION POINTS<br>', '<h3 style="color: #2d3748; margin-top: 20px;">Key Discussion Points</h3>')
        html = html.replace('DECISIONS MADE<br>', '<h3 style="color: #2d3748; margin-top: 20px;">Decisions Made</h3>')
        html = html.replace('ACTION ITEMS<br>', '<h3 style="color: #2d3748; margin-top: 20px;">Action Items</h3>')
        
        # Remove separator lines
        html = html.replace('-' * 40 + '<br>', '')
        
        # Wrap in HTML template
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        h3 {{
            border-bottom: 2px solid #f59e0b;
            padding-bottom: 5px;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>
"""
        return html_template
