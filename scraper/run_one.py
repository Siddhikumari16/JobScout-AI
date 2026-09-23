from remotive_adapter import RemotiveAdapter
from pipeline_runner import PipelineRunner
import json

adapter = RemotiveAdapter()
runner = PipelineRunner(adapter)
first = runner.run(limit=1, use_llm=True)
# Report LLM call status, structured output, and validation (no secrets logged)
if first.get('llm_used'):
    print('LLM API call succeeded')
else:
    errs = first.get('extractor_errors') or []
    # locate a non-sensitive LLM diagnostic if present
    llm_msg = None
    for e in errs:
        if 'llm_extract' in e or 'OpenAI' in e or 'LLM' in e:
            llm_msg = e
            break
    if llm_msg:
        print('LLM diagnostic:', llm_msg)
    else:
        print('LLM not used or no diagnostic message available')

print('\nExtracted structured fields:')
print(first.get('extracted'))

print('\nValidation result:')
print('validation_error:', first.get('validation_error'))
