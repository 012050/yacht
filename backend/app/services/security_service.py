"""Security helpers: rate limiting and input validation."""
import re

from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Rate limiter ──────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10/minute"],
    strategy="fixed-window",
)

# Per-endpoint overrides:
#   - Auth endpoints: 10/minute per IP
#   - Game endpoints: 30/minute per user
#   - WebSocket connections: 10/minute

# ── Input validation helpers ──────────────────────────────────────────

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")
_NICKNAME_RE = re.compile(r"^[a-zA-Z0-9_\u3130-\uDBFF\uDC00-\uDFFF]+$")
_JOIN_CODE_RE = re.compile(r"^[A-Z0-9]{6}$")


def validate_username(username: str) -> bool:
    """Username: max 20 chars, alphanumeric + underscore."""
    return bool(_USERNAME_RE.match(username)) and len(username) <= 20


def validate_nickname(nickname: str) -> bool:
    """Nickname: max 20 chars, alphanumeric + underscore + Unicode."""
    return bool(_NICKNAME_RE.match(nickname)) and len(nickname) <= 20


def validate_join_code(code: str) -> bool:
    """Join code: exactly 6 uppercase letters or digits."""
    return bool(_JOIN_CODE_RE.match(code))
