"""The three study configurations must generate as saved in r1-wsl/, whatever model engine/cerebrollm.toml selects.

    cd research/model-study && ~/.cerebrollm/venv/bin/python -m unittest test_study_configs

Needs no Ollama and no database.
"""
import re
import unittest

from retrieval import OUT, R1, REPO, TABLES, study_config_text


def bge_era(live):
    """The engine file as it was before R1: model bge-m3, no query_prefix."""
    text = re.sub(r'^query_prefix = [^\r\n]*(?:\r?\n)?', '', live, count=1, flags=re.M)
    return re.sub(r'^model = "[^"]*"[^\r\n]*', 'model = "bge-m3"', text, count=1, flags=re.M)


class TestStudyConfigs(unittest.TestCase):
    live = (REPO / 'cerebrollm.toml').read_text()

    def variants(self):
        return {'live file': self.live,
                'bge-m3 era (no prefix)': bge_era(self.live),
                'qwen 4b live model': self.live.replace('model = "qwen3-embedding:0.6b"', 'model = "qwen3-embedding:4b"')}

    def test_each_model_generates_its_saved_config_from_every_engine_variant(self):
        for model, table in TABLES.items():
            saved = (OUT / R1 / f'cerebrollm-{table}.toml').read_text()
            for name, engine in self.variants().items():
                with self.subTest(model=model, engine=name):
                    self.assertEqual(study_config_text(engine, model, table), saved)

    def test_study_config_sets_model_and_table_and_drops_the_prefix(self):
        text = study_config_text(self.live, 'bge-m3', 'study_d_bge_m3')
        self.assertIn('model = "bge-m3"', text)
        self.assertIn('table = "study_d_bge_m3"', text)
        self.assertNotIn('query_prefix', text)
        self.assertNotIn('qwen3-embedding:0.6b', text)

    def test_other_engine_settings_flow_through(self):
        changed = self.live.replace('default_k = 8', 'default_k = 9')
        self.assertIn('default_k = 9', study_config_text(changed, 'bge-m3', 'study_d_bge_m3'))


if __name__ == '__main__':
    unittest.main()
