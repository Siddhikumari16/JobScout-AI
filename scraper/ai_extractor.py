import re
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def rule_based_extract(jd_text):
    jd = jd_text.replace('\n', ' ').strip()
    # Simple heuristics
    title_match = re.search(r"(?i)(?:role|position|title)[:\-]\s*([A-Za-z0-9 _/+-]+)", jd)
    skills = re.findall(r"\b(Java|Python|SQL|Spring|Django|Flask|React|Node|AWS|Docker|Kubernetes|REST|HTML|CSS)\b", jd, re.I)
    exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience)?", jd, re.I)
    location_match = re.search(r"(?i)location[:\-]\s*([A-Za-z ,-]+)", jd)

    result = {
        "title": title_match.group(1).strip() if title_match else None,
        "skills": sorted(set([s.capitalize() for s in skills])),
        "experience_years": int(exp_match.group(1)) if exp_match else None,
        "location": location_match.group(1).strip() if location_match else None,
        "summary": jd[:500]
    }
    return result


SAMPLES_DIR = Path(__file__).parent.parent / "data"
import re
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None


def rule_based_extract(jd_text):
    jd = jd_text.replace('\n', ' ').strip()
    title_match = re.search(r"(?i)(?:role|position|title)[:\-]\s*([A-Za-z0-9 _/+-]+)", jd)
    skills = re.findall(r"\b(Java|Python|SQL|Spring|Django|Flask|React|Node|AWS|Docker|Kubernetes|REST|HTML|CSS|JavaScript)\b", jd, re.I)
    exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience)?", jd, re.I)
    location_match = re.search(r"(?i)location[:\-]\s*([A-Za-z0-9 ,\-]+)", jd)

    result = {
        "title": title_match.group(1).strip() if title_match else None,
        "skills": sorted(set([s.capitalize() for s in skills])),
        "experience_years": int(exp_match.group(1)) if exp_match else None,
        "location": location_match.group(1).strip() if location_match else None,
        "summary": jd[:500]
    }
    return result


def extract_json_from_text(text):
    # find the first JSON object in the text
    start = text.find('{')
    if start == -1:
        return None
    # try to find a matching closing brace by simple heuristic
    stack = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            stack += 1
        elif text[i] == '}':
            stack -= 1
            if stack == 0:
                try:
                    return json.loads(text[start:i+1])
                except Exception:
                    return None
    return None


def llm_extract(jd_text, model="gpt-4o-mini"):
    """Call the OpenAI Chat API to extract structured JSON.
    Falls back to rule-based if OpenAI is not configured.
    """
    # Diagnostic checks: fail loudly with a clear message (no API key value leaked)
    if not OpenAIClient:
        raise RuntimeError("LLM disabled: OpenAI client library not installed or failed to import")
    if not OPENAI_API_KEY:
        raise RuntimeError("LLM disabled: OPENAI_API_KEY not set in environment")

    try:
        # create a client using the provided key (do not print the key)
        client = OpenAIClient(api_key=OPENAI_API_KEY)
        # Load prompt template and schema reference if available
        try:
            prompt_file = Path(__file__).parent / 'llm_prompt.json'
            prompt_json = json.loads(prompt_file.read_text()) if prompt_file.exists() else {}
        except Exception:
            prompt_json = {}

        system = prompt_json.get('system', 'You are an assistant that extracts structured fields from job descriptions.')
        instruction = prompt_json.get('instruction', 'Return only a single JSON object with the keys: title, skills, experience_years, location, summary.')
        schema_ref = prompt_json.get('schema_file')

        system_msg = system + '\n' + instruction
        user = 'Extract fields from the following job posting. Respond only with JSON that conforms to the schema: ' + (schema_ref or 'embedded schema') + '\n\n' + jd_text

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user}],
                temperature=0,
                max_tokens=700,
            )
        except Exception as e:
            # API/network/auth error
            raise RuntimeError(f"OpenAI API request failed: {e}")

        # extract assistant content and parse JSON
        try:
            content = resp['choices'][0]['message']['content']
        except Exception as e:
            raise RuntimeError(f"OpenAI response malformed or missing content: {e}")

        parsed = extract_json_from_text(content)
        if parsed is None:
            # parsing failure: assistant didn't return JSON or returned unexpected text
            raise ValueError("LLM output parsing failed: no JSON object found in assistant response")
        return parsed
    except Exception:
        # re-raise to allow caller to capture diagnostic message
        raise


SAMPLES_DIR = Path(__file__).parent.parent / "data"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_FILE = SAMPLES_DIR / "sample_jds.txt"
if not SAMPLE_FILE.exists():
    SAMPLE_FILE.write_text("""Title: Junior Java Developer\nLocation: Delhi NCR\nExperience: 0-2 years\nSkills: Java, SQL, Spring Boot\n\nWe are looking for a Junior Java Developer with experience in building REST APIs...\n\n---\nTitle: Frontend Engineer\nLocation: Remote\nExperience: 1-3 years\nSkills: React, HTML, CSS, JavaScript\n\nBuild dynamic web UIs...\n""")


def run_on_samples(use_llm=False):
    text = SAMPLE_FILE.read_text()
    blocks = [b.strip() for b in text.split('\n---\n') if b.strip()]
    results = []
    for b in blocks:
        res = None
        if use_llm:
            res = llm_extract(b)
        if not res:
            res = rule_based_extract(b)
        res['original'] = b
        results.append(res)
    out = SAMPLES_DIR / 'extracted.json'
    out.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out}")


if __name__ == '__main__':
    use_llm = bool(OPENAI_API_KEY and openai)
    if use_llm:
        print("OPENAI_API_KEY found — using LLM extraction.")
    else:
        print("OPENAI_API_KEY not found or OpenAI client missing — using rule-based extraction.")
    run_on_samples(use_llm=use_llm)
