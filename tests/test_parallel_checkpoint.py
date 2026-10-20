"""Concurrency and recovery checks use invented texts and mocked providers."""
import csv
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from pipeline.common import SOURCE_FIELDS, configuration, read_json, read_jsonl
from pipeline.providers import Transport, DispatchLimiter
from pipeline.budget import BudgetLedger
from concurrent.futures import ThreadPoolExecutor
from pipeline.runner import run_checkpoint
from test_live_and_contract import mock_provider


class ParallelCheckpointTests(unittest.TestCase):
    def exercise(self, fail=False):
        config = configuration()
        config['workers'] = 2
        lock = threading.Lock()
        state = {'active': 0, 'peak': 0, 'calls': 0}
        real_sleep = time.sleep
        def factory(*args):
            def send(provider, payload):
                with lock:
                    state['active'] += 1
                    state['peak'] = max(state['peak'], state['active'])
                    state['calls'] += 1
                try:
                    real_sleep(.02)
                    if fail and threading.current_thread().name.endswith('_0'):
                        raise RuntimeError('invented worker failure')
                    return mock_provider(provider, payload)
                finally:
                    with lock:
                        state['active'] -= 1
            return Transport(*args, send=send)
        with tempfile.TemporaryDirectory() as temporary, patch('pipeline.providers.time.sleep'):
            root = Path(temporary)
            source = root / 'invented.csv'
            with source.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=SOURCE_FIELDS)
                writer.writeheader()
                for index in range(9):
                    writer.writerow(dict(zip(SOURCE_FIELDS, [str(index), 'Invented complaint '+str(index), '1', '0', '', '2023-01-01'])))
            run = root / 'run'
            if fail:
                with self.assertRaisesRegex(RuntimeError, 'invented worker failure'):
                    run_checkpoint(source, config, run, 'initial', '1', True, 3, factory, {})
                saved = read_json(run / 'checkpoint_latest.json')['completed_ids']
                self.assertEqual(len(saved), 1)
                self.assertEqual(state['calls'], 2)
                self.assertEqual(state['active'], 0)
                return
            first = run_checkpoint(source, config, run, 'initial', '1', True, 3, factory, {})
            self.assertEqual(first['new_unique_results'], 3)
            self.assertEqual(state['calls'], 3)
            before = read_json(run / 'checkpoint_before.json')['completed_ids']
            run_checkpoint(source, config, run, 'resume', '1', True, 3, factory, {})
            self.assertEqual(read_json(run / 'checkpoint_before.json')['completed_ids'], before)
            after = read_json(run / 'checkpoint_after.json')['completed_ids']
            self.assertEqual(len(after), 6)
            calls = [read_json(path) for path in (run / 'attempts').glob('*.json')]
            resumed = [rid for call in calls if call['phase']=='resume' for rid in call['review_ids']]
            self.assertFalse(set(before) & set(resumed))
            self.assertEqual(len({rid for call in calls for rid in call['review_ids']}), 6)
            self.assertEqual(state['peak'], 2)
            measurement = read_json(next((run / 'cost').glob('resume-*/measurement.json')))
            self.assertEqual(measurement['max_workers'], 2)
            self.assertEqual(measurement['budget']['reserved_usd'], '0')

    def test_exact_stop_resume_and_shared_ledger(self):
        self.exercise()

    def test_successful_peer_is_saved_when_other_worker_fails(self):
        self.exercise(fail=True)

    def test_two_connections_cannot_reserve_beyond_shared_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'budget.sqlite'
            initial = BudgetLedger(path, '.01')
            initial.close()
            barrier = threading.Barrier(2)
            def reserve(index):
                ledger = BudgetLedger(path, '.01')
                try:
                    barrier.wait()
                    try:
                        ledger.reserve(str(index), '.006')
                        return True
                    except ValueError:
                        return False
                finally:
                    ledger.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(reserve, range(2)))
            self.assertEqual(sum(results), 1)
            ledger = BudgetLedger(path, '.01')
            self.assertEqual(ledger.snapshot()['reserved_usd'], '0.006')
            ledger.close()

    def test_rate_wait_rejects_expired_deadline_before_reservation(self):
        limiter = DispatchLimiter()
        with self.assertRaisesRegex(ValueError, 'before dispatch'):
            limiter.wait(time.monotonic()-1)
