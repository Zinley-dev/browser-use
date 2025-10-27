# Browser-Use MCP Setup for macOS Swift Apps

## 🎯 What's Fixed

This custom fork includes critical fixes for **Chrome profile support** on macOS:

1. ✅ **Chrome Profile Credentials** - Use your real Chrome profiles (Default, Profile 1, etc.) with saved logins
2. ✅ **Credential Sync** - New logins during automation are saved back to your Chrome profile
3. ✅ **CDP Compatibility** - Automatic profile copying to bypass Chrome's security restriction
4. ✅ **Keep Alive** - Browser stays open after tasks (configurable)
5. ✅ **Direct Arguments** - All settings can be passed as tool arguments (no config.json required)

## 📦 Installation

### Option 1: From Swift App (Recommended)

Update your `BrowserAutomationTool.swift`:

```swift
let config = MCPServerConfig(
    name: "browser-use",
    command: uvxPath,
    args: [
        "--python", qualifiedPython.path,
        "--from", "git+https://github.com/kn1026/browser-use.git#egg=browser-use[cli]",  // ← Custom repo with CLI extras
        "browser-use",
        "--mcp"
    ],
    env: [
        "OPENAI_API_KEY": openAIKey,
        "BROWSER_USE_HEADLESS": "false",
        "BROWSER_USE_LOG_LEVEL": "DEBUG"
    ]
)
```

### Option 2: Manual Installation

```bash
# Install from custom repo (IMPORTANT: Use #egg=browser-use[cli] to install CLI extras)
uvx --python python3.11 --from "git+https://github.com/kn1026/browser-use.git#egg=browser-use[cli]" browser-use --help

# Test MCP mode
export OPENAI_API_KEY="your-key-here"
uvx --python python3.11 --from "git+https://github.com/kn1026/browser-use.git#egg=browser-use[cli]" browser-use --mcp

# Or clone and install in editable mode
git clone https://github.com/kn1026/browser-use.git
cd browser-use
python -m venv .venv
source .venv/bin/activate
pip install -e ".[cli]"  # Important: Include [cli] extras
```

### ⚠️ Common Error: "CLI addon is not installed"

If you see this error:
```
⚠️ CLI addon is not installed. Please install it with: `pip install "browser-use[cli]"` and try again.
```

**Fix:** You forgot the `#egg=browser-use[cli]` part in the git URL!

**Wrong:** `--from git+https://github.com/kn1026/browser-use.git`
**Correct:** `--from "git+https://github.com/kn1026/browser-use.git#egg=browser-use[cli]"`

The `#egg=browser-use[cli]` syntax tells uvx to install the CLI extras when installing from git.

## 🔧 Usage

### Basic Usage (No config.json needed)

```swift
let result = try await mcpManager.executeTool(
    serverName: "browser-use",
    toolName: "retry_with_browser_use_agent",
    arguments: [
        "task": "Navigate to gmail and check unread emails",
        "model": "o3",
        "use_vision": true,
        "max_steps": 100,
        "keep_alive": true,  // Browser stays open
    ]
)
```

### With Chrome Profile (for saved credentials)

```swift
let result = try await mcpManager.executeTool(
    serverName: "browser-use",
    toolName: "retry_with_browser_use_agent",
    arguments: [
        "task": "Login to my account and check settings",
        "model": "o3",
        "use_vision": true,
        "keep_alive": true,

        // Chrome profile settings (uses your real Chrome data)
        "user_data_dir": "\(NSHomeDirectory())/Library/Application Support/Google/Chrome",
        "profile_directory": "Default",  // or "Profile 1", "Profile 5", etc.
    ]
)
```

### All Available Arguments

```swift
arguments: [
    // Required
    "task": String,                    // The task description

    // LLM Settings
    "model": String,                   // Default: "gpt-4o"
    "api_key": String,                 // Override config.json
    "temperature": Float,              // Default: 0.7

    // Agent Settings
    "max_steps": Int,                  // Default: 100
    "use_vision": Bool,                // Default: true
    "allowed_domains": [String],       // Security: restrict domains

    // Browser Profile Settings
    "user_data_dir": String,           // Chrome user data directory
    "profile_directory": String,       // Profile name (Default, Profile 1, etc.)
    "headless": Bool,                  // Run headless
    "keep_alive": Bool,                // Keep browser open after task
]
```

## 📋 Optional: config.json Setup

You can still use `~/.config/browseruse/config.json` for defaults:

```json
{
  "browser_profile": {
    "5523ec30-1126-4f0d-bdf7-ae9b346ee825": {
      "id": "5523ec30-1126-4f0d-bdf7-ae9b346ee825",
      "default": true,
      "created_at": "2025-10-26T14:28:02.600162",
      "headless": false,
      "user_data_dir": "/Users/YOUR_USERNAME/Library/Application Support/Google/Chrome",
      "profile_directory": "Default",
      "keep_alive": true
    }
  },
  "llm": {
    "169d55a2-b3c9-4b2a-8e70-7fa3cf380336": {
      "id": "169d55a2-b3c9-4b2a-8e70-7fa3cf380336",
      "default": true,
      "created_at": "2025-10-26T14:28:02.600168",
      "api_key": "sk-proj-...",
      "model": "o3"
    }
  }
}
```

**Note:** Tool arguments always override config.json values.

## 🔍 How Chrome Profile Support Works

### The Problem
Chrome blocks CDP (Chrome DevTools Protocol) when using the default system Chrome directory for security reasons.

### The Solution
1. **On browser start**: Essential credential files (Cookies, Login Data, etc.) are copied from your real Chrome profile to a temporary non-default location
2. **During automation**: Chrome runs from the temp location (CDP works)
3. **On browser close**: Modified credentials are synced back to your real Chrome profile
4. **Result**: Your logins persist across sessions! 🎉

### Files Synced
- `Cookies` - Browser cookies
- `Login Data` - Saved passwords
- `Web Data` - Autofill data
- `Bookmarks` - User bookmarks
- `Preferences` - User preferences
- `History` - Browsing history

## 🚀 Quick Start

1. **Install prerequisites**:
   ```bash
   brew install python@3.11
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set API key**:
   ```bash
   export OPENAI_API_KEY="sk-proj-..."
   ```

3. **Update Swift code** to use custom repo (see above)

4. **Run your Swift app** - browser-use will be installed automatically via uvx

## 💡 Tips

- **Keep browser open**: Set `"keep_alive": true` to review automation results
- **Use specific profiles**: Set `"profile_directory": "Profile 5"` to use a dedicated automation profile
- **Debug issues**: Set `BROWSER_USE_LOG_LEVEL=DEBUG` in environment
- **Security**: Use `"allowed_domains": ["example.com"]` to restrict navigation

## 🐛 Troubleshooting

**Chrome closes immediately:**
- Ensure `keep_alive: true` is set in arguments or config.json

**Profile not working:**
- Verify `user_data_dir` points to: `~/Library/Application Support/Google/Chrome`
- Check `profile_directory` matches your Chrome profile name (Default, Profile 1, etc.)
- Look in `chrome://version` → "Profile Path" to find the correct name

**CDP timeout:**
- Kill all Chrome processes: `killall -9 "Google Chrome"`
- Ensure no other Chrome instances are using the same profile

## 📚 References

- Original repo: https://github.com/browser-use/browser-use
- Custom fork: https://github.com/kn1026/browser-use
- MCP Protocol: https://modelcontextprotocol.io/

---

Made with ❤️ for macOS Swift developers
