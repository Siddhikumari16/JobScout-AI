from pathlib import Path
import json

from ai_extractor import extract_json_from_text


def load_prompt():
    p = Path(__file__).parent / 'llm_prompt.json'
    if p.exists():
        return json.loads(p.read_text())
    return {}


def run_demo():
    prompt = load_prompt()
    sample = Path(__file__).parent.parent / 'data' / 'sample_jds.txt'
    text = sample.read_text()
    first = text.split('\n---\n')[0].strip()

    system = prompt.get('system', 'You are an assistant that extracts structured fields from job descriptions.')
    instruction = prompt.get('instruction', 'Return only a single JSON object matching the schema.')
    schema_ref = prompt.get('schema_file', 'schemas/job_schema.json')

    system_msg = system + '\n' + instruction
    user_msg = 'Extract fields from the following job posting. Respond only with JSON that conforms to the schema: ' + schema_ref + '\n\n' + first

    print('---- SYSTEM MESSAGE ----')
    print(system_msg)
    print('\n---- USER MESSAGE ----')
    print(user_msg)

    # Mocked assistant response (JSON only):
    mocked_response = json.dumps({
        "title": "Junior Java Developer",
        "skills": ["Java", "SQL", "Spring Boot"],
        "experience_years": 1,
        "location": "Delhi NCR",
        "summary": "We are looking for a Junior Java Developer with experience in building REST APIs..."
    })

    print('\n---- MOCKED ASSISTANT RESPONSE ----')
    print(mocked_response)

    parsed = extract_json_from_text(mocked_response)
    print('\n---- PARSED JSON OBJECT ----')
    print(json.dumps(parsed, indent=2))


if __name__ == '__main__':
    run_demo()
