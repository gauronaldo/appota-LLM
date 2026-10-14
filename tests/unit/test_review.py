import copy
import unittest
from unittest.mock import patch

from meeting_trace.meeting.core import extract, parse_transcript
from meeting_trace.meeting.llm import verify_semantics
from meeting_trace.meeting.review import ReviewStore
from meeting_trace.meeting.schema import CHECK_FIELDS


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.result = extract('Minh: Về email, chốt gói B nếu pháp chế duyệt.')
        self.item = self.result['items'][0]
        self.verdict = dict(item_id=self.item['id'], **{key: 'pass' for key in CHECK_FIELDS},
                            reason='Có câu chốt và giữ điều kiện.', evidence=self.item['evidence'])

    def check(self, verdict):
        verdict = {**verdict, 'evidence':[dict(turn_id=ev['turn_id']) for ev in verdict['evidence']]}
        with patch('meeting_trace.meeting.llm.provider_call', return_value=dict(checks=[verdict])):
            return verify_semantics([self.item], self.result['turns'], 'ollama', 'test-model')

    def test_each_failed_or_uncertain_semantic_dimension_blocks_acceptance(self):
        for field in CHECK_FIELDS:
            for value in ['fail', 'uncertain']:
                with self.subTest(field=field,value=value):
                    verdict = {**self.verdict, field:value}
                    accepted, review, checks = self.check(verdict)
                    self.assertEqual(accepted, [])
                    self.assertEqual(review[0]['item'], self.item)
                    self.assertIn(field + ': ' + value, review[0]['errors'])

    def test_checker_hallucinated_evidence_is_not_trusted(self):
        verdict = {**self.verdict, 'evidence':[dict(turn_id='T999',quote='chốt C')]}
        with self.assertRaises(ValueError): self.check(verdict)

    def test_checker_missing_or_duplicate_verdict_aborts(self):
        for checks in [[], [self.verdict,self.verdict]]:
            with patch('meeting_trace.meeting.llm.provider_call', return_value=dict(checks=checks)):
                with self.assertRaises(ValueError):
                    verify_semantics([self.item],self.result['turns'],'ollama','test-model')


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.store = ReviewStore()
        self.original = extract('Lan: Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.')
        self.view = self.store.create(self.original)

    def act(self, action, **kwargs):
        self.view = self.store.act(self.view['session_id'], self.view['revision'], '0', action, **kwargs)

    def export(self):
        return self.store.export(self.view['session_id'],self.view['revision'])

    def test_pending_cannot_export_and_confirmed_can(self):
        with self.assertRaises(ValueError): self.export()
        self.act('confirm')
        approved = self.export()
        self.assertTrue(approved['metadata']['approved'])
        self.assertEqual(approved['automated_snapshot'],self.original)
        self.assertIn('thứ Sáu',approved['minutes_markdown'])

    def test_edit_restore_invalidate_approval_and_audit_preserves_original(self):
        self.act('confirm')
        self.act('edit', changes={'due':None},reason='Chưa đủ chắc về hạn.')
        with self.assertRaises(ValueError): self.export()
        self.act('confirm')
        self.act('remove')
        self.assertEqual(len(self.export()['excluded_items']),1)
        self.act('restore')
        with self.assertRaises(ValueError): self.export()
        self.assertEqual(self.store.get(self.view['session_id'])['original'],self.original)

    def test_local_cannot_approve_contradictory_content_with_literal_evidence(self):
        self.act('edit',changes={'content':'Không cần kiểm thử.'},reason='Probe')
        with self.assertRaises(ValueError): self.act('confirm')
        with self.assertRaises(ValueError): self.export()

    def test_quarantined_item_must_be_resolved_or_removed(self):
        item = copy.deepcopy(self.original['items'][0])
        item['evidence'][0]['quote']='Không tồn tại'
        original = {**self.original,'items':[], 'review_queue':[dict(item=item,errors=['quote sai'])]}
        self.view = self.store.create(original)
        with self.assertRaises(ValueError): self.export()
        with self.assertRaises(ValueError): self.act('confirm')
        self.act('remove')
        self.assertEqual(self.export()['items'],[])

    def test_client_forged_review_state_does_not_approve_server_record(self):
        self.view['items'][0]['human_review']['state']='confirmed'
        self.view['export_ready']=True
        with self.assertRaises(ValueError): self.export()

    def test_stale_revision_cannot_confirm_or_export(self):
        token = self.view['session_id']
        self.act('confirm')
        with self.assertRaises(ValueError): self.store.export(token,0)
        with self.assertRaises(ValueError): self.store.act(token,0,'0','remove')

    def test_llm_edit_is_checked_again_and_bad_verdict_blocks(self):
        original = {**self.original,'metadata':{**self.original['metadata'],'engine':'ollama','model':'test'}}
        self.view=self.store.create(original)
        self.act('edit', changes={'content':'Em nhận làm kiểm thử không cần pháp chế.'},reason='Probe')
        verdict=dict(item_id='I1', **{key:'pass' for key in CHECK_FIELDS},
            reason='Nội dung thêm không có trong evidence.',evidence=[dict(turn_id='T1')])
        verdict['supported'] = 'fail'
        with patch('meeting_trace.meeting.llm.provider_call', return_value=dict(checks=[verdict])):
            with self.assertRaisesRegex(ValueError, 'supported: fail'): self.act('confirm')


if __name__ == '__main__':
    unittest.main()
