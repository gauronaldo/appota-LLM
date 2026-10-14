import hashlib
import json
import unittest

from meeting_trace.config import PATHS
from meeting_trace.meeting.core import parse_transcript


class FreshHoldoutTests(unittest.TestCase):
    def test_six_labels_exist_before_inference_and_match_evidence(self):
        manifest=json.loads((PATHS.root/'data/holdout-v3/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest),6)
        for row in manifest:
            with self.subTest(case=row['id']):
                raw=(PATHS.root/row['transcript']).read_text(encoding='utf-8')
                path=PATHS.root/row['expected']
                gold=json.loads(path.read_text(encoding='utf-8'))
                self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),row['transcript_sha256'])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['expected_sha256'])
                self.assertTrue(gold['authored_before_inference'])
                turns=parse_transcript(raw)
                self.assertEqual(len(turns),18)
                lookup={turn['id']:turn['text'] for turn in turns}
                for item in gold['items']:
                    text=lookup[item['evidence_turn']]
                    self.assertIn(item['contains'].casefold(),text.casefold())
                    for condition in item['conditions']:
                        self.assertIn(condition.casefold(),text.casefold())
                    if item['due']: self.assertIn(item['due'],text)
