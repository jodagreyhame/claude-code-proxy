# Claude Code Proxy: Weekly Rate Limits? Resolved!

Route **each Claude Code model tier** to **different providers**! Use [GLM](https://z.ai/subscribe?ic=CAO6LGU9S1) for Haiku/Opus and keep Sonnet on your [Claude](https://claude.ai/) subscription - all at the same time.

## Why This Exists

Apparently I'm one of the "2%" of users that should encounter or be affected by Anthropic's new weekly limits. So I built this proxy to route certain models to LLM providers of your choice - welcome to the good ol days when we didn't need to worry about hitting our weekly limit. These models work with agents too!

## Key Features

- ✨ **3 independent providers** - Route Haiku, Opus, and Sonnet to different APIs simultaneously
- 🔄 **Mix and match** - GLM for speed/cost, Claude for premium
- 💰 **Cost optimized** - Route cheap tasks to alternatives, premium to Claude
- 🔐 **OAuth preserved** - Keep your Claude subscription active for Sonnet
- 🎯 **Dead simple** - Each tier configured with just 2 environment variables
- 🌐 **Cross-platform** - Works on macOS, Linux, and Windows

## What It Does

```
Claude Code UI          Proxy Routes To
─────────────────       ───────────────────────────────
Haiku  (glm-4.6)        → GLM API
Opus   (glm-4.5-air)    → GLM API
Sonnet (claude-sonnet)  → Real Anthropic (OAuth)
```

## How It Works

The proxy intercepts Claude Code's API requests:

1. **You set:** `ANTHROPIC_BASE_URL=http://localhost:8082`
2. **Claude Code sends requests to:** `localhost:8082` instead of `api.anthropic.com`
3. **Proxy checks model name:**
   - `glm-4.6` → Routes to GLM (HAIKU_PROVIDER_BASE_URL)
   - `glm-4.5-air` → Routes to GLM (OPUS_PROVIDER_BASE_URL)
   - `claude-sonnet-4-5` → Routes to real Anthropic (OAuth passthrough)

## Quick Start

**macOS/Linux:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure providers - Create .env file with:
cat > .env << 'EOF'
# GLM for Haiku (fast, cheap)
HAIKU_PROVIDER_API_KEY=sk-glm-xxx
HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

# GLM for Opus (premium GLM)
OPUS_PROVIDER_API_KEY=sk-glm-xxx
OPUS_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

# Sonnet uses OAuth (leave commented)
# SONNET_PROVIDER_API_KEY=
# SONNET_PROVIDER_BASE_URL=
EOF

# 3. Configure Claude Code (add to ~/.zshrc or ~/.bashrc)
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.6
export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.5-air
export ANTHROPIC_BASE_URL=http://localhost:8082  # ⚠️ CRITICAL

# 4. Start proxy & use Claude Code
python proxy.py &
claude
```

**Windows (PowerShell):**
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure providers - Create .env file with:
@"
# GLM for Haiku (fast, cheap)
HAIKU_PROVIDER_API_KEY=sk-glm-xxx
HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

# GLM for Opus (premium GLM)
OPUS_PROVIDER_API_KEY=sk-glm-xxx
OPUS_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

# Sonnet uses OAuth (leave commented)
# SONNET_PROVIDER_API_KEY=
# SONNET_PROVIDER_BASE_URL=
"@ | Out-File -FilePath .env -Encoding utf8

# 3. Configure Claude Code (add to PowerShell $PROFILE)
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "glm-4.6"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "glm-4.5-air"
$env:ANTHROPIC_BASE_URL = "http://localhost:8082"  # ⚠️ CRITICAL

# 4. Start proxy & use Claude Code
Start-Process python -ArgumentList "proxy.py" -WindowStyle Hidden
claude
```

**What goes where:**
- **`.env` file** → Provider API keys and URLs (read by proxy)
- **Shell env vars** → Claude Code model configs only

## Supported Providers

- **[GLM](https://z.ai/subscribe?ic=CAO6LGU9S1)** (via Z.AI) - Fast, cheap Chinese models
- **[Claude](https://claude.ai/)** - Premium Anthropic models via OAuth
- **Any Anthropic-compatible API** - Works with any provider supporting `/v1/messages`

## Use Cases

```bash
Haiku  → GLM (glm-4.6)      # $0.02/1M tokens
Opus   → GLM (glm-4.5-air)  # $0.01/1M tokens
Sonnet → Claude (real)      # Your subscription
```

## Benefits

| Benefit | Description |
|---------|-------------|
| ✅ **Keep your Claude subscription** | Uses OAuth, no API key needed |
| ✅ **3 providers simultaneously** | Different provider for each tier |
| ✅ **Native Claude Code support** | Uses built-in environment variables |
| ✅ **Update-proof** | No SDK modifications, survives updates |
| ✅ **Transparent** | `/model` command shows actual routed model names |
| ✅ **Simple** | Just environment variables, no complex config |

## Requirements

- Python 3.8+
- Claude Code installed globally
- Provider(s) with Anthropic-compatible API

## Using with Agents

Agents automatically use your configured models:

```yaml
---
name: my-agent
model: haiku  # Uses glm-4.6 (your ANTHROPIC_DEFAULT_HAIKU_MODEL)
---
```

## API Endpoint Support

The proxy implements the following Anthropic API endpoints:

| Endpoint | GLM Providers | Real Anthropic | Notes |
|----------|--------------|----------------|-------|
| `POST /v1/messages` | ✅ Full support | ✅ Full support | Main chat completion endpoint |
| `POST /v1/messages/count_tokens` | ⚠️ Returns 501 | ✅ Full support | Token counting before sending. GLM doesn't support this - use token counts from message responses instead |
| `GET /health` | ✅ Proxy health | ✅ Proxy health | Proxy status endpoint (not forwarded to providers) |

**About Token Counting:**
- **Sonnet (Real Anthropic)**: Token counting works normally via `/v1/messages/count_tokens`
- **Haiku/Opus (GLM)**: Token counting returns HTTP 501 with a helpful message. Token usage is still available in every `/v1/messages` response under the `usage` field.

## Troubleshooting

**Proxy not intercepting requests?**

macOS/Linux:
```bash
echo $ANTHROPIC_BASE_URL  # Should output: http://localhost:8082
# If empty: export ANTHROPIC_BASE_URL=http://localhost:8082
```

Windows:
```powershell
echo $env:ANTHROPIC_BASE_URL  # Should output: http://localhost:8082
# If empty: $env:ANTHROPIC_BASE_URL = "http://localhost:8082"
```

**Check if proxy is running:**
```bash
curl http://localhost:8082/health
```

Expected response:
```json
{
  "status": "healthy",
  "haiku": {"model": "glm-4.6", "provider_set": true},
  "opus": {"model": "glm-4.5-air", "provider_set": true},
  "sonnet": {"uses_oauth": true}
}
```

**Models not routing correctly?**
- Verify model names in `.env` match `ANTHROPIC_DEFAULT_*_MODEL` vars
- Check proxy logs for routing info
- Test provider API keys directly with `curl`

**Sonnet OAuth not working?**
```bash
claude --login  # Refresh your Claude session
```

## License

MIT

---