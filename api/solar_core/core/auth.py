"""API key authentication + rate limiting (Phase 1 / 4C.9d).

verify_api_key is the single dependency every protected route already uses, so
adding rate-limiting here covers Air, process, documents, and connectors at once
without touching each route.
"""
from fastapi import Header, HTTPException, Request

from solar_core.config import get_settings
from solar_core.core.ratelimit import RateLimiter

# Module-level limiter, built once from settings. Single-instance store.
_settings = get_settings()
_limiter = RateLimiter(
    limit=_settings.rate_limit_requests,
    window_seconds=_settings.rate_limit_window_seconds,
)


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Render sits behind a proxy, so prefer the
    forwarded header, falling back to the direct peer."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        # First entry is the original client.
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify API key from X-API-Key header, then apply rate limiting.

    Phase 1: simple comma-separated key list in env.
    Phase 2: JWT, OAuth, per-user keys.
    """
    settings = get_settings()
    valid_keys = settings.api_keys_list

    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_error",
                "message": "Missing or invalid API key. Provide X-API-Key header.",
            },
        )

    # Rate limit per (key + IP). A leaked key is throttled per-source, and a
    # single abusive IP can't drain credits even with a valid key.
    if settings.rate_limit_enabled:
        identity = f"{x_api_key}:{_client_ip(request)}"
        allowed, retry_after = _limiter.check(identity)
        _limiter.prune()
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": (
                        f"Too many requests. Limit is "
                        f"{settings.rate_limit_requests} per "
                        f"{settings.rate_limit_window_seconds}s."
                    ),
                },
                headers={"Retry-After": str(retry_after)},
            )

    return x_api_key
