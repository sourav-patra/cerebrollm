"""Tests for r2_wsl.py (guard stops a unit) and r2_report.py (exact 100% GPU rule). No model is called."""
import subprocess
import sys
import unittest
from unittest import mock

import r2_report
import r2_wsl


class GuardStopsUnit(unittest.TestCase):
    def setUp(self):  # never write into the saved r2-wsl records
        patch = mock.patch.object(r2_wsl, 'append')
        patch.start()
        self.addCleanup(patch.stop)

    def run_guard(self, rc):
        return mock.patch.object(r2_wsl.subprocess, 'run', return_value=subprocess.CompletedProcess([], rc, '', 'refused'))

    def test_refused_pull_stops_correctness_before_inference(self):
        for rc in (1, 2):
            with self.run_guard(rc), mock.patch.object(r2_wsl, 'code_unit') as code, mock.patch.object(r2_wsl, 'tools_unit') as tools, \
                    mock.patch.object(r2_wsl, 'snapshot') as snap:
                with self.assertRaises(SystemExit):
                    r2_wsl.correctness('phi4')
            code.assert_not_called(); tools.assert_not_called(); snap.assert_not_called()

    def test_refused_pull_stops_speed_before_inference(self):
        with self.run_guard(2), mock.patch.object(r2_wsl, 'speed_unit') as unit, mock.patch.object(r2_wsl, 'ps_models') as ps:
            with self.assertRaises(SystemExit):
                r2_wsl.speed('phi4')
        unit.assert_not_called(); ps.assert_not_called()

    def test_failed_unload_is_not_ignored(self):
        calls = []
        def fake(cmd, **kw):
            calls.append(cmd[3])
            return subprocess.CompletedProcess(cmd, 0 if cmd[3] == 'pull' else 1, '', '')
        with mock.patch.object(r2_wsl.subprocess, 'run', side_effect=fake), mock.patch.object(r2_wsl, 'code_unit'), \
                mock.patch.object(r2_wsl, 'tools_unit'), mock.patch.object(r2_wsl, 'snapshot', return_value={}), mock.patch.object(r2_wsl, 'append'):
            with self.assertRaises(SystemExit):
                r2_wsl.correctness('phi4')
        self.assertEqual(calls, ['pull', 'unload'])

    def test_good_guard_returns_zero(self):
        with self.run_guard(0):
            self.assertEqual(r2_wsl.guard('check-empty'), 0)


def row(model, mode, gen, gpu, combined=90.0, code=90.0):
    return {'model': model, 'mode': mode, 'combined': combined, 'code_pct': code, 'gen_tps_8000': gen, 'gpu_pct_8000': gpu}


def rows(gpu):
    return [row(m, mode, 30.0, gpu) for m, mode in r2_report.CORE]


class Rules(unittest.TestCase):
    def test_99_9_percent_gpu_does_not_qualify(self):
        self.assertIsNone(r2_report.apply_rules(rows(99.9))['r2a'])
        self.assertIsNone(r2_report.apply_rules(rows(99.5))['r2a'])

    def test_exactly_100_percent_gpu_qualifies(self):
        self.assertIsNotNone(r2_report.apply_rules(rows(100.0))['r2a'])

    def test_slow_model_at_100_percent_does_not_qualify(self):
        rs = rows(100.0)
        for r in rs:
            r['gen_tps_8000'] = 14.9
        self.assertIsNone(r2_report.apply_rules(rs)['r2a'])

    def test_closest_text_names_each_failed_gate(self):
        rs = rows(80.0)
        rs[0]['gen_tps_8000'] = 10.0
        text = [x for x in r2_report.apply_rules(rs)['log'] if x.startswith('R2a closest')][0]
        self.assertIn('fails: generation below 15 tok/s and GPU below 100%', text)
        self.assertIn('fails: GPU below 100%)', text)


    def test_r10_drops_gpu_gate_but_keeps_speed_gate(self):
        self.assertIsNone(r2_report.apply_rules(rows(71.0))['r2a'])
        self.assertIsNotNone(r2_report.apply_rules(rows(71.0), r10=True)['r2a'])
        rs = rows(71.0)
        for r in rs:
            r['gen_tps_8000'] = 14.9
        self.assertIsNone(r2_report.apply_rules(rs, r10=True)['r2a'])


class M3Modes(unittest.TestCase):
    def test_mtp_draft_length_and_thinking_switch(self):
        import study
        q = 'qwen3.6:35b-a3b-coding-mtp-q4_K_M'
        self.assertEqual(study.extra_options(q, 'mtp4-think-off'), {'draft_num_predict': 4})
        self.assertEqual(study.extra_options(q, 'mtp0-think-off'), {'draft_num_predict': 0})
        self.assertEqual(study.mode_args(q, 'mtp0-think-off'), {'think': False})
        self.assertEqual(study.extra_options('gpt-oss:20b', 'low'), {})
        self.assertEqual(study.mode_args('glm-4.7-flash:q4_K_M', 'think-off'), {'think': False})
        self.assertEqual(set(r2_wsl.MODES[q]), {'mtp4-think-off', 'mtp0-think-off'})

    def test_memory_gate_needs_five_paging_samples_in_a_row(self):
        import m3_speed
        def rows(pps, free=5000):
            return [{'pages_per_sec': p, 'free_mb': free, 'available_mb': free} for p in pps]
        self.assertFalse(m3_speed.summarise(rows([2000, 2000, 10, 2000, 2000, 2000, 2000]))['sustained_paging'])
        self.assertTrue(m3_speed.summarise(rows([2000] * 5))['sustained_paging'])
        self.assertFalse(m3_speed.summarise(rows([1], free=2048))['free_ok'])
        self.assertTrue(m3_speed.summarise(rows([1], free=2049))['free_ok'])


if __name__ == '__main__':
    unittest.main()
