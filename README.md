# Custom Model Proxy for Claude Code

Route **each Claude Code model tier** to **different providers**! Use GLM for Haiku, Gemini for Opus, and keep Sonnet on your Claude subscription - all at the same time.

## Key Features

- ✨ **3 independent providers** - Route Haiku, Opus, and Sonnet to different APIs simultaneously
- 🔄 **Mix and match** - GLM for speed, Gemini for quality, Claude for premium, Ollama for local
- 💰 **Cost optimized** - Route cheap tasks to alternatives, premium to Claude
- 🔐 **OAuth preserved** - Keep your Claude subscription active for Sonnet
- 🎯 **Dead simple** - Each tier configured with just 2 environment variables
- 🌐 **Cross-platform** - Works on macOS, Linux, and Windows

## What It Does

```
Claude Code UI          Proxy Routes To
─────────────────       ───────────────────────────────
Haiku  (glm-4.5-air)    → GLM API
Opus   (gemini-1.5-pro) → Gemini API
Sonnet (claude-sonnet)  → Real Anthropic (OAuth)
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure providers
export HAIKU_PROVIDER_API_KEY=your_glm_api_key
export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export OPUS_PROVIDER_API_KEY=your_gemini_api_key
export OPUS_PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# 3. Configure Claude Code
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro
export ANTHROPIC_BASE_URL=http://localhost:8082  # ⚠️ CRITICAL

# 4. Start proxy & use Claude Code
python proxy.py &
claude
```

**📖 [Full Setup Guide →](SETUP.md)** (includes Windows, troubleshooting, examples)

## How It Works

The proxy intercepts Claude Code's API requests:

1. **You set:** `ANTHROPIC_BASE_URL=http://localhost:8082`
2. **Claude Code sends requests to:** `localhost:8082` instead of `api.anthropic.com`
3. **Proxy checks model name:**
   - `glm-4.5-air` → Routes to GLM (HAIKU_PROVIDER_BASE_URL)
   - `gemini-1.5-pro` → Routes to Gemini (OPUS_PROVIDER_BASE_URL)
   - `claude-sonnet-4-5` → Routes to real Anthropic (OAuth passthrough)

## Supported Providers

- **GLM** (via Z.AI) - Fast, cheap Chinese models
- **Google Gemini** - High-quality Google models
- **Ollama** (local) - Free, offline local models
- **Any Anthropic-compatible API** - Works with any provider supporting `/v1/messages`

## Use Cases

### Cost Optimization
```bash
Haiku  → GLM (glm-4-flash)      # $0.01/1M tokens
Opus   → Gemini (gemini-1.5-pro) # $1.25/1M tokens
Sonnet → Claude (real)           # Your subscription
```

### Offline Development
```bash
Haiku  → Ollama (llama3.1:8b)
Opus   → Ollama (qwen2.5:14b)
Sonnet → Ollama (qwen2.5:32b)
```

### Hybrid Local + Cloud
```bash
Haiku  → Ollama (free, local)
Opus   → GLM (cheap, fast)
Sonnet → Claude (premium)
```

## Benefits

✅ **Keep your Claude subscription** - Sonnet uses OAuth, no API key needed
✅ **3 providers simultaneously** - Different provider for each tier
✅ **Native Claude Code support** - Uses built-in environment variables
✅ **Update-proof** - No SDK modifications, survives updates
✅ **Transparent** - `/model` command shows actual model names
✅ **Simple** - Just environment variables, no complex config
✅ **Cross-platform** - macOS, Linux, Windows support

## Requirements

- Python 3.8+
- Claude Code installed globally
- Provider(s) with Anthropic-compatible API

## Documentation

- **[SETUP.md](SETUP.md)** - Full installation guide (macOS/Linux/Windows)
- **[.env.example](.env.example)** - Configuration template with examples
- **[proxy.py](proxy.py)** - Source code (208 lines)

## Quick Troubleshooting

**Proxy not intercepting?**
```bash
# Verify this is set:
echo $ANTHROPIC_BASE_URL  # Should output: http://localhost:8082
```

**Model not routing?**
```bash
# Check proxy is running:
curl http://localhost:8082/health
```

**More help:** See [SETUP.md → Troubleshooting](SETUP.md#troubleshooting)

## Example: Multi-Provider Setup

```bash
# GLM for Haiku (fast, cheap)
export HAIKU_PROVIDER_API_KEY=sk-glm-xxx
export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4-flash

# Gemini for Opus (balanced)
export OPUS_PROVIDER_API_KEY=AIza-xxx
export OPUS_PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta
export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro

# Claude for Sonnet (premium, OAuth)
# No config needed - uses your subscription

# Enable proxy
export ANTHROPIC_BASE_URL=http://localhost:8082
python proxy.py &
claude
```

## License

MIT

---

**Made this?** [⭐ Star on GitHub](https://github.com/yourusername/claude-code-proxy)
**Questions?** See [SETUP.md](SETUP.md) or open an issue
