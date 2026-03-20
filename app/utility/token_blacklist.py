import time
import threading
from typing import Set, Dict


class TokenBlacklist:
    """In-memory token blacklist for server-side token invalidation.

    Stores blacklisted JTIs (JWT IDs) with their expiry times.
    Automatically cleans up expired entries periodically.
    """

    def __init__(self):
        self._blacklist: Dict[str, float] = {}  # jti -> expiry timestamp
        self._lock = threading.Lock()

    def add(self, jti: str, exp: float) -> None:
        """Add a token JTI to the blacklist with its expiry time."""
        with self._lock:
            self._blacklist[jti] = exp

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        with self._lock:
            return jti in self._blacklist

    def cleanup(self) -> None:
        """Remove expired entries from the blacklist."""
        now = time.time()
        with self._lock:
            expired = [jti for jti, exp in self._blacklist.items() if exp < now]
            for jti in expired:
                del self._blacklist[jti]


token_blacklist = TokenBlacklist()
