import os
import hashlib
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

_raw = os.environ.get('DATABASE_URL', '')
DATABASE_URL = _raw.replace('postgres://', 'postgresql://', 1) if _raw.startswith('postgres://') else _raw


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


_pool = None

def _init_pool():
    global _pool
    if not DATABASE_URL:
        return
    try:
        from psycopg_pool import ConnectionPool
        _pool = ConnectionPool(
            DATABASE_URL,
            kwargs={'row_factory': dict_row},
            min_size=1,
            max_size=10,
            open=True,
        )
        print("[DB] Connection pool initialised (min=1, max=10)")
    except Exception as e:
        print(f"[DB] Pool init failed, falling back to single connections: {e}")


@contextmanager
def get_db():
    if _pool is not None:
        with _pool.connection() as conn:
            yield conn
    else:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            yield conn


_init_pool()
