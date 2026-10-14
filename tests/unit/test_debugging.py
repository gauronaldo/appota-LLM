"""Diagnostics isolate checks and never overwrite or soften benchmark data."""
import copy
import unittest

from meeting_trace.evaluation.debugging import field_ablation, item, oracle
from meeting_trace.evaluation.scoring import score


class DebuggingTests(unittest.TestCase):
    def test_single_field_relaxation_preserves_source_and_other_failures(self):
        row,_=item(raw='Mai: Em nhận gửi báo cáo trước thứ Sáu.')
        actual=dict(items=[row],review_queue=[])
        gold=dict(id='probe',title='Probe',lesson='Probe',history_turns=[],intermediate_turns=[],
            items=[dict(topic='different topic',type='action',contains='gửi báo cáo',conditions=[],
                status='confirmed',owner='Mai',due='thứ Sáu',evidence_turn='T1')])
        snapshots=copy.deepcopy((actual,gold))
        sensitivity=field_ablation(actual,gold)
        self.assertTrue(sensitivity['topic'])
        self.assertFalse(sensitivity['due'])
        self.assertEqual((actual,gold),snapshots)
        gold['items'][0]['conditions']=['sau khi được duyệt']
        self.assertFalse(field_ablation(actual,gold)['topic'])

    def test_supported_owner_is_not_an_independent_invention_measure(self):
        row,_=item(raw='Huy: Mai gửi báo cáo trước thứ Sáu.')
        actual=dict(items=[row],review_queue=[])
        gold=dict(id='probe',title='Probe',lesson='Probe',history_turns=[],intermediate_turns=[],
            items=[dict(topic='báo cáo',type='action',contains='gửi báo cáo',conditions=[],
                status='confirmed',owner='Mai',due='thứ Sáu',evidence_turn='T1')])
        self.assertEqual(score(actual,gold)['metrics']['invented_owner_due'],0)
        row['topic']='Gửi báo cáo đã đối soát'
        self.assertEqual(score(actual,gold)['metrics']['invented_owner_due'],2)
        self.assertEqual(row['owner'],gold['items'][0]['owner'])
        self.assertIn(row['owner'],row['evidence'][0]['quote'])

    def test_oracle_is_explicitly_source_and_label_based(self):
        _,turns=item(raw='Huy: Ngọc gửi CSV sau khi pháp chế xác nhận, trước thứ Năm.')
        gold=dict(items=[dict(type='action',topic='xuất dữ liệu',status='needs_confirmation',
            owner='Ngọc',due='thứ Năm',evidence_turn='T1')],history_turns=['T1'])
        rows=oracle(gold,turns)
        self.assertEqual(rows[0]['content'],turns[0]['text'])
        self.assertEqual(rows[0]['owner'],'Ngọc')
        self.assertIn('not a model prediction',rows[0]['reason'])


if __name__=='__main__': unittest.main()
