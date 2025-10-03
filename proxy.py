#!/usr/bin/env python3
"""
Custom Model Proxy for Claude Code

Routes each Claude Code model tier to different providers:
- Haiku → HAIKU_PROVIDER (or custom model to any provider)
- Opus → OPUS_PROVIDER (or custom model to any provider)
- Sonnet → SONNET_PROVIDER (or Real Anthropic with OAuth if not set)

Supports any Anthropic-compatible API (GLM, Gemini, Ollama, etc.)

Usage:
    # Configure providers for each tier
    export HAIKU_PROVIDER_API_KEY=your_glm_key
    export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

    export OPUS_PROVIDER_API_KEY=your_gemini_key
    export OPUS_PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta

    # SONNET provider optional - defaults to real Anthropic with OAuth
    # export SONNET_PROVIDER_API_KEY=your_key
    # export SONNET_PROVIDER_BASE_URL=http://localhost:11434

    export PORT=8082  # Optional, defaults to 8082

    # Tell Claude Code what models to use
    export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
    export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro
    # export ANTHROPIC_DEFAULT_SONNET_MODEL=llama3.1  # Or leave unset for real Claude
    export ANTHROPIC_BASE_URL=http://localhost:8082

    python proxy.py &
    claude
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os
from pathlib import Path

# Load .env file for provider configs
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables

app = FastAPI(title="Custom Model Proxy for Claude Code")

# Configuration - 3 separate providers (loaded from .env or environment)
HAIKU_API_KEY = os.getenv("HAIKU_PROVIDER_API_KEY")
HAIKU_BASE_URL = os.getenv("HAIKU_PROVIDER_BASE_URL")

OPUS_API_KEY = os.getenv("OPUS_PROVIDER_API_KEY")
OPUS_BASE_URL = os.getenv("OPUS_PROVIDER_BASE_URL")

SONNET_API_KEY = os.getenv("SONNET_PROVIDER_API_KEY")
SONNET_BASE_URL = os.getenv("SONNET_PROVIDER_BASE_URL")

ANTHROPIC_BASE_URL = "https://api.anthropic.com"
PORT = int(os.getenv("PORT", "8082"))

# Model tier detection - read from Claude Code env vars
HAIKU_MODEL = os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-3-haiku")
OPUS_MODEL = os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", "claude-3-opus")
SONNET_MODEL = os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet")


def get_provider_config(model_name: str):
    """
    Determine which provider to route to based on model name.
    Returns (api_key, base_url, provider_name) or None for OAuth passthrough.
    """
    # Check if model matches configured tier models
    if model_name == HAIKU_MODEL and HAIKU_BASE_URL:
        return (HAIKU_API_KEY, HAIKU_BASE_URL, "Haiku Provider")
    elif model_name == OPUS_MODEL and OPUS_BASE_URL:
        return (OPUS_API_KEY, OPUS_BASE_URL, "Opus Provider")
    elif model_name == SONNET_MODEL and SONNET_BASE_URL:
        return (SONNET_API_KEY, SONNET_BASE_URL, "Sonnet Provider")

    # Default to OAuth passthrough (real Anthropic)
    return None


@app.post("/v1/messages")
async def proxy_messages(request: Request):
    """Route requests based on model name and tier configuration"""

    data = await request.json()
    original_model = data.get("model", "")
    is_streaming = data.get("stream", False)
    original_headers = dict(request.headers)

    # Check which provider to route to
    provider_config = get_provider_config(original_model)

    if provider_config:
        # Route to custom provider
        api_key, base_url, provider_name = provider_config
        target_url = f"{base_url}/v1/messages"
        target_headers = {
            "Content-Type": "application/json",
        }

        # Add auth if API key is set
        if api_key:
            target_headers["Authorization"] = f"Bearer {api_key}"

        print(f"[Proxy] {original_model} → {provider_name}")
    else:
        # Default to Real Anthropic with OAuth passthrough
        target_url = f"{ANTHROPIC_BASE_URL}/v1/messages"
        target_headers = {"Content-Type": "application/json"}

        # Forward OAuth token
        if "authorization" in original_headers:
            target_headers["Authorization"] = original_headers["authorization"]

        # Forward Anthropic headers
        for header in ["anthropic-version", "x-api-key"]:
            if header in original_headers:
                target_headers[header] = original_headers[header]

        print(f"[Proxy] {original_model} → Real Anthropic (OAuth)")

    if is_streaming:
        target_headers["Accept"] = "text/event-stream"

    # Forward request
    async with httpx.AsyncClient(timeout=120.0) as client:
        if is_streaming:
            async def stream_generator():
                async with client.stream(
                    "POST", target_url, json=data, headers=target_headers
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        else:
            response = await client.post(
                target_url, json=data, headers=target_headers
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "haiku": {
            "model": HAIKU_MODEL,
            "provider_set": bool(HAIKU_BASE_URL),
            "api_key_set": bool(HAIKU_API_KEY),
        },
        "opus": {
            "model": OPUS_MODEL,
            "provider_set": bool(OPUS_BASE_URL),
            "api_key_set": bool(OPUS_API_KEY),
        },
        "sonnet": {
            "model": SONNET_MODEL,
            "provider_set": bool(SONNET_BASE_URL),
            "api_key_set": bool(SONNET_API_KEY),
            "uses_oauth": not bool(SONNET_BASE_URL),
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("  Custom Model Proxy for Claude Code - Multi-Provider Edition")
    print("=" * 80)
    print()
    print(f"Port: {PORT}")
    print()
    print("Model Tier Configuration:")
    print(f"  Haiku  → {HAIKU_MODEL}")
    print(f"           Provider: {HAIKU_BASE_URL or 'Real Anthropic (OAuth)'}")
    print(f"           API Key: {'✓ Set' if HAIKU_API_KEY else '✗ Not Set'}")
    print()
    print(f"  Opus   → {OPUS_MODEL}")
    print(f"           Provider: {OPUS_BASE_URL or 'Real Anthropic (OAuth)'}")
    print(f"           API Key: {'✓ Set' if OPUS_API_KEY else '✗ Not Set'}")
    print()
    print(f"  Sonnet → {SONNET_MODEL}")
    print(f"           Provider: {SONNET_BASE_URL or 'Real Anthropic (OAuth)'}")
    print(f"           API Key: {'✓ Set' if SONNET_API_KEY else '✗ Not Set'}")
    print()
    print("Routing Logic:")
    print(f"  • {HAIKU_MODEL} → {'Custom Haiku Provider' if HAIKU_BASE_URL else 'Real Anthropic'}")
    print(f"  • {OPUS_MODEL} → {'Custom Opus Provider' if OPUS_BASE_URL else 'Real Anthropic'}")
    print(f"  • {SONNET_MODEL} → {'Custom Sonnet Provider' if SONNET_BASE_URL else 'Real Anthropic'}")
    print()
    print("Configure Claude Code:")
    print("  export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air")
    print("  export ANTHROPIC_DEFAULT_OPUS_MODEL=gemini-1.5-pro")
    print("  # export ANTHROPIC_DEFAULT_SONNET_MODEL=llama3.1  # Optional")
    print(f"  export ANTHROPIC_BASE_URL=http://localhost:{PORT}")
    print()
    print(f"Starting proxy on http://localhost:{PORT}")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
