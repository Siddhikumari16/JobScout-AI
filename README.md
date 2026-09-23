# JobScout AI

JobScout AI is a full-stack job aggregation and search platform that collects job listings, normalizes job data, validates structured records, stores them in SQLite, and provides a searchable web interface.

## 🚀 Features

- Job aggregation using external job APIs
- Adapter-based job data normalization
- Rule-based job information extraction
- Optional LLM-based extraction
- JSON Schema validation
- SQLite database storage
- Duplicate job detection using job URLs
- FastAPI REST API
- Search jobs by keyword
- Filter jobs by skill
- Filter jobs by location
- Pagination support
- React + Vite frontend
- Responsive job listing interface
- Direct links to original job postings

## 🏗️ Architecture

```text
External Job Source
       ↓
Source Adapter
       ↓
Normalized Job Data
       ↓
Job Extraction
       ↓
JSON Schema Validation
       ↓
SQLite Database
       ↓
FastAPI REST API
       ↓
React + Vite Frontend