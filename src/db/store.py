import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Default to a "data" folder next to src/ so the DB survives container restarts
# when that folder is mounted as a volume (see docker-compose.yml).
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ticket_router.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH)))

PBKDF2_ITERATIONS = 200_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text               TEXT NOT NULL,
    category           TEXT NOT NULL,
    priority           TEXT NOT NULL,
    confidence         INTEGER NOT NULL,
    source             TEXT NOT NULL,
    summary            TEXT NOT NULL DEFAULT '',
    suggested_response TEXT NOT NULL DEFAULT '',
    created_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id, id DESC);
"""


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _password_matches(password: str, stored: str) -> bool:
    try:
        _algo, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_user(username: str, password: str) -> dict:
    """Register a new account. Returns {"user": {...}} or {"error": "..."}."""
    username = username.strip()
    if len(username) < 3:
        return {"error": "Username must be at least 3 characters."}
    if len(password) < 6:
        return {"error": "Password must be at least 6 characters."}

    with _connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), _now()),
            )
        except sqlite3.IntegrityError:
            return {"error": "That username is already taken."}
        return {"user": {"id": cur.lastrowid, "username": username}}


def verify_user(username: str, password: str) -> dict:
    """Check credentials. Returns {"user": {...}} or {"error": "..."}."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if row is None or not _password_matches(password, row["password_hash"]):
        return {"error": "Invalid username or password."}
    return {"user": {"id": row["id"], "username": row["username"]}}


def user_exists(user_id: int) -> bool:
    """A browser session can outlive its account (e.g. after `docker compose down -v`)."""
    with _connect() as conn:
        return conn.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ).fetchone() is not None


def add_ticket(user_id: int, text: str, result: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO tickets
                (user_id, text, category, priority, confidence, source,
                 summary, suggested_response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                text,
                result["category"],
                result["priority"],
                result["confidence"],
                result.get("source", "unknown"),
                result.get("summary", ""),
                result.get("suggested_response", ""),
                _now(),
            ),
        )


def get_history(user_id: int) -> list:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT created_at, text, category, priority, confidence, source,
                   summary, suggested_response
            FROM tickets WHERE user_id = ? ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_history(user_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM tickets WHERE user_id = ?", (user_id,))
