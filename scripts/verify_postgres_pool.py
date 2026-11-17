"""Verify pooled PostgreSQL rollback, connection reuse and concurrent checkout.

Run in the API container with its configured database URL. No secrets are emitted.
"""
from concurrent.futures import ThreadPoolExecutor
import json

from pdm.store import Store


def main():
    store = Store()
    if not store.postgres:
        raise RuntimeError('This verification requires PostgreSQL')
    try:
        def query(_):
            with store.transaction() as connection:
                return store.execute(connection, 'SELECT pg_backend_pid() AS pid, pg_sleep(0.01)').fetchone()['pid']
        reused = [query(index) for index in range(10)]
        try:
            with store.transaction(write=True) as connection:
                store.execute(connection, 'SELECT 1/0')
        except Exception as error:
            if getattr(error, 'sqlstate', None) != '22012':
                raise
        else:
            raise AssertionError('Division error was not raised')
        with store.transaction() as connection:
            assert store.execute(connection, 'SELECT 1 AS ok').fetchone()['ok'] == 1
        with ThreadPoolExecutor(max_workers=20) as executor:
            concurrent = list(executor.map(query, range(40)))
        assert len(set(reused)) < 10
        assert len(set(concurrent)) <= 8
        print(json.dumps({'sequential_transactions': 10, 'sequential_backend_count': len(set(reused)),
                          'concurrent_transactions': 40, 'concurrent_backend_count': len(set(concurrent)),
                          'rollback_recovery': 'passed', 'pool': store.pool_stats()}, indent=2))
    finally:
        store.close()


if __name__ == '__main__':
    main()
