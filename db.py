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
            kwargs={'row_factory': dict_row, 'connect_timeout': 10},
            min_size=2,
            max_size=10,
            open=True,
            check=ConnectionPool.check_connection,
            reconnect_timeout=30,
            max_waiting=30,
            max_lifetime=600,
            max_idle=300,
        )
        print("[DB] Connection pool initialised (min=2, max=10)")
    except Exception as e:
        print(f"[DB] Pool init failed, falling back to single connections: {e}")


@contextmanager
def get_db(timeout: float = 5.0):
    if _pool is not None:
        try:
            with _pool.connection(timeout=timeout) as conn:
                yield conn
            return
        except Exception as e:
            print(f"[DB] Pool unavailable ({e}), falling back to direct connection")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


_init_pool()
