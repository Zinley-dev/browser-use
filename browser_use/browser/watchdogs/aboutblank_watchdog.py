"""About:blank watchdog for managing about:blank tabs with bouncing text animation."""

from typing import TYPE_CHECKING, ClassVar

from bubus import BaseEvent
from cdp_use.cdp.target import TargetID
from pydantic import PrivateAttr

from browser_use.browser.events import (
	AboutBlankAnimationShownEvent,
	BrowserStopEvent,
	BrowserStoppedEvent,
	CloseTabEvent,
	NavigateToUrlEvent,
	TabClosedEvent,
	TabCreatedEvent,
)
from browser_use.browser.watchdog_base import BaseWatchdog

if TYPE_CHECKING:
	pass


class AboutBlankWatchdog(BaseWatchdog):
	"""Ensures there's always exactly one about:blank tab with bouncing text animation."""

	# Event contracts
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		BrowserStopEvent,
		BrowserStoppedEvent,
		TabCreatedEvent,
		TabClosedEvent,
	]
	EMITS: ClassVar[list[type[BaseEvent]]] = [
		NavigateToUrlEvent,
		CloseTabEvent,
		AboutBlankAnimationShownEvent,
	]

	_stopping: bool = PrivateAttr(default=False)

	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		"""Handle browser stop request - stop creating new tabs."""
		# logger.info('[AboutBlankWatchdog] Browser stop requested, stopping tab creation')
		self._stopping = True

	async def on_BrowserStoppedEvent(self, event: BrowserStoppedEvent) -> None:
		"""Handle browser stopped event."""
		# logger.info('[AboutBlankWatchdog] Browser stopped')
		self._stopping = True

	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		"""Check tabs when a new tab is created."""
		# logger.debug(f'[AboutBlankWatchdog] ➕ New tab created: {event.url}')

		# If an about:blank tab was created, show text animation on all about:blank tabs
		if event.url == 'about:blank':
			await self._show_text_animation_on_about_blank_tabs()

	async def on_TabClosedEvent(self, event: TabClosedEvent) -> None:
		"""Check tabs when a tab is closed and proactively create about:blank if needed."""
		# logger.debug('[AboutBlankWatchdog] Tab closing, checking if we need to create about:blank tab')

		# Don't create new tabs if browser is shutting down
		if self._stopping:
			# logger.debug('[AboutBlankWatchdog] Browser is stopping, not creating new tabs')
			return

		# Check if we're about to close the last tab (event happens BEFORE tab closes)
		# Use _cdp_get_all_pages for quick check without fetching titles
		page_targets = await self.browser_session._cdp_get_all_pages()
		if len(page_targets) <= 1:
			self.logger.debug(
				'[AboutBlankWatchdog] Last tab closing, creating new about:blank tab to avoid closing entire browser'
			)
			# Create the animation tab since no tabs should remain
			navigate_event = self.event_bus.dispatch(NavigateToUrlEvent(url='about:blank', new_tab=True))
			await navigate_event
			# Show text animation on the new tab
			await self._show_text_animation_on_about_blank_tabs()
		else:
			# Multiple tabs exist, check after close
			await self._check_and_ensure_about_blank_tab()

	async def attach_to_target(self, target_id: TargetID) -> None:
		"""AboutBlankWatchdog doesn't monitor individual targets."""
		pass

	async def _check_and_ensure_about_blank_tab(self) -> None:
		"""Check current tabs and ensure exactly one about:blank tab with animation exists."""
		try:
			# For quick checks, just get page targets without titles to reduce noise
			page_targets = await self.browser_session._cdp_get_all_pages()

			# If no tabs exist at all, create one to keep browser alive
			if len(page_targets) == 0:
				# Only create a new tab if there are no tabs at all
				self.logger.debug('[AboutBlankWatchdog] No tabs exist, creating new about:blank text animation tab')
				navigate_event = self.event_bus.dispatch(NavigateToUrlEvent(url='about:blank', new_tab=True))
				await navigate_event
				# Show text animation on the new tab
				await self._show_text_animation_on_about_blank_tabs()
			# Otherwise there are tabs, don't create new ones to avoid interfering

		except Exception as e:
			self.logger.error(f'[AboutBlankWatchdog] Error ensuring about:blank tab: {e}')

	async def _show_text_animation_on_about_blank_tabs(self) -> None:
		"""Show text animation on all about:blank pages only."""
		try:
			# Get just the page targets without expensive title fetching
			page_targets = await self.browser_session._cdp_get_all_pages()
			browser_session_label = str(self.browser_session.id)[-4:]

			for page_target in page_targets:
				target_id = page_target['targetId']
				url = page_target['url']

				# Only target about:blank pages specifically
				if url == 'about:blank':
					await self._show_text_animation_cdp(target_id, browser_session_label)

		except Exception as e:
			self.logger.error(f'[AboutBlankWatchdog] Error showing text animation: {e}')

	async def _show_text_animation_cdp(self, target_id: TargetID, browser_session_label: str) -> None:
		"""
		Injects a bouncing text animation overlay into the target using CDP.
		This is used to visually indicate that the browser is setting up or waiting.
		"""
		try:
			# Create temporary session for this target without switching focus
			temp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)

			# Inject the text animation script
			script = f"""
				(function(browser_session_label) {{
					// Idempotency check
					if (window.__bounceAnimationRunning) {{
						return; // Already running, don't add another
					}}
					window.__bounceAnimationRunning = true;

					// Ensure document.body exists before proceeding
					if (!document.body) {{
						// Try again after DOM is ready
						window.__bounceAnimationRunning = false; // Reset flag to retry
						if (document.readyState === 'loading') {{
							document.addEventListener('DOMContentLoaded', () => arguments.callee(browser_session_label));
						}}
						return;
					}}

					const animated_title = `Orion is waking up...`;
					if (document.title === animated_title) {{
						return;      // already run on this tab, dont run again
					}}
					document.title = animated_title;

					// Create clean minimal overlay
					const loadingOverlay = document.createElement('div');
					loadingOverlay.id = 'pretty-loading-animation';
					loadingOverlay.style.position = 'fixed';
					loadingOverlay.style.top = '0';
					loadingOverlay.style.left = '0';
					loadingOverlay.style.width = '100vw';
					loadingOverlay.style.height = '100vh';
					loadingOverlay.style.background = '#000000';
					loadingOverlay.style.zIndex = '99999';
					loadingOverlay.style.overflow = 'hidden';
					loadingOverlay.style.display = 'flex';
					loadingOverlay.style.alignItems = 'center';
					loadingOverlay.style.justifyContent = 'center';

					// Create minimal glass container
					const glassContainer = document.createElement('div');
					glassContainer.style.padding = '32px 64px';
					glassContainer.style.background = 'rgba(255, 255, 255, 0.04)';
					glassContainer.style.backdropFilter = 'blur(20px)';
					glassContainer.style.webkitBackdropFilter = 'blur(20px)';
					glassContainer.style.borderRadius = '20px';
					glassContainer.style.border = '0.5px solid rgba(255, 255, 255, 0.08)';
					glassContainer.style.boxShadow = '0 4px 24px rgba(0, 0, 0, 0.2)';

					// Create the text element
					const textElement = document.createElement('div');
					textElement.textContent = 'Orion';
					textElement.style.fontSize = '48px';
					textElement.style.fontWeight = '600';
					textElement.style.fontFamily = '-apple-system, BlinkMacSystemFont, "SF Pro Display", system-ui, sans-serif';
					textElement.style.color = '#ffffff';
					textElement.style.letterSpacing = '-0.02em';
					textElement.style.userSelect = 'none';
					textElement.style.pointerEvents = 'none';
					textElement.style.opacity = '0.92';

					glassContainer.appendChild(textElement);
					loadingOverlay.appendChild(glassContainer);
					document.body.appendChild(loadingOverlay);

					// Subtle breathing animation
					let opacity = 0.92;
					let increasing = false;
					function breathe() {{
						if (increasing) {{
							opacity += 0.002;
							if (opacity >= 1) increasing = false;
						}} else {{
							opacity -= 0.002;
							if (opacity <= 0.7) increasing = true;
						}}
						textElement.style.opacity = opacity.toFixed(3);
						requestAnimationFrame(breathe);
					}}
					breathe();

					// Minimal CSS for smoothness
					const style = document.createElement('style');
					style.textContent = `
						@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {{
							#pretty-loading-animation {{
								-webkit-font-smoothing: antialiased;
								-moz-osx-font-smoothing: grayscale;
							}}
						}}
					`;
					document.head.appendChild(style);
				}})('{browser_session_label}');
			"""

			await temp_session.cdp_client.send.Runtime.evaluate(params={'expression': script}, session_id=temp_session.session_id)

			# No need to detach - session is cached

			# Dispatch event
			self.event_bus.dispatch(AboutBlankAnimationShownEvent(target_id=target_id))

		except Exception as e:
			self.logger.error(f'[AboutBlankWatchdog] Error injecting text animation: {e}')