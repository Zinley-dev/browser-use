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

					// Create the main overlay with subtle gradient
					const loadingOverlay = document.createElement('div');
					loadingOverlay.id = 'pretty-loading-animation';
					loadingOverlay.style.position = 'fixed';
					loadingOverlay.style.top = '0';
					loadingOverlay.style.left = '0';
					loadingOverlay.style.width = '100vw';
					loadingOverlay.style.height = '100vh';
					loadingOverlay.style.background = 'radial-gradient(ellipse at center, #1a1a1a 0%, #0a0a0a 100%)';
					loadingOverlay.style.zIndex = '99999';
					loadingOverlay.style.overflow = 'hidden';

					// Create glass container for the text
					const glassContainer = document.createElement('div');
					glassContainer.style.position = 'absolute';
					glassContainer.style.padding = '40px 60px';
					glassContainer.style.background = 'rgba(255, 255, 255, 0.03)';
					glassContainer.style.backdropFilter = 'blur(40px) saturate(180%)';
					glassContainer.style.webkitBackdropFilter = 'blur(40px) saturate(180%)';
					glassContainer.style.borderRadius = '30px';
					glassContainer.style.border = '1px solid rgba(255, 255, 255, 0.1)';
					glassContainer.style.boxShadow = '0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)';
					glassContainer.style.left = '0px';
					glassContainer.style.top = '0px';

					// Create the text element
					const textElement = document.createElement('div');
					textElement.textContent = 'ORION';
					textElement.style.fontSize = '64px';
					textElement.style.fontWeight = '700';
					textElement.style.fontFamily = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif';
					textElement.style.background = 'linear-gradient(135deg, #a8c0ff 0%, #c3cfe2 25%, #ffffff 50%, #a8c0ff 75%, #c3cfe2 100%)';
					textElement.style.backgroundSize = '300% 300%';
					textElement.style.backgroundClip = 'text';
					textElement.style.webkitBackgroundClip = 'text';
					textElement.style.color = 'transparent';
					textElement.style.letterSpacing = '0.05em';
					textElement.style.userSelect = 'none';
					textElement.style.pointerEvents = 'none';
					textElement.style.whiteSpace = 'nowrap';
					textElement.style.filter = 'drop-shadow(0 0 20px rgba(168, 192, 255, 0.3))';

					glassContainer.appendChild(textElement);
					loadingOverlay.appendChild(glassContainer);
					document.body.appendChild(loadingOverlay);

					// Gradient animation
					let gradientPos = 0;
					function animateGradient() {{
						gradientPos = (gradientPos + 1) % 300;
						textElement.style.backgroundPosition = `${{gradientPos}}% 50%`;
					}}
					setInterval(animateGradient, 30);

					// Smooth bounce animation logic
					let x = Math.random() * (window.innerWidth - 500);
					let y = Math.random() * (window.innerHeight - 250);
					let dx = 1.2 + Math.random() * 0.3; // Slower, smoother movement
					let dy = 1.2 + Math.random() * 0.3;
					// Randomize direction
					if (Math.random() > 0.5) dx = -dx;
					if (Math.random() > 0.5) dy = -dy;

					function animate() {{
						const containerWidth = glassContainer.offsetWidth || 500;
						const containerHeight = glassContainer.offsetHeight || 250;
						x += dx;
						y += dy;

						if (x <= 0) {{
							x = 0;
							dx = Math.abs(dx);
						}} else if (x + containerWidth >= window.innerWidth) {{
							x = window.innerWidth - containerWidth;
							dx = -Math.abs(dx);
						}}
						if (y <= 0) {{
							y = 0;
							dy = Math.abs(dy);
						}} else if (y + containerHeight >= window.innerHeight) {{
							y = window.innerHeight - containerHeight;
							dy = -Math.abs(dy);
						}}

						glassContainer.style.left = `${{x}}px`;
						glassContainer.style.top = `${{y}}px`;
						glassContainer.style.transform = 'translateZ(0)'; // Hardware acceleration

						requestAnimationFrame(animate);
					}}
					animate();

					// Responsive: update bounds on resize
					window.addEventListener('resize', () => {{
						x = Math.min(x, window.innerWidth - glassContainer.offsetWidth);
						y = Math.min(y, window.innerHeight - glassContainer.offsetHeight);
					}});

					// Add CSS for premium smoothness
					const style = document.createElement('style');
					style.textContent = `
						#pretty-loading-animation {{
							will-change: opacity;
						}}
						#pretty-loading-animation > div {{
							will-change: transform;
							transition: transform 0.1s cubic-bezier(0.25, 0.46, 0.45, 0.94);
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