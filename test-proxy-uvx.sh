#!/bin/bash

echo "========================================"
echo "🧪 Browser-Use with SnowX API Proxy Test"
echo "========================================"
echo ""

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s -f http://localhost:3000/api/browser-use/o3/v1/chat/completions \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"test"}],"max_completion_tokens":10}' > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:3000"
else
    echo "❌ Backend is NOT running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd /Users/khoinguyen/Desktop/snowx-api-v2"
    echo "  npm run dev"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "🚀 Running browser automation test..."
echo "========================================"
echo ""

# Kill any existing Chrome processes
echo "🧹 Cleaning up existing Chrome processes..."
killall -9 "Google Chrome" 2>/dev/null || true
sleep 2

# Create inline Python script
cat > /tmp/test-proxy.py << 'PYTHON_SCRIPT'
import asyncio
import os
import sys

# Set environment variables
os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'INFO'
os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'

from browser_use import Agent
from browser_use.browser import BrowserProfile
from browser_use.llm import ChatOpenAI

async def main():
    print("="*60)
    print("🔧 Configuring LLM to use SnowX API proxy...")

    llm = ChatOpenAI(
        model='o3',
        api_key='not-needed',
        base_url='http://localhost:3000/api/browser-use/o3/v1',  # ChatOpenAI appends /chat/completions
        temperature=0.7,
    )

    print(f"✓ Model: {llm.model}")
    print(f"✓ Proxy: http://localhost:3000/api/browser-use/o3/v1/chat/completions")

    profile = BrowserProfile(
        headless=False,
        user_data_dir='/Users/khoinguyen/Library/Application Support/Google/Chrome',
        profile_directory='Default',
        allowed_domains=[],
        keep_alive=False,
    )

    print(f"✓ Profile: {profile.profile_directory}")

    task = "Go to google.com and search for 'OpenAI'. Tell me the first search result title."

    print(f"\n📋 Task: {task}")
    print("\n🚀 Starting agent...")
    print("-"*60)

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=profile,
        use_vision=False,
    )

    try:
        history = await agent.run(max_steps=10)

        print("\n" + "="*60)
        print("✅ RESULTS")
        print("="*60)
        print(f"\nSteps: {len(history.history)}")
        print(f"Success: {history.is_successful()}")

        final_result = history.final_result()
        if final_result:
            print(f"\n📊 Final Result:\n{final_result}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await agent.close()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
PYTHON_SCRIPT

# Run the test using uvx (like MCP server)
echo "🔧 Running test via uvx (same as MCP server)..."
~/.local/bin/uvx --python python3.11 \
  --from "git+https://github.com/kn1026/browser-use.git#egg=browser-use[cli]" \
  python3 /tmp/test-proxy.py

EXIT_CODE=$?

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test completed successfully"
    echo "✅ Browser-use works with SnowX API proxy!"
else
    echo "❌ Test failed with exit code $EXIT_CODE"
fi
echo "========================================"
echo ""

# Cleanup
rm -f /tmp/test-proxy.py

exit $EXIT_CODE
