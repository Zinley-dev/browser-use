# Browser-Use × Orion

**A fork of [browser-use/browser-use](https://github.com/browser-use/browser-use) optimized for [Orion](https://meetorion.app/) browser control capabilities.**

This fork enhances the original browser-use library with performance optimizations and features specifically designed for Orion's advanced browser automation and control requirements.

---

## 🎯 What's Different

This fork includes optimizations and enhancements for production-grade browser automation:

### ⚡ Performance Improvements
- **Adaptive Network Idle Detection**: Intelligent page load waiting that's 5x faster than naive fixed delays
- **Smart Request Filtering**: Automatically filters ads, tracking, and noise from page load detection
- **Configurable Stability Thresholds**: Fine-tune when pages are "ready" for your use case

### 🔧 Orion Integration
Optimized to work seamlessly with [Orion](https://meetorion.app/) for:
- Advanced browser control capabilities
- Production-grade automation workflows
- High-performance parallel execution
- Reliable page state detection

See [NETWORK_IDLE_OPTIMIZATION.md](./NETWORK_IDLE_OPTIMIZATION.md) for technical details on performance improvements.

---

## 🚀 Quick Start

**1. Install dependencies (Python >= 3.11):**
```bash
# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate
uv sync

# Or using pip
pip install -r requirements.txt
```

**2. Download Chromium:**
```bash
uvx playwright install chromium --with-deps --no-shell
```

**3. Set up your LLM API key:**
```bash
# For OpenAI
export OPENAI_API_KEY=your-key

# For Anthropic
export ANTHROPIC_API_KEY=your-key

# Or create a .env file
echo "OPENAI_API_KEY=your-key" > .env
```

**4. Run your first agent:**
```python
from browser_use import Agent
from langchain_openai import ChatOpenAI
import asyncio

async def main():
    agent = Agent(
        task="Find the number of GitHub stars for browser-use/browser-use",
        llm=ChatOpenAI(model="gpt-4o"),
    )

    result = await agent.run()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📖 Documentation

### Configuration

This fork adds enhanced configuration options for page load optimization:

```python
from browser_use import Agent
from browser_use.browser.profile import BrowserProfile
from langchain_openai import ChatOpenAI

# Configure adaptive network idle detection
profile = BrowserProfile(
    # Network idle settings (new in this fork)
    enable_adaptive_network_idle=True,  # Enable smart waiting
    network_idle_time=0.5,               # Network must be idle for 500ms
    network_idle_max_inflight=2,         # Max 2 requests to consider "idle"
    network_idle_timeout=10.0,           # Max wait time before giving up

    # Standard browser settings
    headless=False,
    user_data_dir=None,
)

agent = Agent(
    task="Your task here",
    llm=ChatOpenAI(model="gpt-4o"),
    browser_profile=profile,
)
```

### Performance Tuning

**Conservative (Wait for Complete Idle):**
```python
BrowserProfile(
    network_idle_max_inflight=0,      # All requests must finish
    network_idle_time=0.5,             # Stable for 500ms
    network_idle_timeout=15.0          # Wait up to 15s
)
```

**Aggressive (Fast but may miss lazy content):**
```python
BrowserProfile(
    network_idle_max_inflight=5,      # Allow 5 in-flight requests
    network_idle_time=0.2,             # Stable for 200ms
    network_idle_timeout=5.0           # Give up after 5s
)
```

**Legacy (Original browser-use behavior):**
```python
BrowserProfile(
    enable_adaptive_network_idle=False  # Disable optimizations
)
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ci -v

# Run specific test suite
uv run pytest tests/ci/browser/test_page_load_timing.py -v

# Type checking
uv run pyright
```

---

## 📊 Performance Comparison

| Scenario | Original | This Fork | Improvement |
|----------|----------|-----------|-------------|
| Simple page | ~1 second | ~0-200ms | **5x faster** |
| Slow page (3s load) | Captures too early ❌ | Waits until stable ✅ | **More reliable** |
| Already loaded | Waits 1s unnecessarily | Returns immediately | **Eliminates waste** |

---

## 🔗 Links

- **Original Project**: [browser-use/browser-use](https://github.com/browser-use/browser-use)
- **Orion**: [meetorion.app](https://meetorion.app/)
- **Original Docs**: [docs.browser-use.com](https://docs.browser-use.com)
- **Optimization Details**: [NETWORK_IDLE_OPTIMIZATION.md](./NETWORK_IDLE_OPTIMIZATION.md)

---

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/browser-use.git
cd browser-use

# Install dev dependencies
uv sync

# Run tests
uv run pytest tests/ci -v

# Type check
uv run pyright

# Format code
uv run ruff format
uv run ruff check --fix
```

---

## 📝 Examples

### Basic Usage
```python
from browser_use import Agent
from langchain_openai import ChatOpenAI
import asyncio

async def search_example():
    agent = Agent(
        task="Search for the latest news about AI",
        llm=ChatOpenAI(model="gpt-4o"),
    )
    await agent.run()

asyncio.run(search_example())
```

### Custom Tools
```python
from browser_use import Agent
from browser_use.tools import Tool
from langchain_openai import ChatOpenAI

@Tool()
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    task="Check weather in San Francisco",
    llm=ChatOpenAI(model="gpt-4o"),
    use_custom_tools=[get_weather],
)
```

### Using Real Browser Profile
```python
from browser_use import Agent
from browser_use.browser.profile import BrowserProfile
from langchain_openai import ChatOpenAI
from pathlib import Path

profile = BrowserProfile(
    user_data_dir=Path.home() / ".config" / "google-chrome" / "Default",
    headless=False,
)

agent = Agent(
    task="Check my Gmail inbox",
    llm=ChatOpenAI(model="gpt-4o"),
    browser_profile=profile,
)
```

More examples in the [examples/](./examples/) directory.

---

## 🤝 Contributing

This is a fork optimized for Orion integration. For contributions to the core browser-use library, please see the [original repository](https://github.com/browser-use/browser-use).

For Orion-specific improvements and optimizations:
1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

Same as the original [browser-use](https://github.com/browser-use/browser-use) project.

---

## 🙏 Credits

- **Original Project**: [browser-use](https://github.com/browser-use/browser-use) by Magnus and Gregor
- **Orion Integration**: Optimizations for [Orion](https://meetorion.app/) browser control capabilities
- **Community**: All contributors to the browser-use ecosystem

---

<div align="center">

**Intelligent browser automation for production workloads**

Forked with ❤️ for Orion

</div>
