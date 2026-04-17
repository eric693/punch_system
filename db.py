import os
import hashlib

import psycopg
from psycopg.rows import dict_row

_raw = os.environ.get('DATABASE_URL', '')
DATABASE_URL = _raw.replace('postgres://', 'postgresql://', 1) if _raw.startswith('postgres://') else _raw


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()
