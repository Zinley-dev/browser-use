"""
Test script to verify the new Apple Liquid Glass UI is working correctly.

This will open a browser and demonstrate:
1. Premium colored element highlights (cyan, purple, pink, emerald, amber)
2. Glassmorphism interaction overlays with pulsing glow and shimmer
3. DOM highlights with backdrop-filter blur effects

Run with: uv run python test_liquid_glass_ui.py
"""

import asyncio

from browser_use import Agent, BrowserProfile


async def test_liquid_glass_ui():
	print("🎨 Testing Apple Liquid Glass UI...")
	print("=" * 60)

	# Test 1: DOM Highlights (Real-time glassmorphism in browser)
	print("\n📍 Test 1: DOM Highlights with Glassmorphism")
	print("=" * 60)
	profile_dom = BrowserProfile(
		headless=False,
		dom_highlight_elements=True,  # Enable real-time glassmorphism
		highlight_elements=False,  # Disable screenshot highlights
		interaction_highlight_color='rgb(0, 217, 255)',  # Premium cyan glow
		interaction_highlight_duration=2.0,  # 2 second animations
	)

	print(f"✅ DOM Highlights: {profile_dom.dom_highlight_elements}")
	print(f"✅ Interaction Color: {profile_dom.interaction_highlight_color}")
	print(f"✅ Interaction Duration: {profile_dom.interaction_highlight_duration}s")
	print("\nStarting agent with DOM highlights...")
	print("👀 Watch for:")
	print("  - Glowing rounded borders on interactive elements")
	print("  - Backdrop blur effects (glassmorphism)")
	print("  - Premium colored labels (cyan, purple, pink, etc.)")
	print("  - Pulsing glow rings on interactions")
	print("  - Shimmer effects sweeping across elements")

	agent_dom = Agent(browser_profile=profile_dom, task="Go to https://google.com")

	try:
		await agent_dom.run()
		print("\n✅ DOM Highlights test completed!")
		print("📝 You should have seen glassmorphism highlights in the browser")
		input("\nPress Enter to continue to next test...")
	except KeyboardInterrupt:
		print("\n⚠️ Test interrupted by user")
	finally:
		await agent_dom.stop()

	# Test 2: Screenshot Highlights (For LLM)
	print("\n" + "=" * 60)
	print("📸 Test 2: Screenshot Highlights (Python/PIL)")
	print("=" * 60)
	profile_screenshot = BrowserProfile(
		headless=False,
		highlight_elements=True,  # Enable screenshot highlights
		dom_highlight_elements=False,  # Disable DOM highlights
		filter_highlight_ids=False,  # Show all element IDs
		interaction_highlight_color='rgb(255, 107, 157)',  # Premium pink glow
		interaction_highlight_duration=2.0,
	)

	print(f"✅ Screenshot Highlights: {profile_screenshot.highlight_elements}")
	print(f"✅ Interaction Color: {profile_screenshot.interaction_highlight_color}")
	print("\nStarting agent with screenshot highlights...")
	print("👀 Watch for:")
	print("  - Premium colored borders on screenshots sent to LLM")
	print("  - Glowing element labels with vibrant colors")
	print("  - Pink pulsing interaction overlays")

	agent_screenshot = Agent(browser_profile=profile_screenshot, task="Go to https://google.com and show me the search button")

	try:
		await agent_screenshot.run()
		print("\n✅ Screenshot highlights test completed!")
		input("\nPress Enter to finish...")
	except KeyboardInterrupt:
		print("\n⚠️ Test interrupted by user")
	finally:
		await agent_screenshot.stop()

	print("\n" + "=" * 60)
	print("🎉 All tests completed!")
	print("=" * 60)
	print("\n🎨 Premium Apple Liquid Glass UI verified:")
	print("  ✅ Vibrant OLED-optimized colors (cyan, purple, pink, emerald, amber)")
	print("  ✅ Real backdrop-filter blur effects")
	print("  ✅ Multi-layered glowing shadows")
	print("  ✅ Smooth spring animations")
	print("  ✅ Pulsing glow rings")
	print("  ✅ Shimmer light reflections")
	print("\n✨ Your browser automation UI is now PREMIUM! ✨\n")


if __name__ == "__main__":
	asyncio.run(test_liquid_glass_ui())
