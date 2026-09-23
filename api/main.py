from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from database.sqlite_db import get_jobs, get_job_by_id

app = FastAPI(title="JobScout AI API")

# Minimal CORS for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs", response_model=List[dict])
def read_jobs(
    search: Optional[str] = Query(None, description="Search text in title/company/summary"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    location: Optional[str] = Query(None, description="Filter by location string"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
):
    # Load all jobs from SQLite and apply simple in-memory filters
    jobs = get_jobs("data/jobscout.db")

    def matches_search(j: dict, q: str) -> bool:
        ql = q.lower()
        fields = [j.get('title') or '', j.get('company') or '', j.get('summary') or '']
        return any(ql in (f or '').lower() for f in fields)

    def matches_skill(j: dict, s: str) -> bool:
        s_l = s.lower()
        for sk in (j.get('skills') or []):
            if s_l == (sk or '').lower():
                return True
        return False

    def matches_location(j: dict, loc: str) -> bool:
        return loc.lower() in ((j.get('location') or '').lower())

    filtered = []
    for j in jobs:
        if search and not matches_search(j, search):
            continue
        if skill and not matches_skill(j, skill):
            continue
        if location and not matches_location(j, location):
            continue
        filtered.append(j)

    # Apply pagination
    if skip:
        filtered = filtered[skip:]
    if limit is not None:
        filtered = filtered[:limit]

    return filtered


@app.get("/jobs/{job_id}")
def read_job(job_id: int):
    job = get_job_by_id("data/jobscout.db", job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, log_level="info")
