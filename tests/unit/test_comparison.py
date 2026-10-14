import copy
import unittest
from unittest.mock import patch

from meeting_trace.meeting.baseline import extract_baseline
from meeting_trace.meeting.core import extract
from meeting_trace.evaluation.comparison import execute


class ComparisonTests(unittest.TestCase):
    def test_baseline_uses_one_call_no_gold_no_verifier_and_same_literal_guards(self):
        raw='Lan: Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.'
        row=copy.deepcopy(extract(raw)['items'][0])
        row['evidence']=[dict(turn_id='T1')]
        row['history']=[]
        with patch('meeting_trace.meeting.baseline.provider_call',return_value=dict(items=[row])) as call:
            result=extract_baseline(raw,'ollama','test-model')
        self.assertEqual(call.call_count,1)
        self.assertEqual(set(call.call_args.args[2]),{'turns'})
        self.assertEqual(result['items'][0]['evidence'][0]['quote'],'Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.')
        self.assertFalse(result['metadata']['semantic_verification'])
        self.assertEqual(result['metadata']['model_calls'],1)

    def test_failed_baseline_is_recorded_not_replaced_with_rules(self):
        with patch('meeting_trace.evaluation.comparison.extract_baseline',side_effect=ValueError('Output bị cắt')):
            result=execute('Minh: Chốt B.','baseline_b','ollama','test-model')
        self.assertEqual(result['items'],[])
        self.assertIn('error',result)

    def test_baseline_owner_does_not_pass_literal_guard_when_unsupported(self):
        raw='Người nói 2: Về kiểm thử, em nhận làm kiểm thử.'
        row=copy.deepcopy(extract(raw)['items'][0])
        row.update(owner='Người nói 2',status='confirmed',evidence=[dict(turn_id='T1')],history=[])
        with patch('meeting_trace.meeting.baseline.provider_call',return_value=dict(items=[row])):
            result=extract_baseline(raw,'ollama','test-model')
        self.assertEqual(result['items'],[])
        self.assertTrue(result['review_queue'])
