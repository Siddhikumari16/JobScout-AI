import requests
from pathlib import Path
import json
from typing import List, Dict, Any

from adapter import SourceAdapter

API = 'https://remotive.com/api/remote-jobs'


class RemotiveAdapter(SourceAdapter):
    def fetch(self, limit: int = 10) -> List[Dict[str, Any]]:
        params = {}
        resp = requests.get(API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get('jobs', [])[:limit]
        out = []
        for j in jobs:
            # normalize to job_schema.json keys
            record = {
                'title': j.get('title'),
                'skills': j.get('tags') or [],
                'experience_years': None,
                'location': j.get('candidate_required_location'),
                'summary': j.get('description') or '',
                'url': j.get('url'),
                'company': j.get('company_name'),
                'raw': j,
            }
            out.append(record)
        return out


if __name__ == '__main__':
    adapter = RemotiveAdapter()
    items = adapter.fetch(limit=5)
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / 'remotive_normalized.json'
    out_file.write_text(json.dumps(items, indent=2))
    print('Wrote', out_file)
    for i, it in enumerate(items, 1):
        print(f'[{i}]', it['title'], '@', it.get('company'), '-', it.get('location'))
