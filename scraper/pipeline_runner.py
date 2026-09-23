from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import json
from typing import Any, Dict, Optional

from remotive_adapter import RemotiveAdapter
from ai_extractor import rule_based_extract, llm_extract
from database.sqlite_db import init_db, insert_job
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import time
from typing import Callable


def load_job_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).parent / 'schemas' / 'job_schema.json'
    if not schema_path.exists():
        # try alternate location
        schema_path = Path(__file__).parent.parent / 'scraper' / 'schemas' / 'job_schema.json'
    return json.loads(schema_path.read_text())


def validate_extracted(extracted: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
    try:
        validate(instance=extracted, schema=schema)
        return None
    except ValidationError as e:
        return str(e)


class PipelineRunner:
    def __init__(self, adapter):
        self.adapter = adapter
        self.schema = load_job_schema()

    def run(self, limit: int = 5, use_llm: bool = False) -> Dict[str, Any]:
        items = self.adapter.fetch(limit=limit)
        out = []
        # initialize sqlite DB
        db_path = Path(__file__).parent.parent / 'data' / 'jobscout.db'
        init_db(str(db_path))
        for item in items:
            # build plain text JD for extractor
            parts = []
            if item.get('title'):
                parts.append(f"Title: {item.get('title')}")
            if item.get('company'):
                parts.append(f"Company: {item.get('company')}")
            if item.get('location'):
                parts.append(f"Location: {item.get('location')}")
            parts.append('\n')
            parts.append(item.get('summary') or '')
            jd_text = '\n'.join(parts)


            # Try preferred extractor (LLM optional) with retries, then fallback to rule-based
            parsed = None
            extractor_errors = []
            llm_attempts = 0
            llm_used = False
            fallback_used = False
            if use_llm:
                # small retry/backoff wrapper
                def try_llm():
                    return llm_extract(jd_text)

                max_retries = 3
                backoff = 1.0
                for attempt in range(1, max_retries + 1):
                    llm_attempts = attempt
                    try:
                        parsed = try_llm()
                        if parsed is not None:
                            llm_used = True
                            break
                    except Exception as e:
                        # capture the diagnostic message but redact any direct API key info
                        msg = str(e)
                        extractor_errors.append(f"llm_extract attempt {attempt} error: {msg}")
                        # If error indicates missing API key or client, stop retrying
                        if 'OPENAI_API_KEY not set' in msg or 'OpenAI client library not installed' in msg:
                            break
                    # simple exponential backoff
                    if attempt < max_retries:
                        time.sleep(backoff)
                        backoff *= 2

            if parsed is None:
                try:
                    parsed = rule_based_extract(jd_text)
                    fallback_used = True
                except Exception as e:
                    extractor_errors.append(f"rule_based_extract error: {e}")

            if not isinstance(parsed, dict):
                extractor_errors.append('parsed result not a dict')
                parsed = parsed or {}

            # Validate against JSON Schema
            validation_error = validate_extracted(parsed, self.schema)

            record = {
                'source': 'remotive',
                'url': item.get('url'),
                'title': item.get('title'),
                'company': item.get('company'),
                'location': item.get('location'),
                'extracted': parsed,
                'raw': item.get('raw'),
                'validation_error': validation_error,
                'extractor_errors': extractor_errors,
                'llm_attempts': llm_attempts,
                'llm_used': llm_used,
                'fallback_used': fallback_used,
            }
            out.append(record)

            # Persist validated records to SQLite (avoid storing invalid ones)
            if validation_error is None:
                # Flatten fields for DB insert; prefer extracted values when present
                db_job = {
                    'url': record.get('url'),
                    'title': (parsed.get('title') if isinstance(parsed, dict) and parsed.get('title') else record.get('title')),
                    'company': (parsed.get('company') if isinstance(parsed, dict) and parsed.get('company') else record.get('company')),
                    'location': (parsed.get('location') if isinstance(parsed, dict) and parsed.get('location') else record.get('location')),
                    'skills': parsed.get('skills') if isinstance(parsed, dict) else [],
                    'experience_years': parsed.get('experience_years') if isinstance(parsed, dict) else None,
                    'summary': parsed.get('summary') if isinstance(parsed, dict) and parsed.get('summary') else record.get('raw'),
                    'source': record.get('source'),
                }
                try:
                    inserted = insert_job(str(db_path), db_job)
                    record['db_inserted'] = inserted
                except Exception as e:
                    record['db_insert_error'] = str(e)

        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        out_file = data_dir / 'pipeline_output.json'
        out_file.write_text(json.dumps(out, indent=2))
        return out[0] if out else {}


if __name__ == '__main__':
    adapter = RemotiveAdapter()
    runner = PipelineRunner(adapter)
    # Run 5 jobs using the LLM extractor with rule-based fallback
    first = runner.run(limit=5, use_llm=True)
    print('Raw job (from source):')
    print(json.dumps(first.get('raw', {}), indent=2))
    print('\nLLM / Extracted output:')
    print(json.dumps(first.get('extracted', {}), indent=2))
    print('\nValidation status:')
    print('validation_error:', first.get('validation_error'))
    if first.get('extractor_errors'):
        print('\nExtractor errors:')
        for e in first.get('extractor_errors'):
            print('-', e)