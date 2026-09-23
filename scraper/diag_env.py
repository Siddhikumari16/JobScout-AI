import os
from pathlib import Path
from dotenv import find_dotenv, dotenv_values

# Current working directory
cwd = os.getcwd()

# Locate .env using python-dotenv's finder
env_path = find_dotenv()  # returns '' if not found
resolved_env_path = env_path if env_path else str(Path(cwd) / '.env')

# Existence
env_exists = Path(resolved_env_path).exists()

# Parse .env values safely (does not modify environment)
env_file_values = dotenv_values(resolved_env_path) if env_exists else {}
file_has_key = 'OPENAI_API_KEY' in env_file_values and bool(env_file_values.get('OPENAI_API_KEY'))
file_key_length = len(env_file_values.get('OPENAI_API_KEY') or '') if file_has_key else 0

# Check OS environment
os_env_present = 'OPENAI_API_KEY' in os.environ and bool(os.environ.get('OPENAI_API_KEY'))
os_env_key_length = len(os.environ.get('OPENAI_API_KEY') or '') if os_env_present else 0

# Determine if environment overrides .env (non-sensitive check)
env_overrides = False
if os_env_present:
    # If .env missing or empty, env overrides
    if not file_has_key:
        env_overrides = True
    else:
        # If lengths differ, likely different value
        if os_env_key_length != file_key_length:
            env_overrides = True

# Print requested diagnostics (no secrets)
print('cwd:', cwd)
print('resolved_env_path:', resolved_env_path)
print('env_exists:', env_exists)
print('openai_key_in_env_file:', file_has_key)
print('openai_key_length_in_file:', file_key_length)
print('openai_key_in_os_env:', os_env_present)
print('openai_key_length_in_os_env:', os_env_key_length)
print('env_overrides:', env_overrides)
