"""
Shared Constants
Common validation patterns and constants used across the backend
"""

import re

# Validation patterns
SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,100}$')
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s\.]{1,500}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
COUNTRY_CODE_PATTERN = re.compile(r'^[A-Z]{2}$')

# Valid transaction channels
VALID_CHANNELS = [
    'wire_transfer',
    'ach',
    'mobile',
    'web',
    'branch',
    'atm',
    'phone'
]

# Size limits
MAX_AUDIO_SIZE_MB = 15
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024

# Field length limits
MAX_ID_LENGTH = 100
MAX_STRING_LENGTH = 200
MAX_TEXT_LENGTH = 1000
MAX_RED_FLAGS = 50
MAX_TRANSACTIONS = 1000
