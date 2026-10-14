"""Saved evaluation provenance and report integrity; never call a model."""
import hashlib
import unittest
from unittest.mock import patch

from meeting_trace.config import PATHS
from meeting_trace.evaluation.comparison import current_hashes
from meeting_trace.evaluation.revalidate import canonical_hash
from meeting_trace.evaluation import submission_report as report


class SubmissionReportTests(unittest.TestCase):
    def test_full_review_coverage_and_saved_source_hashes(self):
        for suite, size in [('v2', 20), ('holdout-v3', 6)]:
            for arm in report.load_suite(suite).values():
                self.assertEqual(arm['report']['total'], size)
                self.assertEqual(len(arm['grades']), size)
        self.assertEqual(report.render(), (PATHS.root/'TESTS.md').read_text(encoding='utf-8'))

    def test_changed_reviewed_output_is_rejected(self):
        original = report.read
        def modified(path):
            data = original(path)
            if path.endswith('/01_change_ab.json'):
                data['metadata']['model'] = 'different-model'
            return data
        with patch.object(report, 'read', side_effect=modified):
            with self.assertRaisesRegex(ValueError, 'Reviewed output changed'):
                report.load_suite('v2')

    def test_final_holdout_frozen_inputs_and_once_only_claims(self):
        suite = 'holdout-v3'
        protocol = report.read(f'{report.BASE}/{suite}/protocol.json')
        manifest = report.read('data/holdout-v3/manifest.json')
        self.assertEqual(protocol['hashes'], current_hashes())
        self.assertEqual(protocol['manifest_sha256'], canonical_hash(manifest))
        self.assertEqual(len(list((PATHS.root/f'{report.BASE}/{suite}/claims').glob('*.json'))), 12)
        for row in manifest:
            raw = (PATHS.root/row['transcript']).read_text(encoding='utf-8')
            self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), row['transcript_sha256'])
            self.assertEqual(hashlib.sha256((PATHS.root/row['expected']).read_bytes()).hexdigest(), row['expected_sha256'])
            for arm in protocol['arms']:
                claim = report.read(f'{report.BASE}/{suite}/claims/{arm}-{row["id"]}.json')
                output = report.read(f'{report.BASE}/{suite}/{arm}/{row["id"]}.json')
                self.assertGreater(claim['started_at'], protocol['at'])
                self.assertEqual(output['comparison_execution']['kind'], 'live_once_no_retry')


if __name__ == '__main__':
    unittest.main()
