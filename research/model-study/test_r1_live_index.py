"""The swap retry of r1_live_index.py (mocked: no database, no Ollama).

    cd research/model-study && ~/.cerebrollm/venv/bin/python -m unittest test_r1_live_index
"""
import unittest
from unittest import mock

import psycopg2
import psycopg2.errors

import r1_live_index as live


class TestSwapRetry(unittest.TestCase):
    def run_with(self, effects):
        fake = mock.Mock(side_effect=effects)
        with mock.patch.object(live, 'original_swap_in', fake), mock.patch.object(live.time, 'sleep') as sleep:
            try:
                result = live.swap_in_with_retry('cfg')
            except Exception as e:                  # noqa: BLE001
                return fake, sleep, e
        return fake, sleep, result

    def test_success_after_a_deadlock(self):
        fake, sleep, result = self.run_with([psycopg2.errors.DeadlockDetected('x'), 'swapped'])
        self.assertEqual(result, 'swapped')
        self.assertEqual(fake.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    def test_exhaustion_after_five_deadlocks(self):
        fake, sleep, error = self.run_with([psycopg2.errors.DeadlockDetected('x')] * 5)
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(fake.call_count, 5)

    def test_other_database_errors_propagate_at_once(self):
        for exc in (psycopg2.errors.UndefinedTable('x'), psycopg2.OperationalError('x'), ValueError('x')):
            with self.subTest(exc=type(exc).__name__):
                fake, sleep, error = self.run_with([exc, 'swapped'])
                self.assertIs(error, exc)
                self.assertEqual(fake.call_count, 1)
                sleep.assert_not_called()

    def test_clean_swap_is_not_retried(self):
        fake, sleep, result = self.run_with(['swapped'])
        self.assertEqual((result, fake.call_count), ('swapped', 1))
        sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
