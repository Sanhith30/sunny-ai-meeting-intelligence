"""
Meeting Joiner Module
Handles automatic joining of Zoom and Google Meet meetings.
"""

import asyncio
import re
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import structlog

logger = structlog.get_logger(__name__)


class MeetingPlatform(Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    UNKNOWN = "unknown"


@dataclass
class MeetingInfo:
    platform: MeetingPlatform
    meeting_id: str
    url: str
    password: Optional[str] = None


class MeetingJoiner:
    """Autonomous meeting joiner for Zoom and Google Meet."""

    def __init__(self, config: dict):
        self.config = config
        self.bot_name = config.get("general", {}).get("bot_name", "Sunny AI – Assistant")
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_in_meeting = False
        self._meeting_end_callback: Optional[Callable] = None
        self._playwright = None

    def detect_platform(self, url: str) -> MeetingPlatform:
        """Detect meeting platform from URL."""
        url_lower = url.lower()
        
        if "zoom.us" in url_lower or "zoom.com" in url_lower:
            return MeetingPlatform.ZOOM
        elif "meet.google.com" in url_lower:
            return MeetingPlatform.GOOGLE_MEET
        else:
            return MeetingPlatform.UNKNOWN

    def parse_meeting_url(self, url: str) -> MeetingInfo:
        """Parse meeting URL and extract relevant information."""
        platform = self.detect_platform(url)
        meeting_id = ""
        password = None

        if platform == MeetingPlatform.ZOOM:
            # Extract Zoom meeting ID
            match = re.search(r'/j/(\d+)', url)
            if match:
                meeting_id = match.group(1)
            # Extract password if present
            pwd_match = re.search(r'pwd=([^&]+)', url)
            if pwd_match:
                password = pwd_match.group(1)

        elif platform == MeetingPlatform.GOOGLE_MEET:
            # Extract Google Meet code
            match = re.search(r'meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})', url)
            if match:
                meeting_id = match.group(1)

        return MeetingInfo(
            platform=platform,
            meeting_id=meeting_id,
            url=url,
            password=password
        )

    async def initialize_browser(self) -> None:
        """Initialize Playwright browser."""
        browser_config = self.config.get("browser", {})
        
        self._playwright = await async_playwright().start()
        
        self.browser = await self._playwright.chromium.launch(
            headless=browser_config.get("headless", False),
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--autoplay-policy=no-user-gesture-required",
            ]
        )
        
        self.context = await self.browser.new_context(
            permissions=["microphone", "camera"],
            user_agent=browser_config.get("user_agent"),
            viewport={"width": 1280, "height": 720}
        )
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")

    async def join_meeting(self, url: str) -> bool:
        """Join a meeting from the given URL."""
        meeting_info = self.parse_meeting_url(url)
        logger.info(f"Joining {meeting_info.platform.value} meeting", meeting_id=meeting_info.meeting_id)

        if not self.browser:
            await self.initialize_browser()

        try:
            if meeting_info.platform == MeetingPlatform.GOOGLE_MEET:
                return await self._join_google_meet(meeting_info)
            elif meeting_info.platform == MeetingPlatform.ZOOM:
                return await self._join_zoom(meeting_info)
            else:
                logger.error("Unsupported meeting platform")
                return False
        except Exception as e:
            logger.error(f"Failed to join meeting: {e}")
            return False


    async def _join_google_meet(self, meeting_info: MeetingInfo) -> bool:
        """Join a Google Meet meeting."""
        try:
            await self.page.goto(meeting_info.url, wait_until="networkidle")
            await asyncio.sleep(2)

            # Handle "Got it" or cookie consent buttons
            try:
                got_it_btn = await self.page.query_selector('button:has-text("Got it")')
                if got_it_btn:
                    await got_it_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Enter name
            try:
                name_input = await self.page.wait_for_selector(
                    'input[placeholder="Your name"], input[aria-label="Your name"]',
                    timeout=10000
                )
                if name_input:
                    await name_input.fill(self.bot_name)
                    logger.info(f"Entered name: {self.bot_name}")
            except Exception as e:
                logger.warning(f"Could not find name input: {e}")

            # Turn off camera
            try:
                camera_btn = await self.page.query_selector(
                    '[aria-label*="camera"], [data-is-muted="false"][aria-label*="video"]'
                )
                if camera_btn:
                    await camera_btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("Camera turned off")
            except Exception:
                pass

            # Turn off microphone
            try:
                mic_btn = await self.page.query_selector(
                    '[aria-label*="microphone"], [data-is-muted="false"][aria-label*="mic"]'
                )
                if mic_btn:
                    await mic_btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("Microphone muted")
            except Exception:
                pass

            # Click "Ask to join" or "Join now" button
            join_selectors = [
                'button:has-text("Ask to join")',
                'button:has-text("Join now")',
                'button:has-text("Join")',
                '[data-idom-class*="join"]'
            ]

            for selector in join_selectors:
                try:
                    join_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if join_btn:
                        await join_btn.click()
                        logger.info("Clicked join button")
                        break
                except Exception:
                    continue

            # Wait for meeting to load
            await asyncio.sleep(5)

            # Check if we're in the meeting
            self.is_in_meeting = await self._verify_in_meeting()
            
            if self.is_in_meeting:
                logger.info("Successfully joined Google Meet")
                return True
            else:
                # Might be in waiting room
                logger.info("Waiting for host to admit...")
                return await self._wait_for_admission()

        except Exception as e:
            logger.error(f"Failed to join Google Meet: {e}")
            return False

    async def _join_zoom(self, meeting_info: MeetingInfo) -> bool:
        """Join a Zoom meeting via web client."""
        try:
            # Use Zoom web client
            web_url = meeting_info.url
            if "/j/" in web_url:
                web_url = web_url.replace("/j/", "/wc/join/")
            
            await self.page.goto(web_url, wait_until="networkidle")
            await asyncio.sleep(3)

            # Click "Join from Your Browser" if available
            try:
                browser_join = await self.page.wait_for_selector(
                    'a:has-text("Join from Your Browser"), a:has-text("join from your browser")',
                    timeout=10000
                )
                if browser_join:
                    await browser_join.click()
                    await asyncio.sleep(3)
            except Exception:
                pass

            # Enter name
            try:
                name_input = await self.page.wait_for_selector(
                    '#inputname, input[placeholder*="name"], input[id*="name"]',
                    timeout=10000
                )
                if name_input:
                    await name_input.fill(self.bot_name)
                    logger.info(f"Entered name: {self.bot_name}")
            except Exception as e:
                logger.warning(f"Could not find name input: {e}")

            # Enter password if required
            if meeting_info.password:
                try:
                    pwd_input = await self.page.query_selector(
                        '#inputpasscode, input[type="password"], input[placeholder*="password"]'
                    )
                    if pwd_input:
                        await pwd_input.fill(meeting_info.password)
                        logger.info("Entered meeting password")
                except Exception:
                    pass

            # Click join button
            join_selectors = [
                'button:has-text("Join")',
                '#joinBtn',
                'button[type="submit"]'
            ]

            for selector in join_selectors:
                try:
                    join_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if join_btn:
                        await join_btn.click()
                        logger.info("Clicked join button")
                        break
                except Exception:
                    continue

            await asyncio.sleep(5)

            # Handle audio/video permissions
            await self._handle_zoom_av_settings()

            # Verify we're in the meeting
            self.is_in_meeting = await self._verify_in_meeting()
            
            if self.is_in_meeting:
                logger.info("Successfully joined Zoom meeting")
                return True
            else:
                logger.info("Waiting for host to admit...")
                return await self._wait_for_admission()

        except Exception as e:
            logger.error(f"Failed to join Zoom: {e}")
            return False

    async def _handle_zoom_av_settings(self) -> None:
        """Handle Zoom audio/video settings popup."""
        try:
            # Join with computer audio
            audio_btn = await self.page.query_selector(
                'button:has-text("Join Audio by Computer"), button:has-text("Join with Computer Audio")'
            )
            if audio_btn:
                await audio_btn.click()
                await asyncio.sleep(1)

            # Mute microphone
            mute_btn = await self.page.query_selector(
                '[aria-label*="mute"], button:has-text("Mute")'
            )
            if mute_btn:
                await mute_btn.click()

            # Stop video
            video_btn = await self.page.query_selector(
                '[aria-label*="stop video"], button:has-text("Stop Video")'
            )
            if video_btn:
                await video_btn.click()

        except Exception as e:
            logger.warning(f"Error handling AV settings: {e}")

    async def _verify_in_meeting(self) -> bool:
        """Verify that we're actually in the meeting."""
        try:
            # Google Meet indicators
            meet_indicators = [
                '[data-meeting-title]',
                '[data-self-name]',
                '.google-material-icons:has-text("call_end")'
            ]
            
            # Zoom indicators
            zoom_indicators = [
                '#wc-container-left',
                '.meeting-client',
                '[aria-label="Leave meeting"]'
            ]

            all_indicators = meet_indicators + zoom_indicators
            
            for indicator in all_indicators:
                try:
                    element = await self.page.query_selector(indicator)
                    if element:
                        return True
                except Exception:
                    continue

            return False
            
        except Exception:
            return False

    async def _wait_for_admission(self) -> bool:
        """Wait for host to admit from waiting room."""
        timeout = self.config.get("meeting", {}).get("waiting_room_timeout_seconds", 300)
        check_interval = 5
        elapsed = 0

        while elapsed < timeout:
            await asyncio.sleep(check_interval)
            elapsed += check_interval

            if await self._verify_in_meeting():
                logger.info("Admitted to meeting")
                self.is_in_meeting = True
                return True

            # Check if denied
            page_content = await self.page.content()
            if "denied" in page_content.lower() or "removed" in page_content.lower():
                logger.warning("Entry was denied")
                return False

        logger.warning("Waiting room timeout exceeded")
        return False

    async def leave_meeting(self) -> None:
        """Leave the current meeting and close browser."""
        logger.info("Leaving meeting")
        
        if self.page:
            try:
                # Try to click leave button
                leave_selectors = [
                    '[aria-label="Leave call"]',
                    'button:has-text("Leave")',
                    '[aria-label="Leave meeting"]',
                    '.google-material-icons:has-text("call_end")'
                ]
                
                for selector in leave_selectors:
                    try:
                        leave_btn = await self.page.query_selector(selector)
                        if leave_btn:
                            await leave_btn.click()
                            await asyncio.sleep(1)
                            break
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.warning(f"Error clicking leave button: {e}")

        # Close browser
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

        self.is_in_meeting = False
        logger.info("Left meeting and closed browser")
