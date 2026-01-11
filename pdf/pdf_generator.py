"""
PDF Generator Module
Creates professional meeting summary reports.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import structlog

from summarization.llm_pipeline import MeetingSummary

logger = structlog.get_logger(__name__)


class PDFGenerator:
    """Generates professional PDF meeting reports."""

    def __init__(self, config: dict):
        pdf_config = config.get("pdf", {})
        self.font_family = pdf_config.get("font_family", "Helvetica")
        self.title_font_size = pdf_config.get("title_font_size", 18)
        self.heading_font_size = pdf_config.get("heading_font_size", 14)
        self.body_font_size = pdf_config.get("body_font_size", 11)
        self.margin = pdf_config.get("margin", 50)
        
        self.output_dir = Path(config.get("general", {}).get("output_dir", "./outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_styles()

    def _setup_styles(self):
        """Setup PDF styles."""
        self.styles = getSampleStyleSheet()
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontName=f'{self.font_family}-Bold',
            fontSize=self.title_font_size,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a365d')
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontName=self.font_family,
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#4a5568')
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontName=f'{self.font_family}-Bold',
            fontSize=self.heading_font_size,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2d3748'),
            borderPadding=(0, 0, 5, 0)
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontName=self.font_family,
            fontSize=self.body_font_size,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontName=self.font_family,
            fontSize=self.body_font_size,
            leftIndent=20,
            spaceAfter=6,
            bulletIndent=10
        ))

    def generate_report(
        self,
        summary: MeetingSummary,
        platform: str,
        duration: str,
        meeting_date: Optional[datetime] = None,
        output_filename: Optional[str] = None,
        diarization: Optional[Any] = None,
        topics: Optional[Any] = None,
        sentiment: Optional[Any] = None,
        action_items: Optional[Any] = None,
        analytics: Optional[Any] = None
    ) -> Path:
        """Generate a PDF report from meeting summary with advanced features."""
        
        if meeting_date is None:
            meeting_date = datetime.now()
        
        if output_filename is None:
            timestamp = meeting_date.strftime("%Y%m%d_%H%M%S")
            output_filename = f"meeting_summary_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        logger.info(f"Generating PDF report: {output_path}")
        
        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build content
        story = []
        
        # Header
        story.extend(self._build_header(meeting_date, platform, duration))
        
        # Analytics Summary (if available)
        if analytics:
            story.extend(self._build_analytics_summary(analytics))
        
        # Executive Summary
        story.extend(self._build_executive_summary(summary.executive_summary))
        
        # Speaker Analysis (if diarization available)
        if diarization and diarization.num_speakers > 0:
            story.extend(self._build_speaker_analysis(diarization))
        
        # Topic Timeline (if topics available)
        if topics and topics.total_topics > 0:
            story.extend(self._build_topic_timeline(topics))
        
        # Sentiment Analysis (if available)
        if sentiment:
            story.extend(self._build_sentiment_section(sentiment))
        
        # Key Discussion Points
        story.extend(self._build_key_points(summary.key_discussion_points))
        
        # Decisions Made
        story.extend(self._build_decisions(summary.decisions_made))
        
        # Action Items (enhanced)
        if action_items and action_items.total_items > 0:
            story.extend(self._build_action_items_enhanced(action_items))
        else:
            story.extend(self._build_action_items(summary.action_items))
        
        # Footer
        story.extend(self._build_footer(summary.confidence_score))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF report generated successfully: {output_path}")
        return output_path

    def _build_header(self, meeting_date: datetime, platform: str, duration: str) -> list:
        """Build report header."""
        elements = []
        
        # Title
        elements.append(Paragraph("MEETING SUMMARY REPORT", self.styles['ReportTitle']))
        
        # Subtitle
        elements.append(Paragraph(
            "Generated by Sunny AI – Autonomous Meeting Assistant",
            self.styles['ReportSubtitle']
        ))
        
        # Horizontal line
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=20
        ))
        
        # Meeting details table
        details_data = [
            ['Date:', meeting_date.strftime("%B %d, %Y at %I:%M %p")],
            ['Platform:', platform.replace('_', ' ').title()],
            ['Duration:', duration],
        ]
        
        details_table = Table(details_data, colWidths=[1.5*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), f'{self.font_family}-Bold'),
            ('FONTNAME', (1, 0), (1, -1), self.font_family),
            ('FONTSIZE', (0, 0), (-1, -1), self.body_font_size),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3748')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_executive_summary(self, summary: str) -> list:
        """Build executive summary section."""
        elements = []
        
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        if summary:
            elements.append(Paragraph(summary, self.styles['ReportBody']))
        else:
            elements.append(Paragraph(
                "<i>No executive summary available.</i>",
                self.styles['ReportBody']
            ))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_key_points(self, points: list) -> list:
        """Build key discussion points section."""
        elements = []
        
        elements.append(Paragraph("KEY DISCUSSION POINTS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        if points:
            for point in points:
                bullet_text = f"• {point}"
                elements.append(Paragraph(bullet_text, self.styles['BulletPoint']))
        else:
            elements.append(Paragraph(
                "<i>No key discussion points identified.</i>",
                self.styles['ReportBody']
            ))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_decisions(self, decisions: list) -> list:
        """Build decisions made section."""
        elements = []
        
        elements.append(Paragraph("DECISIONS MADE", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        if decisions:
            for decision in decisions:
                bullet_text = f"✓ {decision}"
                elements.append(Paragraph(bullet_text, self.styles['BulletPoint']))
        else:
            elements.append(Paragraph(
                "<i>No explicit decisions recorded during this meeting.</i>",
                self.styles['ReportBody']
            ))
        
        elements.append(Spacer(1, 15))
        return elements


    def _build_action_items(self, action_items: list) -> list:
        """Build action items section."""
        elements = []
        
        elements.append(Paragraph("ACTION ITEMS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        if action_items:
            # Create table for action items
            table_data = [['Task', 'Owner', 'Deadline']]
            
            for item in action_items:
                table_data.append([
                    item.task,
                    item.owner or 'TBD',
                    item.deadline or 'TBD'
                ])
            
            # Calculate column widths
            col_widths = [4*inch, 1.5*inch, 1.5*inch]
            
            action_table = Table(table_data, colWidths=col_widths)
            action_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), f'{self.font_family}-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), self.font_family),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(action_table)
        else:
            elements.append(Paragraph(
                "<i>No action items identified during this meeting.</i>",
                self.styles['ReportBody']
            ))
        
        elements.append(Spacer(1, 20))
        return elements

    def _build_footer(self, confidence_score: float) -> list:
        """Build report footer."""
        elements = []
        
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor('#e2e8f0'),
            spaceBefore=20,
            spaceAfter=15
        ))
        
        # Confidence indicator
        confidence_text = f"Summary Confidence Score: {confidence_score:.0%}"
        confidence_color = colors.HexColor('#38a169') if confidence_score >= 0.7 else \
                          colors.HexColor('#d69e2e') if confidence_score >= 0.4 else \
                          colors.HexColor('#e53e3e')
        
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontName=self.font_family,
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#718096')
        )
        
        elements.append(Paragraph(confidence_text, footer_style))
        elements.append(Spacer(1, 10))
        
        # Disclaimer
        disclaimer = """
        <i>This summary was automatically generated by Sunny AI. 
        Please verify important details against the original meeting recording.
        Sunny AI identifies itself as an AI assistant and requires recording consent from all participants.</i>
        """
        elements.append(Paragraph(disclaimer, footer_style))
        
        # Generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Report generated: {timestamp}", footer_style))
        
        return elements

    def _build_analytics_summary(self, analytics) -> list:
        """Build analytics summary section."""
        elements = []
        
        elements.append(Paragraph("MEETING ANALYTICS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        # Create analytics table
        analytics_data = [
            ['Metric', 'Value'],
            ['Speakers', str(analytics.num_speakers)],
            ['Topics Discussed', str(analytics.num_topics)],
            ['Action Items', str(analytics.num_action_items)],
            ['Decisions Made', str(analytics.num_decisions)],
            ['Total Words', f"{analytics.total_words:,}"],
            ['Words/Minute', f"{analytics.words_per_minute:.1f}"],
            ['Overall Sentiment', analytics.overall_sentiment.title()],
            ['Participation Balance', f"{analytics.participation_balance:.0%}"]
        ]
        
        analytics_table = Table(analytics_data, colWidths=[2.5*inch, 2*inch])
        analytics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), f'{self.font_family}-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbeb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(analytics_table)
        elements.append(Spacer(1, 15))
        
        return elements

    def _build_speaker_analysis(self, diarization) -> list:
        """Build speaker analysis section."""
        elements = []
        
        elements.append(Paragraph("SPEAKER ANALYSIS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        elements.append(Paragraph(
            f"<b>{diarization.num_speakers}</b> speakers identified in this meeting.",
            self.styles['ReportBody']
        ))
        
        if diarization.speaker_stats:
            # Create speaker stats table
            speaker_data = [['Speaker', 'Speaking Time', 'Percentage']]
            
            for speaker, time_seconds in diarization.speaker_stats.items():
                minutes = int(time_seconds // 60)
                seconds = int(time_seconds % 60)
                time_str = f"{minutes}m {seconds}s"
                
                # Calculate percentage (approximate)
                total_time = sum(diarization.speaker_stats.values())
                pct = (time_seconds / total_time * 100) if total_time > 0 else 0
                
                speaker_data.append([speaker, time_str, f"{pct:.1f}%"])
            
            speaker_table = Table(speaker_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            speaker_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3182ce')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), f'{self.font_family}-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(speaker_table)
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_topic_timeline(self, topics) -> list:
        """Build topic timeline section."""
        elements = []
        
        elements.append(Paragraph("TOPIC TIMELINE", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        for i, topic in enumerate(topics.topics, 1):
            # Format timestamps
            start_min = int(topic.start_time // 60)
            start_sec = int(topic.start_time % 60)
            end_min = int(topic.end_time // 60)
            end_sec = int(topic.end_time % 60)
            
            time_range = f"{start_min:02d}:{start_sec:02d} – {end_min:02d}:{end_sec:02d}"
            
            topic_text = f"<b>{i}. {topic.title}</b> <font color='#718096'>({time_range})</font>"
            elements.append(Paragraph(topic_text, self.styles['BulletPoint']))
            
            if topic.summary:
                elements.append(Paragraph(
                    f"<font color='#4a5568'>{topic.summary}</font>",
                    ParagraphStyle(
                        name='TopicSummary',
                        parent=self.styles['Normal'],
                        fontSize=9,
                        leftIndent=30,
                        spaceAfter=8
                    )
                ))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_sentiment_section(self, sentiment) -> list:
        """Build sentiment analysis section."""
        elements = []
        
        elements.append(Paragraph("SENTIMENT ANALYSIS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        # Overall sentiment with color coding
        sentiment_colors = {
            'positive': '#38a169',
            'neutral': '#718096',
            'negative': '#e53e3e'
        }
        sent_value = sentiment.overall_sentiment.value if hasattr(sentiment.overall_sentiment, 'value') else str(sentiment.overall_sentiment)
        sent_color = sentiment_colors.get(sent_value, '#718096')
        
        elements.append(Paragraph(
            f"Overall Tone: <font color='{sent_color}'><b>{sent_value.upper()}</b></font> "
            f"(Confidence: {sentiment.overall_confidence:.0%})",
            self.styles['ReportBody']
        ))
        
        # Sentiment distribution
        if sentiment.sentiment_distribution:
            dist_text = " | ".join([
                f"{k.title()}: {v:.1f}%" 
                for k, v in sentiment.sentiment_distribution.items()
            ])
            elements.append(Paragraph(f"Distribution: {dist_text}", self.styles['BulletPoint']))
        
        # Conflict/Agreement indicators
        if sentiment.conflict_detected:
            elements.append(Paragraph(
                "⚠️ <font color='#e53e3e'>Potential conflict detected in discussion</font>",
                self.styles['BulletPoint']
            ))
        
        elements.append(Paragraph(
            f"Agreement Level: {sentiment.agreement_level:.0%}",
            self.styles['BulletPoint']
        ))
        
        # Key emotional moments
        if sentiment.key_emotional_moments:
            elements.append(Spacer(1, 5))
            elements.append(Paragraph("<b>Key Moments:</b>", self.styles['BulletPoint']))
            for moment in sentiment.key_emotional_moments[:3]:
                elements.append(Paragraph(
                    f"• <i>{moment[:100]}...</i>" if len(moment) > 100 else f"• <i>{moment}</i>",
                    ParagraphStyle(
                        name='Moment',
                        parent=self.styles['Normal'],
                        fontSize=9,
                        leftIndent=40,
                        textColor=colors.HexColor('#4a5568')
                    )
                ))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_action_items_enhanced(self, action_items) -> list:
        """Build enhanced action items section with priorities."""
        elements = []
        
        elements.append(Paragraph("ACTION ITEMS", self.styles['SectionHeading']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        # Summary stats
        elements.append(Paragraph(
            f"<b>{action_items.total_items}</b> action items identified | "
            f"<b>{action_items.items_with_owners}</b> with owners | "
            f"<b>{action_items.items_with_deadlines}</b> with deadlines",
            self.styles['ReportBody']
        ))
        elements.append(Spacer(1, 10))
        
        if action_items.items:
            # Create enhanced table
            table_data = [['#', 'Task', 'Owner', 'Deadline', 'Priority']]
            
            priority_colors = {
                'High': colors.HexColor('#e53e3e'),
                'Medium': colors.HexColor('#d69e2e'),
                'Low': colors.HexColor('#38a169')
            }
            
            for item in action_items.items:
                table_data.append([
                    str(item.id),
                    item.task[:50] + "..." if len(item.task) > 50 else item.task,
                    item.owner or 'TBD',
                    item.deadline or 'TBD',
                    item.priority
                ])
            
            col_widths = [0.4*inch, 3.2*inch, 1*inch, 1*inch, 0.8*inch]
            
            action_table = Table(table_data, colWidths=col_widths)
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), f'{self.font_family}-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(action_table)
        else:
            elements.append(Paragraph(
                "<i>No action items identified during this meeting.</i>",
                self.styles['ReportBody']
            ))
        
        elements.append(Spacer(1, 20))
        return elements
