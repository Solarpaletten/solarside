"""Simple API key authentication for Phase 1."""
from fastapi import Header, HTTPException

from solar_core.config import get_settings


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify API key from X-API-Key header.

    For Phase 1, we use a simple comma-separated list of keys in env.
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
    return x_api_key
