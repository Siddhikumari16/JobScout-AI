import sqlite3
from pathlib import Path
import json
from typing import Any, Dict, List, Optional


def init_db(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            company TEXT,
            location TEXT,
            skills TEXT,
            experience_years REAL,
            summary TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def _connect(db_path: str):
    return sqlite3.connect(db_path)


def insert_job(db_path: str, job: Dict[str, Any]) -> bool:
    """Insert a single job. Returns True if inserted, False if duplicate/skipped."""
    conn = _connect(db_path)
    cur = conn.cursor()
    skills = job.get('skills', [])
    # Ensure skills serializable
    try:
        skills_json = json.dumps(skills)
    except Exception:
        skills_json = json.dumps([])

    try:
        cur.execute(
            """
            INSERT INTO jobs (url, title, company, location, skills, experience_years, summary, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.get('url'),
                job.get('title'),
                job.get('company'),
                job.get('location'),
                skills_json,
                job.get('experience_years'),
                job.get('summary'),
                job.get('source'),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate URL or constraint violation
        return False
    finally:
        conn.close()


def insert_jobs(db_path: str, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {'inserted': 0, 'skipped': 0}
    for j in jobs:
        ok = insert_job(db_path, j)
        if ok:
            counts['inserted'] += 1
        else:
            counts['skipped'] += 1
    return counts


def get_jobs(db_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = _connect(db_path)
    cur = conn.cursor()
    q = "SELECT id, url, title, company, location, skills, experience_years, summary, source, created_at FROM jobs ORDER BY id DESC"
    if limit:
        q = q + f" LIMIT {int(limit)}"
    cur.execute(q)
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        skills = []
        try:
            skills = json.loads(r[5] or '[]')
        except Exception:
            skills = []
        out.append(
            {
                'id': r[0],
                'url': r[1],
                'title': r[2],
                'company': r[3],
                'location': r[4],
                'skills': skills,
                'experience_years': r[6],
                'summary': r[7],
                'source': r[8],
                'created_at': r[9],
            }
        )
    return out


def get_job_by_id(db_path: str, job_id: int) -> Optional[Dict[str, Any]]:
    conn = _connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, url, title, company, location, skills, experience_years, summary, source, created_at FROM jobs WHERE id = ?",
        (int(job_id),),
    )
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    try:
        skills = json.loads(r[5] or '[]')
    except Exception:
        skills = []
    return {
        'id': r[0],
        'url': r[1],
        'title': r[2],
        'company': r[3],
        'location': r[4],
        'skills': skills,
        'experience_years': r[6],
        'summary': r[7],
        'source': r[8],
        'created_at': r[9],
    }
