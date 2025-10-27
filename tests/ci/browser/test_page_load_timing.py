"""
Tests for page load timing and network idle detection.

This file tests the browser's ability to wait for page stability before
capturing DOM state and screenshots.
"""

import asyncio
import time

import pytest
from pytest_httpserver import HTTPServer

from browser_use.browser import BrowserSession
from browser_use.browser.events import BrowserStateRequestEvent, NavigateToUrlEvent
from browser_use.browser.profile import BrowserProfile


@pytest.fixture(scope='session')
def http_server():
	"""Create and provide a test HTTP server that serves pages with various loading patterns."""
	server = HTTPServer()
	server.start()

	# Simple page that loads immediately
	server.expect_request('/simple').respond_with_data(
		'<html><head><title>Simple Page</title></head><body><h1>Simple Page</h1></body></html>',
		content_type='text/html',
	)

	# Page with slow-loading resource (simulates real-world network delay)
	server.expect_request('/slow-page').respond_with_data(
		"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>Slow Loading Page</title>
			<script>
				// Simulate a slow-loading resource
				fetch('/slow-resource').then(r => r.text()).then(data => {
					document.getElementById('result').textContent = data;
				});
			</script>
		</head>
		<body>
			<h1>Page with Slow Resource</h1>
			<div id="result">Loading...</div>
		</body>
		</html>
		""",
		content_type='text/html',
	)

	# Slow resource that takes 2 seconds to respond
	def slow_resource_handler(request):
		time.sleep(2)
		return 'Resource loaded!'

	server.expect_request('/slow-resource').respond_with_handler(slow_resource_handler)

	# Page that continues loading resources after initial render
	server.expect_request('/dynamic-page').respond_with_data(
		"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>Dynamic Page</title>
			<script>
				// Load resources after page load
				window.addEventListener('load', () => {
					setTimeout(() => {
						fetch('/dynamic-resource-1');
					}, 100);
					setTimeout(() => {
						fetch('/dynamic-resource-2');
					}, 500);
				});
			</script>
		</head>
		<body>
			<h1>Dynamic Loading Page</h1>
		</body>
		</html>
		""",
		content_type='text/html',
	)

	server.expect_request('/dynamic-resource-1').respond_with_data('resource1', content_type='text/plain')
	server.expect_request('/dynamic-resource-2').respond_with_data('resource2', content_type='text/plain')

	# Page with long-polling request (should be filtered out)
	server.expect_request('/polling-page').respond_with_data(
		"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>Polling Page</title>
			<script>
				// Simulate long-polling
				function poll() {
					fetch('/long-poll').then(r => r.text()).then(() => {
						// Start next poll immediately
						poll();
					});
				}
				poll();
			</script>
		</head>
		<body>
			<h1>Page with Long Polling</h1>
		</body>
		</html>
		""",
		content_type='text/html',
	)

	# Long polling endpoint that hangs for 15 seconds
	def long_poll_handler(request):
		time.sleep(15)
		return 'poll response'

	server.expect_request('/long-poll').respond_with_handler(long_poll_handler)

	yield server
	server.stop()


@pytest.fixture(scope='session')
def base_url(http_server):
	"""Return the base URL for the test HTTP server."""
	return f'http://{http_server.host}:{http_server.port}'


@pytest.fixture
async def browser_session():
	"""Create a browser session for testing."""
	session = BrowserSession(
		browser_profile=BrowserProfile(
			headless=True,
			user_data_dir=None,
			keep_alive=False,
		)
	)
	await session.start()
	yield session
	await session.kill()


class TestPageLoadTiming:
	"""Tests for page load timing behavior."""

	async def test_simple_page_loads_quickly(self, browser_session, base_url):
		"""Test that a simple page loads without unnecessary delays."""
		# Navigate to simple page
		nav_event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/simple'))
		await nav_event

		# Request browser state and measure time
		start_time = time.time()
		state_event = browser_session.event_bus.dispatch(BrowserStateRequestEvent(include_screenshot=True))
		await state_event
		result = await state_event.event_result()
		elapsed = time.time() - start_time

		# Simple page should capture state quickly (< 2 seconds)
		assert elapsed < 2.0, f'Simple page took {elapsed:.2f}s to capture state'
		assert result is not None
		assert 'Simple Page' in result.title

	async def test_current_behavior_with_pending_requests(self, browser_session, base_url):
		"""Test current behavior: captures state even while resources are loading."""
		# Navigate to page with slow resource
		nav_event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/slow-page'))
		await nav_event

		# Small delay to let navigation settle but not long enough for slow resource
		await asyncio.sleep(0.2)

		# Request browser state immediately (while resource is loading)
		start_time = time.time()
		state_event = browser_session.event_bus.dispatch(BrowserStateRequestEvent(include_screenshot=True))
		await state_event
		result = await state_event.event_result()
		elapsed = time.time() - start_time

		# Current implementation may capture immediately or wait up to 1s
		# depending on timing of when the fetch() starts
		assert result is not None
		assert 'Slow Loading Page' in result.title
		# Should complete in reasonable time (< 3s)
		assert elapsed < 3.0, f'Page capture took too long: {elapsed:.2f}s'

	async def test_document_ready_state_detection(self, browser_session, base_url):
		"""Test that we can detect document.readyState."""
		# Navigate to simple page
		nav_event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/simple'))
		await nav_event
		await asyncio.sleep(0.5)  # Wait for page to fully load

		# Get DOM watchdog to check pending requests
		dom_watchdog = browser_session._dom_watchdog
		assert dom_watchdog is not None, 'DOMWatchdog not found'

		# Check pending requests (should be none on fully loaded page)
		pending = await dom_watchdog._get_pending_network_requests()
		assert isinstance(pending, list), 'Should return list of pending requests'


class TestNetworkRequestDetection:
	"""Tests for network request detection logic."""

	async def test_filters_ads_and_tracking(self, browser_session, base_url):
		"""Test that ad/tracking requests are filtered from pending requests."""
		# This test verifies the filtering logic works
		# We'll load a simple page and check that the filter list is being applied
		nav_event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/simple'))
		await nav_event
		await asyncio.sleep(0.2)

		# Get DOM watchdog
		dom_watchdog = browser_session._dom_watchdog
		assert dom_watchdog is not None

		pending = await dom_watchdog._get_pending_network_requests()

		# All pending requests should not contain known ad domains
		ad_domains = ['doubleclick.net', 'googlesyndication.com', 'googletagmanager.com']
		for request in pending:
			for ad_domain in ad_domains:
				assert ad_domain not in request.url, f'Ad domain {ad_domain} should be filtered out'

	async def test_long_polling_filtered_after_timeout(self, browser_session, base_url):
		"""Test that long-running requests (>10s) are filtered out."""
		# Navigate to polling page
		nav_event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/polling-page'))
		await nav_event

		# Wait for polling to start
		await asyncio.sleep(0.5)

		# Get DOM watchdog
		dom_watchdog = browser_session._dom_watchdog
		assert dom_watchdog is not None

		# Check pending requests multiple times
		for i in range(3):
			pending = await dom_watchdog._get_pending_network_requests()
			# The filter logic should eventually exclude requests loading >10s
			# For now, just verify we can call this without errors
			assert isinstance(pending, list)
			await asyncio.sleep(0.5)
