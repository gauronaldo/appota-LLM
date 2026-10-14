"""Repository refactors must preserve data, frozen core bytes, and known failures."""
import hashlib
import json
import unittest

from meeting_trace.config import PATHS
from meeting_trace.evaluation.runner import verify_freeze, benchmark_extract
from meeting_trace.evaluation.scoring import score
from meeting_trace.evaluation.revalidate import canonical_hash
from meeting_trace.meeting.core import extract


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PATHS.fixtures / 'dataset_manifest.json').read_text(encoding='utf-8'))

    def test_frozen_core_bytes_unchanged_after_move(self):
        verify_freeze()

    def test_transcript_and_expectation_hashes_unchanged(self):
        for row in self.manifest:
            with self.subTest(case=row['id']):
                raw = (PATHS.examples / (row['id'] + '.txt')).read_text(encoding='utf-8')
                expected = PATHS.fixtures / (row['id'] + '.expected.json')
                self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), row['transcript_sha256'])
                self.assertEqual(hashlib.sha256(expected.read_bytes()).hexdigest(), row['expected_sha256'])

    def test_all_local_outputs_match_saved_baseline(self):
        for row in self.manifest:
            with self.subTest(case=row['id']):
                raw = (PATHS.examples / (row['id'] + '.txt')).read_text(encoding='utf-8')
                saved = PATHS.benchmarks / 'results' / 'local' / (row['id'] + '.json')
                previous = json.loads(saved.read_text(encoding='utf-8'))
                previous.pop('run_seconds', None)
                self.assertEqual(benchmark_extract(raw), previous)

    def test_original_v2_results_and_core_remain_archived(self):
        archive = PATHS.benchmarks / 'baselines' / 'v2-initial'
        freeze = json.loads((archive / 'freeze.json').read_text(encoding='utf-8'))
        for path, sha in freeze['hashes'].items():
            self.assertEqual(hashlib.sha256((archive / path).read_bytes()).hexdigest(), sha)
        for split in ['dev', 'holdout']:
            report = json.loads((archive / 'local' / (split + '_report.json')).read_text(encoding='utf-8'))
            for previous in report['cases']:
                output = json.loads((archive / 'local' / (previous['id'] + '.json')).read_text(encoding='utf-8'))
                expected = json.loads((PATHS.fixtures / (previous['id'] + '.expected.json')).read_text(encoding='utf-8'))
                self.assertEqual(score(output, expected), previous)

    def test_archived_scores_match_current_scoring(self):
        for split in ['dev', 'holdout']:
            report = json.loads((PATHS.benchmarks / 'results' / 'local' / (split + '_report.json')).read_text(encoding='utf-8'))
            for previous in report['cases']:
                case_id = previous['id']
                with self.subTest(case=case_id):
                    output = json.loads((PATHS.benchmarks / 'results' / 'local' / (case_id + '.json')).read_text(encoding='utf-8'))
                    expected = json.loads((PATHS.fixtures / (case_id + '.expected.json')).read_text(encoding='utf-8'))
                    self.assertEqual(score(output, expected), previous)

    def test_example_index_matches_fixture_metadata(self):
        index = json.loads((PATHS.examples / 'index.json').read_text(encoding='utf-8'))
        self.assertEqual(len(index), len(self.manifest))
        for row in index:
            expected = json.loads((PATHS.fixtures / (row['id'] + '.expected.json')).read_text(encoding='utf-8'))
            self.assertEqual(row, {key: expected[key] for key in ['id', 'title', 'group', 'split', 'input_format']})

    def test_live_qwen_provenance_and_postvalidation_do_not_promote_candidates(self):
        archive=PATHS.benchmarks/'baselines/qwen-v2-live'
        frozen=json.loads((archive/'freeze.json').read_text(encoding='utf-8'))
        for path,sha in frozen['hashes'].items():
            saved=archive/'meeting'/path.rsplit('/',1)[-1]
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(),sha)
        for row in self.manifest:
            raw=json.loads((archive/'ollama'/(row['id']+'.json')).read_text(encoding='utf-8'))
            updated=json.loads((PATHS.benchmarks/'results/ollama'/(row['id']+'.json')).read_text(encoding='utf-8'))
            self.assertEqual(updated['postvalidation']['source_canonical_sha256'],canonical_hash(raw))
            self.assertTrue(all(item in raw['items'] for item in updated['items']))
            self.assertEqual(updated.get('semantic_checks'),raw.get('semantic_checks'))
