import React, { useEffect, useState } from 'react'
import './style.css'

function JobCard({ job }: any) {
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <p className="meta">{job.company} — {job.location}</p>
      <p className="skills">Skills: {(job.skills || []).join(', ')}</p>
      <p className="experience">Experience: {job.experience_years ?? 'N/A'}</p>
      <p className="summary">
  {job.summary?.replace(/<[^>]*>/g, '').slice(0, 200)}...
</p>
      <p className="source">Source: {job.source}</p>
      <a className="view-btn" href={job.url} target="_blank" rel="noreferrer">View Job</a>
    </div>
  )
}

export default function App() {
  const [jobs, setJobs] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [skill, setSkill] = useState('')
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<any>(null)
  const [limit] = useState(5)
  const [skip, setSkip] = useState(0)

  const fetchJobs = async (params: any = {}) => {
    setLoading(true)
    setError(null)
    try {
      const qs = new URLSearchParams(params)
      const res = await fetch(`http://127.0.0.1:8000/jobs?${qs.toString()}`)
      if (!res.ok) throw new Error('API error')
      const data = await res.json()
      setJobs(data)
    } catch (e) {
      setError('Unable to load jobs. Please make sure the FastAPI server is running.')
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs({ limit, skip })
  }, [limit, skip])

  const onSearch = () => {
    const params: any = { limit, skip }
    if (search) params.search = search
    if (skill) params.skill = skill
    if (location) params.location = location
    fetchJobs(params)
  }

  const onClear = () => {
    setSearch('')
    setSkill('')
    setLocation('')
    setSkip(0)
    fetchJobs({ limit: 5, skip: 0 })
  }

  return (
    <div className="container">
      <header>
        <h1>JobScout AI</h1>
        <p className="subtitle">Find and explore software jobs</p>
      </header>

      <div className="controls">
        <input placeholder="Search title/company/keyword" value={search} onChange={e => setSearch(e.target.value)} />
        <input placeholder="Skill (e.g. Python)" value={skill} onChange={e => setSkill(e.target.value)} />
        <input placeholder="Location (e.g. USA)" value={location} onChange={e => setLocation(e.target.value)} />
        <div className="buttons">
          <button onClick={onSearch}>Search</button>
          <button onClick={onClear} className="muted">Clear</button>
        </div>
      </div>

      {loading && <p>Loading jobs...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && jobs.length === 0 && <p>No jobs found.</p>}

      <div className="jobs-grid">
        {jobs.map(j => <JobCard key={j.id} job={j} />)}
      </div>

      <div className="pagination">
        <button onClick={() => setSkip(Math.max(0, skip - limit))} disabled={skip === 0}>Previous</button>
        <button onClick={() => setSkip(skip + limit)}>Next</button>
      </div>
    </div>
  )
}
