"""SQLite storage for the registry app.

SQLite rather than Postgres, deliberately. The registry receives maybe a few
hundred submissions a year; a separate database service would add an operational
surface without adding capability. Backup is copying one file, and if the load
ever justifies Postgres the migration is mechanical.

The authoritative records still live on disk as frozen JSON with their hashes
and OpenTimestamps proofs. This database is an index over them plus a queue of
submissions — if it were lost entirely, nothing that has been proven is lost.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS submission (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    token         TEXT UNIQUE NOT NULL,
    email         TEXT,
    name          TEXT NOT NULL,
    family        TEXT NOT NULL,
    definition    TEXT NOT NULL,
    parameters    TEXT NOT NULL,
    market        TEXT NOT NULL,
    rationale     TEXT,
    status        TEXT NOT NULL DEFAULT 'queued',
    reviewer_note TEXT,
    sweep_id      TEXT,
    created_utc   TEXT NOT NULL,
    updated_utc   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS submission_status_idx ON submission(status);

CREATE TABLE IF NOT EXISTS vote (
    submission_id INTEGER NOT NULL REFERENCES submission(id),
    voter         TEXT NOT NULL,
    created_utc   TEXT NOT NULL,
    PRIMARY KEY (submission_id, voter)
);
"""

STATUSES = ("queued", "accepted", "rejected", "running", "published")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def submit(conn, *, name, family, definition, parameters, market,
           rationale=None, email=None) -> dict:
    token = secrets.token_urlsafe(16)
    ts = now()
    cur = conn.execute(
        """INSERT INTO submission
           (token,email,name,family,definition,parameters,market,rationale,
            created_utc,updated_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (token, email, name, family, definition,
         json.dumps(parameters, ensure_ascii=False), market, rationale, ts, ts))
    conn.commit()
    return {"id": cur.lastrowid, "token": token}


def by_token(conn, token: str):
    return conn.execute("SELECT * FROM submission WHERE token=?", (token,)).fetchone()


def queue(conn, status: str | None = None, limit: int = 200):
    q = ("SELECT s.*, (SELECT COUNT(*) FROM vote v WHERE v.submission_id=s.id) "
         "AS votes FROM submission s")
    args: tuple = ()
    if status:
        q += " WHERE s.status=?"
        args = (status,)
    q += " ORDER BY votes DESC, s.created_utc ASC LIMIT ?"
    return conn.execute(q, args + (limit,)).fetchall()


def set_status(conn, sub_id: int, status: str, note: str | None = None,
               sweep_id: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    conn.execute(
        "UPDATE submission SET status=?, reviewer_note=COALESCE(?,reviewer_note),"
        " sweep_id=COALESCE(?,sweep_id), updated_utc=? WHERE id=?",
        (status, note, sweep_id, now(), sub_id))
    conn.commit()


def vote(conn, sub_id: int, voter: str) -> bool:
    """One vote per voter per submission. Returns False if already voted."""
    try:
        conn.execute("INSERT INTO vote (submission_id,voter,created_utc) VALUES (?,?,?)",
                     (sub_id, voter, now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def counts(conn) -> dict:
    rows = conn.execute(
        "SELECT status, COUNT(*) n FROM submission GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}
