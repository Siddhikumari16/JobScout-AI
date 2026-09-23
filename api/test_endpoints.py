import requests, json
base = 'http://127.0.0.1:8000/jobs'
scenarios = [
    ({}, 'no-params'),
    ({'search': 'frontend'}, 'search=frontend'),
    ({'skill': 'Python'}, 'skill=Python'),
    ({'location': 'USA'}, 'location=USA'),
    ({'limit': 2, 'skip': 1}, 'limit=2&skip=1'),
]
for params, label in scenarios:
    r = requests.get(base, params=params)
    arr = r.json()
    print(label, '->', len(arr))
    if arr:
        print(json.dumps(arr[0], indent=2)[:1000])
    print('---')
