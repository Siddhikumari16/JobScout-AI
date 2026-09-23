# JobScout AI

Initial project skeleton for JobScout AI — an AI-powered job research and scraping agent.

## Quickstart

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate on Windows:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the basic scraper:

```bash
python scraper/job_scraper.py
```

AI extractor (rule-based):

```
python scraper/ai_extractor.py
```

To enable LLM-based extraction, set `OPENAI_API_KEY` in `.env` and install optional packages from `requirements.txt`.
