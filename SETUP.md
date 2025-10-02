# Claude Code Proxy - Setup Guide

Complete installation and configuration guide for all platforms.

**Quick Links:**
- [Installation](#installation)
- [Making It Permanent](#making-it-permanent)
- [Provider Examples](#provider-examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

### 1. Install Dependencies

**macOS/Linux:**
```bash
pip install -r requirements.txt
```

**Windows:**
```powershell
pip install -r requirements.txt
# Or if you have multiple Python versions:
python -m pip install -r requirements.txt
```

### 2. Configure Providers

Create `.env` file:

**macOS/Linux:**
```bash
cp .env.example .env
nano .env  # or vim, or code .env
```

**Windows:**
```powershell
Copy-Item .env.example .env
notepad .env  # or code .env
```

Add your provider credentials for each tier:

```bash
# Haiku provider
HAIKU_PROVIDER_API_KEY=your_haiku_api_key
HAIKU_PROVIDER_BASE_URL=https://api.provider.com/v1

# Opus provider
OPUS_PROVIDER_API_KEY=your_opus_api_key
OPUS_PROVIDER_BASE_URL=https://api.provider.com/v1

# Sonnet provider (optional - leave empty to use real Claude)
# SONNET_PROVIDER_API_KEY=your_sonnet_api_key
# SONNET_PROVIDER_BASE_URL=https://api.provider.com/v1
```

### 3. Set Claude Code Environment Variables

**macOS/Linux:**

Add to `~/.zshrc` (for zsh) or `~/.bashrc` (for bash):

```bash
# Configure which models each tier should use
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro
# export ANTHROPIC_DEFAULT_SONNET_MODEL=llama3.1  # Optional

# Point to local proxy
export ANTHROPIC_BASE_URL=http://localhost:8082
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Windows:**

See ["Making It Permanent"](#making-it-permanent) section below for PowerShell, `setx`, or GUI options.

For current session only:
```powershell
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "glm-4.5-air"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "gemini-1.5-pro"
$env:ANTHROPIC_BASE_URL = "http://localhost:8082"
```

### 4. Start the Proxy

**macOS/Linux:**
```bash
python proxy.py &
```

**Windows:**
```powershell
# Background (hidden window):
Start-Process python -ArgumentList "proxy.py" -WindowStyle Hidden

# Or foreground (see logs):
python proxy.py
```

### 5. Use Claude Code

**All platforms:**
```bash
claude
```

Select Haiku, Opus, or Sonnet from the UI - routing is automatic!

---

## Making It Permanent

### macOS/Linux

**Add to your shell config (`~/.zshrc` for zsh or `~/.bashrc` for bash):**

```bash
# Claude Code Proxy Configuration
export HAIKU_PROVIDER_API_KEY=your_glm_api_key
export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export OPUS_PROVIDER_API_KEY=your_gemini_api_key
export OPUS_PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta

export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro

# ⚠️ This line enables the proxy interception
export ANTHROPIC_BASE_URL=http://localhost:8082
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Windows (PowerShell)

**Option 1: PowerShell Profile (Recommended)**

Edit your PowerShell profile:
```powershell
notepad $PROFILE
```

Add these lines:
```powershell
# Claude Code Proxy Configuration
$env:HAIKU_PROVIDER_API_KEY = "your_glm_api_key"
$env:HAIKU_PROVIDER_BASE_URL = "https://api.z.ai/api/anthropic"
$env:OPUS_PROVIDER_API_KEY = "your_gemini_api_key"
$env:OPUS_PROVIDER_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "glm-4.5-air"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "gemini-1.5-pro"

# ⚠️ This line enables the proxy interception
$env:ANTHROPIC_BASE_URL = "http://localhost:8082"
```

Then reload:
```powershell
. $PROFILE
```

**Option 2: System Environment Variables (Permanent)**

Use `setx` to set permanent environment variables:
```powershell
setx HAIKU_PROVIDER_API_KEY "your_glm_api_key"
setx HAIKU_PROVIDER_BASE_URL "https://api.z.ai/api/anthropic"
setx OPUS_PROVIDER_API_KEY "your_gemini_api_key"
setx OPUS_PROVIDER_BASE_URL "https://generativelanguage.googleapis.com/v1beta"
setx ANTHROPIC_DEFAULT_HAIKU_MODEL "glm-4.5-air"
setx ANTHROPIC_DEFAULT_OPUS_MODEL "gemini-1.5-pro"
setx ANTHROPIC_BASE_URL "http://localhost:8082"
```

⚠️ **Note:** `setx` requires restarting your terminal. For current session, also run:
```powershell
$env:ANTHROPIC_BASE_URL = "http://localhost:8082"
# ... (repeat for other vars)
```

**Option 3: GUI (System Properties)**

1. Open "System Properties" → "Environment Variables"
2. Add each variable under "User variables"
3. Restart your terminal

---

## Starting the Proxy

**Important:** The proxy must be running before you use `claude`.

**macOS/Linux:**
```bash
python proxy.py &
```

**Windows:**
```powershell
Start-Process python -ArgumentList "proxy.py" -WindowStyle Hidden
# Or simply:
python proxy.py
```

---

## Provider Examples

### Example 1: GLM Only (Simple)

Use GLM for all tiers:

**macOS/Linux:**
```bash
# All tiers use GLM
export HAIKU_PROVIDER_API_KEY=your_glm_api_key
export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air

export OPUS_PROVIDER_API_KEY=your_glm_api_key
export OPUS_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# Sonnet uses real Claude (no config)
```

**Windows (PowerShell):**
```powershell
# All tiers use GLM
$env:HAIKU_PROVIDER_API_KEY = "your_glm_api_key"
$env:HAIKU_PROVIDER_BASE_URL = "https://api.z.ai/api/anthropic"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "glm-4.5-air"

$env:OPUS_PROVIDER_API_KEY = "your_glm_api_key"
$env:OPUS_PROVIDER_BASE_URL = "https://api.z.ai/api/anthropic"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "glm-4.6"

# Sonnet uses real Claude (no config)
```

**Available GLM models:**
- `glm-4.5-air` - Fast, cheap
- `glm-4.6` - Balanced
- `glm-4-plus` - Premium
- `glm-4-flash` - Fastest

### Example 2: Multi-Provider Mix (Power User)

Mix different providers for optimal cost/performance:

```bash
# Haiku → GLM (fastest, cheapest)
export HAIKU_PROVIDER_API_KEY=your_glm_api_key
export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4-flash

# Opus → Gemini (balanced)
export OPUS_PROVIDER_API_KEY=your_gemini_api_key
export OPUS_PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta
export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro

# Sonnet → Real Claude (premium, OAuth subscription)
# No config needed
```

### Example 3: Local + Cloud Hybrid

Mix local Ollama with cloud providers:

```bash
# Haiku → Local Ollama (free!)
export HAIKU_PROVIDER_API_KEY=dummy
export HAIKU_PROVIDER_BASE_URL=http://localhost:11434
export ANTHROPIC_DEFAULT_HAIKU_MODEL=llama3.1:8b

# Opus → GLM (paid, fast)
export OPUS_PROVIDER_API_KEY=your_glm_api_key
export OPUS_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# Sonnet → Real Claude (premium)
# No config needed
```

Make sure Ollama is running:
```bash
ollama serve
```

### Example 4: All Local (Offline)

Route all models to local Ollama:

```bash
# All tiers use local Ollama
export HAIKU_PROVIDER_API_KEY=dummy
export HAIKU_PROVIDER_BASE_URL=http://localhost:11434
export ANTHROPIC_DEFAULT_HAIKU_MODEL=llama3.1:8b

export OPUS_PROVIDER_API_KEY=dummy
export OPUS_PROVIDER_BASE_URL=http://localhost:11434
export ANTHROPIC_DEFAULT_OPUS_MODEL=qwen2.5:14b

export SONNET_PROVIDER_API_KEY=dummy
export SONNET_PROVIDER_BASE_URL=http://localhost:11434
export ANTHROPIC_DEFAULT_SONNET_MODEL=qwen2.5:32b
```

---

## How The Proxy Works

### The Interception Mechanism

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Configure Claude Code                               │
│ export ANTHROPIC_BASE_URL=http://localhost:8082             │
│                                                              │
│ This tells Claude Code to send ALL API requests to          │
│ localhost:8082 instead of api.anthropic.com                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Start Proxy                                         │
│ python proxy.py &                                           │
│                                                              │
│ Proxy listens on localhost:8082 and waits for requests      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Use Claude Code                                     │
│ claude                                                       │
│                                                              │
│ User selects "Haiku" → Claude Code sends request to         │
│ http://localhost:8082/v1/messages with model=glm-4.5-air    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Proxy Routes Request                                │
│                                                              │
│ Proxy checks: model == HAIKU_MODEL (glm-4.5-air)?           │
│ Yes → Forward to HAIKU_PROVIDER_BASE_URL                    │
│       with HAIKU_PROVIDER_API_KEY                           │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Provider Routing

```
Claude Code (ANTHROPIC_BASE_URL=localhost:8082)
    ↓
    ├─ Request: model=glm-4.5-air
    │  Proxy: matches HAIKU_MODEL
    │  → GLM API (HAIKU_PROVIDER_BASE_URL)
    │
    ├─ Request: model=gemini-1.5-pro
    │  Proxy: matches OPUS_MODEL
    │  → Gemini API (OPUS_PROVIDER_BASE_URL)
    │
    └─ Request: model=claude-sonnet-4-5
       Proxy: matches SONNET_MODEL, no provider set
       → Real Anthropic API (OAuth passthrough)
```

**Key Point:** Without `ANTHROPIC_BASE_URL=http://localhost:8082`, Claude Code would send requests directly to Anthropic, bypassing the proxy entirely.

---

## Agents

Agents automatically use the configured models:

```yaml
---
name: quick-agent
model: haiku  # Uses ANTHROPIC_DEFAULT_HAIKU_MODEL
---
```

```yaml
---
name: balanced-agent
model: opus  # Uses ANTHROPIC_DEFAULT_OPUS_MODEL
---
```

```yaml
---
name: premium-agent
model: sonnet  # Uses real Claude (OAuth)
---
```

Or use model names directly:

```yaml
---
name: explicit-agent
model: glm-4.5-air  # Direct model name
---
```

---

## Verify It's Working

### Watch proxy logs

```bash
[Proxy] glm-4-flash → Haiku Provider
[Proxy] gemini-1.5-pro → Opus Provider
[Proxy] claude-sonnet-4-5 → Real Anthropic (OAuth)
```

### Check proxy health

```bash
curl http://localhost:8082/health
```

Returns:
```json
{
  "status": "healthy",
  "haiku": {
    "model": "glm-4-flash",
    "provider_set": true,
    "api_key_set": true
  },
  "opus": {
    "model": "gemini-1.5-pro",
    "provider_set": true,
    "api_key_set": true
  },
  "sonnet": {
    "model": "claude-sonnet",
    "provider_set": false,
    "api_key_set": false,
    "uses_oauth": true
  }
}
```

---

## Troubleshooting

### Claude Code not using proxy

**Symptom:** Requests go directly to Anthropic, proxy logs show nothing

**Fix:** Verify `ANTHROPIC_BASE_URL` is set:

**macOS/Linux:**
```bash
echo $ANTHROPIC_BASE_URL
# Should output: http://localhost:8082

# If empty, set it:
export ANTHROPIC_BASE_URL=http://localhost:8082

# Add to ~/.zshrc or ~/.bashrc to make permanent
```

**Windows (PowerShell):**
```powershell
echo $env:ANTHROPIC_BASE_URL
# Should output: http://localhost:8082

# If empty, set it:
$env:ANTHROPIC_BASE_URL = "http://localhost:8082"

# To make permanent, use setx:
setx ANTHROPIC_BASE_URL "http://localhost:8082"
# Then restart terminal
```

### Check proxy configuration

**All platforms:**
```bash
# Check if proxy is running
curl http://localhost:8082/health
```

**macOS/Linux:**
```bash
# Check environment variables
echo $HAIKU_PROVIDER_API_KEY
echo $HAIKU_PROVIDER_BASE_URL
echo $OPUS_PROVIDER_API_KEY
echo $OPUS_PROVIDER_BASE_URL
echo $SONNET_PROVIDER_API_KEY
echo $SONNET_PROVIDER_BASE_URL
```

**Windows (PowerShell):**
```powershell
# Check environment variables
echo $env:HAIKU_PROVIDER_API_KEY
echo $env:HAIKU_PROVIDER_BASE_URL
echo $env:OPUS_PROVIDER_API_KEY
echo $env:OPUS_PROVIDER_BASE_URL
echo $env:SONNET_PROVIDER_API_KEY
echo $env:SONNET_PROVIDER_BASE_URL
```

### Models not routing correctly

**macOS/Linux:**
```bash
# Check Claude Code environment variables
echo $ANTHROPIC_DEFAULT_HAIKU_MODEL   # Should match your Haiku provider's model
echo $ANTHROPIC_DEFAULT_OPUS_MODEL    # Should match your Opus provider's model
echo $ANTHROPIC_DEFAULT_SONNET_MODEL  # Should match your Sonnet provider's model (or unset)
echo $ANTHROPIC_BASE_URL              # Should be http://localhost:8082
echo $PORT                            # Optional, defaults to 8082
```

**Windows (PowerShell):**
```powershell
# Check Claude Code environment variables
echo $env:ANTHROPIC_DEFAULT_HAIKU_MODEL   # Should match your Haiku provider's model
echo $env:ANTHROPIC_DEFAULT_OPUS_MODEL    # Should match your Opus provider's model
echo $env:ANTHROPIC_DEFAULT_SONNET_MODEL  # Should match your Sonnet provider's model (or unset)
echo $env:ANTHROPIC_BASE_URL              # Should be http://localhost:8082
echo $env:PORT                            # Optional, defaults to 8082
```

### Specific tier not working

If Haiku isn't routing:

**macOS/Linux:**
```bash
# Verify Haiku provider is set
echo $HAIKU_PROVIDER_API_KEY
echo $HAIKU_PROVIDER_BASE_URL
echo $ANTHROPIC_DEFAULT_HAIKU_MODEL

# Test Haiku provider connection
curl -H "Authorization: Bearer $HAIKU_PROVIDER_API_KEY" \
  "$HAIKU_PROVIDER_BASE_URL/v1/messages" \
  -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

**Windows (PowerShell):**
```powershell
# Verify Haiku provider is set
echo $env:HAIKU_PROVIDER_API_KEY
echo $env:HAIKU_PROVIDER_BASE_URL
echo $env:ANTHROPIC_DEFAULT_HAIKU_MODEL

# Test Haiku provider connection (requires curl or Invoke-WebRequest)
curl -H "Authorization: Bearer $env:HAIKU_PROVIDER_API_KEY" `
  "$env:HAIKU_PROVIDER_BASE_URL/v1/messages" `
  -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

Same for Opus and Sonnet - replace `HAIKU_` with `OPUS_` or `SONNET_`.

### Sonnet using OAuth not working

Make sure you're logged into Claude Code:

**All platforms:**
```bash
claude --login
```

Your OAuth session must be active. If you configured `SONNET_PROVIDER_*` vars, remove them to use OAuth:

**macOS/Linux:**
```bash
unset SONNET_PROVIDER_API_KEY
unset SONNET_PROVIDER_BASE_URL
```

**Windows (PowerShell):**
```powershell
Remove-Item Env:\SONNET_PROVIDER_API_KEY
Remove-Item Env:\SONNET_PROVIDER_BASE_URL

# If set with setx, remove from system:
# Open System Properties → Environment Variables → Delete the variables
# Then restart terminal
```

### Custom Port

Change the proxy port (defaults to 8082):

```bash
export PORT=9000
export ANTHROPIC_BASE_URL=http://localhost:9000
```

---

## Requirements

### All Platforms
- Python 3.8+
- Claude Code installed globally
- Provider with Anthropic-compatible API

### Platform-Specific
- **macOS/Linux:** bash or zsh shell
- **Windows:** PowerShell 5.1+ or PowerShell Core 7+
  - Note: Git Bash and WSL also work (use Linux instructions)

---

**[← Back to README](README.md)**
