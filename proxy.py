#!/usr/bin/env python3
"""
Custom Model Proxy for Claude Code

Routes each Claude Code model tier to different providers:
- Haiku → HAIKU_PROVIDER (or custom model to any provider)
- Opus → OPUS_PROVIDER (or custom model to any provider)
- Sonnet → SONNET_PROVIDER (or Real Anthropic with OAuth if not set)

Supports any Anthropic-compatible API (GLM, etc.)

Usage:
    # Configure providers for each tier
    export HAIKU_PROVIDER_API_KEY=your_glm_key
    export HAIKU_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

    export OPUS_PROVIDER_API_KEY=your_glm_key
    export OPUS_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

    # SONNET provider optional - defaults to real Anthropic with OAuth
    # export SONNET_PROVIDER_API_KEY=your_glm_key
    # export SONNET_PROVIDER_BASE_URL=https://api.z.ai/api/anthropic

    export PORT=8082  # Optional, defaults to 8082

    # Tell Claude Code what models to use
    export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
    export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6
    # export ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4-plus  # Or leave unset for real Claude
    export ANTHROPIC_BASE_URL=http://localhost:8082

    python proxy.py &
    claude
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.background import BackgroundTask
from contextlib import asynccontextmanager
import httpx
import os
import logging
import asyncio
import random
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file for provider configs
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - create persistent HTTP client"""
    # Startup: Create persistent client with granular timeout and connection limits
    connect_timeout = float(os.getenv("CONNECT_TIMEOUT", "10"))
    read_timeout = float(os.getenv("READ_TIMEOUT", "300"))  # 5 minutes for slow providers
    write_timeout = float(os.getenv("WRITE_TIMEOUT", "30"))
    pool_timeout = float(os.getenv("POOL_TIMEOUT", "5"))

    timeout_config = httpx.Timeout(
        connect=connect_timeout,
        read=read_timeout,
        write=write_timeout,
        pool=pool_timeout
    )

    # Connection pool limits to prevent exhaustion
    limits = httpx.Limits(
        max_connections=int(os.getenv("MAX_CONNECTIONS", "100")),
        max_keepalive_connections=int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20")),
        keepalive_expiry=float(os.getenv("KEEPALIVE_EXPIRY", "30.0"))
    )

    app.state.http_client = httpx.AsyncClient(timeout=timeout_config, limits=limits)
    logger.info(f"HTTP client initialized - connect: {connect_timeout}s, read: {read_timeout}s")
    yield
    # Shutdown: Clean up client
    await app.state.http_client.aclose()

app = FastAPI(
    title="Custom Model Proxy for Claude Code",
    lifespan=lifespan
)

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

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BASE_RETRY_DELAY = float(os.getenv("BASE_RETRY_DELAY", "1.0"))  # Initial delay in seconds
MAX_RETRY_DELAY = float(os.getenv("MAX_RETRY_DELAY", "60.0"))   # Maximum delay cap

# Concurrency control - separate semaphore per provider to prevent overwhelming
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
haiku_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
opus_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
sonnet_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


def get_provider_config(model_name: str):
    """
    Determine which provider to route to based on model name.
    Returns (api_key, base_url, provider_name, semaphore) or None for OAuth passthrough.
    """
    # Check if model matches configured tier models
    if model_name == HAIKU_MODEL and HAIKU_BASE_URL:
        return (HAIKU_API_KEY, HAIKU_BASE_URL, "Haiku Provider", haiku_semaphore)
    elif model_name == OPUS_MODEL and OPUS_BASE_URL:
        return (OPUS_API_KEY, OPUS_BASE_URL, "Opus Provider", opus_semaphore)
    elif model_name == SONNET_MODEL and SONNET_BASE_URL:
        return (SONNET_API_KEY, SONNET_BASE_URL, "Sonnet Provider", sonnet_semaphore)

    # Default to OAuth passthrough (real Anthropic) - no semaphore needed
    return None


def calculate_retry_delay(attempt: int) -> float:
    """
    Calculate retry delay with exponential backoff and full jitter.
    Full jitter prevents thundering herd problem.
    """
    # Exponential backoff: base * 2^attempt, capped at MAX_RETRY_DELAY
    max_delay = min(MAX_RETRY_DELAY, BASE_RETRY_DELAY * (2 ** attempt))
    # Full jitter: random between 0 and max_delay
    return random.uniform(0, max_delay)


async def safe_stream_wrapper(stream, model_name: str):
    """Wrap streaming response to handle mid-stream timeouts gracefully"""
    try:
        async for chunk in stream:
            yield chunk
    except httpx.ReadTimeout:
        logger.error(f"[Mid-Stream Timeout] {model_name} - provider stopped sending data")
        # Stream is broken, stop yielding
    except httpx.NetworkError as e:
        logger.error(f"[Mid-Stream Network Error] {model_name} - {e}")
        # Stream is broken, stop yielding
    except Exception as e:
        logger.error(f"[Mid-Stream Error] {model_name} - {type(e).__name__}: {e}")
        # Stream is broken, stop yielding


@app.post("/v1/messages")
async def proxy_messages(request: Request):
    """
    Route requests based on model name with:
    - Concurrency limiting via semaphores
    - Retry with exponential backoff + jitter
    - Rate limit handling
    - Comprehensive error handling
    """
    data = await request.json()
    original_model = data.get("model", "")
    is_streaming = data.get("stream", False)
    original_headers = dict(request.headers)

    # Check which provider to route to
    provider_config = get_provider_config(original_model)

    if provider_config:
        # Route to custom provider
        api_key, base_url, provider_name, provider_semaphore = provider_config
        target_url = f"{base_url}/v1/messages"
        target_headers = {"Content-Type": "application/json"}

        # Add auth if API key is set
        if api_key:
            target_headers["Authorization"] = f"Bearer {api_key}"

        logger.info(f"[Proxy] {original_model} → {provider_name}")
    else:
        # Default to Real Anthropic with OAuth passthrough (no semaphore)
        provider_semaphore = None
        target_url = f"{ANTHROPIC_BASE_URL}/v1/messages"
        target_headers = {"Content-Type": "application/json"}

        # Forward OAuth token
        if "authorization" in original_headers:
            target_headers["Authorization"] = original_headers["authorization"]

        # Forward Anthropic headers (anthropic-beta is CRITICAL for OAuth)
        for header in ["anthropic-version", "anthropic-beta", "x-api-key"]:
            if header in original_headers:
                target_headers[header] = original_headers[header]

        # Debug logging for auth method
        auth_method = "OAuth" if "authorization" in original_headers else "API Key"
        has_beta = "anthropic-beta" in original_headers
        logger.info(f"[Proxy] {original_model} → Real Anthropic ({auth_method}, beta={has_beta})")

    # Get persistent client from app state
    client = request.app.state.http_client

    # Semaphore context manager (only for custom providers)
    semaphore_ctx = provider_semaphore if provider_semaphore else asyncio.Semaphore(9999)

    # Retry loop with exponential backoff + jitter
    async with semaphore_ctx:
        # Log semaphore acquisition
        if provider_semaphore:
            slots_available = provider_semaphore._value
            logger.info(f"[Concurrency] Acquired slot (available: {slots_available}/{MAX_CONCURRENT_REQUESTS})")

        for attempt in range(MAX_RETRIES):
            try:
                # Forward request
                if is_streaming:
                    target_headers["Accept"] = "text/event-stream"

                    # Build request for streaming
                    req = client.build_request(
                        "POST", target_url, json=data, headers=target_headers
                    )

                    # Attempt streaming connection with timeout protection
                    try:
                        response = await client.send(req, stream=True)
                    except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                        error_type = "Read timeout" if isinstance(e, httpx.ReadTimeout) else "Connect timeout"
                        logger.error(f"[Streaming {error_type}] {original_model} (attempt {attempt + 1}/{MAX_RETRIES})")

                        if attempt < MAX_RETRIES - 1:
                            retry_delay = calculate_retry_delay(attempt)
                            logger.warning(f"[Streaming Retry] Retrying in {retry_delay:.2f}s...")
                            await asyncio.sleep(retry_delay)
                            continue  # Retry the loop
                        else:
                            # Max retries exhausted
                            return JSONResponse(
                                status_code=504,
                                content={"error": f"Gateway timeout - {error_type.lower()} during streaming connection"}
                            )

                    # Connection successful - return streaming response with safe wrapper
                    return StreamingResponse(
                        safe_stream_wrapper(response.aiter_bytes(), original_model),
                        media_type="text/event-stream",
                        background=BackgroundTask(response.aclose)  # Critical: cleanup
                    )
                else:
                    # Non-streaming request
                    response = await client.post(
                        target_url, json=data, headers=target_headers
                    )

                    # Handle rate limiting (429)
                    if response.status_code == 429 and attempt < MAX_RETRIES - 1:
                        retry_after = response.headers.get("retry-after")
                        if retry_after:
                            retry_delay = float(retry_after)
                        else:
                            retry_delay = calculate_retry_delay(attempt)

                        logger.warning(f"[429 Rate Limited] Retrying in {retry_delay:.2f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue

                    # Log 422 errors for debugging
                    if response.status_code == 422:
                        logger.error(f"[422 Unprocessable Entity] Model: {original_model}")

                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )

            except httpx.ReadTimeout:
                logger.error(f"[Non-streaming Read Timeout] {original_model} (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    retry_delay = calculate_retry_delay(attempt)
                    logger.warning(f"[Retry] Retrying in {retry_delay:.2f}s...")
                    await asyncio.sleep(retry_delay)
                    continue
                # Return 504 Gateway Timeout
                return JSONResponse(
                    status_code=504,
                    content={"error": "Gateway timeout - provider did not respond in time"}
                )

            except httpx.ConnectTimeout:
                logger.error(f"[Connect Timeout] {original_model} (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    retry_delay = calculate_retry_delay(attempt)
                    logger.warning(f"[Retry] Retrying in {retry_delay:.2f}s...")
                    await asyncio.sleep(retry_delay)
                    continue
                return JSONResponse(
                    status_code=504,
                    content={"error": "Gateway timeout - could not connect to provider"}
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"[HTTP Error] {e.response.status_code} - {e.response.text}")
                return Response(
                    content=e.response.content,
                    status_code=e.response.status_code,
                    headers=dict(e.response.headers)
                )

            except Exception as e:
                logger.error(f"[Unexpected Error] {original_model} (attempt {attempt + 1}/{MAX_RETRIES}): {type(e).__name__} - {e}")
                if attempt < MAX_RETRIES - 1:
                    retry_delay = calculate_retry_delay(attempt)
                    logger.warning(f"[Retry] Retrying in {retry_delay:.2f}s...")
                    await asyncio.sleep(retry_delay)
                    continue
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Internal proxy error: {str(e)}"}
                )

        # Should not reach here, but just in case
        return JSONResponse(
            status_code=500,
            content={"error": "Max retries exceeded"}
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
    print("  export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6")
    print("  # export ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4-plus  # Optional")
    print(f"  export ANTHROPIC_BASE_URL=http://localhost:{PORT}")
    print()
    print(f"Starting proxy on http://localhost:{PORT}")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
