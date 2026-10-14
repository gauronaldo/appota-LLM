import copy
import unittest

from meeting_trace.evaluation.runner import benchmark_extract
from meeting_trace.evaluation.scoring import score
from meeting_trace.evaluation.revalidate import revalidate, canonical_hash


class EvaluationTests(unittest.TestCase):
    def test_postvalidation_preserves_model_output_and_truthfully_marks_skipped_check(self):
        original=benchmark_extract('Lan: Về email, chốt B.')
        original['metadata']['engine']='ollama'
        original['metadata']['semantic_verification']=True
        previous=copy.deepcopy(original)
        checked=revalidate(original)
        self.assertEqual(original,previous)
        self.assertEqual(checked['items'],previous['items'])
        self.assertFalse(checked['metadata']['semantic_verification'])
        self.assertEqual(checked['postvalidation']['source_canonical_sha256'],canonical_hash(previous))
    def test_missing_speaker_parses_but_missing_semantic_item_still_fails(self):
        result = benchmark_extract('Lan gửi báo cáo trước thứ Sáu.')
        expected = dict(id='probe',title='Input không nhãn',lesson='Không bỏ qua lỗi input',items=[
            dict(topic='báo cáo',type='action',status='confirmed',contains='gửi báo cáo',
                 owner='Lan',due='thứ Sáu',evidence_turn='T1')],history_turns=[],intermediate_turns=[])
        scored = score(result,expected)
        self.assertNotIn('error',result)
        self.assertIsNone(result['turns'][0]['speaker'])
        self.assertFalse(scored['passed'])
        self.assertIn('Thiếu/sai action',scored['errors'][0])

    def test_dropped_condition_does_not_count_as_correct_decision(self):
        result = benchmark_extract('Minh: Về email, chốt dùng gói B nếu pháp chế duyệt.')
        expected = dict(id='probe',title='Điều kiện',lesson='Giữ điều kiện',items=[
            dict(topic='email',type='decision',status='confirmed',contains='gói B',
                 owner=None,due=None,evidence_turn='T1',conditions=['nếu pháp chế duyệt'])],
            history_turns=[],intermediate_turns=[])
        self.assertEqual(score(result,expected)['metrics']['decision_tp'],1)
        bad = copy.deepcopy(result)
        bad['items'][0]['content'] = 'chốt dùng gói B.'
        self.assertEqual(score(bad,expected)['metrics']['decision_tp'],0)
        self.assertFalse(score(bad,expected)['passed'])
