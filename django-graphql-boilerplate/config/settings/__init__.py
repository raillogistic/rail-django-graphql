"""
Initialize django-environ at package import time for development convenience.
This allows reading a local `.env` when ENVIRONMENT=development.
"""

import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').lower()
if ENVIRONMENT == 'development':
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        environ.Env.read_env(str(env_file))