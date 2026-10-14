import copy
import json
import os
import unittest
from unittest.mock import patch

from meeting_trace.meeting.core import extract, parse_transcript, validate_items
from meeting_trace.meeting.llm import call_model, llm_extract, source_quotes
from meeting_trace.meeting.schema import STAGE_TWO


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.raw = 'Minh: Về phát hành, chốt dùng bản B.\nLan: Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.'
        self.result = extract(self.raw)
        self.turns = self.result['turns']

    def test_bogus_quote_is_quarantined_not_deleted(self):
        item = copy.deepcopy(self.result['items'][0])
        item['evidence'][0]['quote'] = 'Chốt dùng bản C.'
        accepted, review = validate_items([item], self.turns)
        self.assertEqual(accepted, [])
        self.assertEqual(review[0]['item'], item)
        self.assertTrue(review[0]['errors'])

    def test_nonexistent_id_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][0])
        item['evidence'][0]['turn_id'] = 'T999'
        self.assertEqual(len(validate_items([item], self.turns)[1]), 1)

    def test_tampered_history_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][0])
        item['history'][0]['quote'] = 'Phương án chưa từng nói'
        self.assertEqual(len(validate_items([item], self.turns)[1]), 1)

    def test_invented_owner_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][1])
        item['owner'] = 'Minh'
        self.assertEqual(len(validate_items([item], self.turns)[1]), 1)

    def test_invented_deadline_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][1])
        item['due'] = '20/12/2030'
        self.assertEqual(len(validate_items([item], self.turns)[1]), 1)

    def test_empty_evidence_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][0])
        item['evidence'] = []
        self.assertEqual(len(validate_items([item], self.turns)[1]), 1)

    def test_schema_error_and_extra_fields_are_retained(self):
        bad = {'content': 'Chốt ảo', 'password': 'synthetic-test-only'}
        self.assertEqual(validate_items([bad], self.turns)[1][0]['item'], bad)

    def test_duplicate_item_id_is_quarantined(self):
        item = copy.deepcopy(self.result['items'][0])
        valid, review = validate_items([item, item], self.turns)
        self.assertEqual((len(valid), len(review)), (1, 1))

    def test_ok_and_look_do_not_create_assignments(self):
        result = extract('Minh: Đề xuất dùng bản A.\nLan: Ok.\nHuy: Để em xem.')
        self.assertFalse(any(i['type'] in ('decision', 'action') for i in result['items']))

    def test_open_after_confirm_drops_old_decision(self):
        result = extract('Minh: Về giá, chốt giá 100.\nMinh: Về giá, chưa chốt, hoãn để kiểm tra.')
        self.assertFalse(any(i['type'] == 'decision' for i in result['items']))

    def test_proposal_after_confirm_does_not_automatically_override(self):
        result = extract('Minh: Về giá, chốt giá 100.\nLan: Về giá, đề xuất giá 90 cho lần sau.')
        decision = next(i for i in result['items'] if i['type'] == 'decision')
        self.assertIn('100', decision['content'])

    def test_missing_owner_stays_null_and_pending(self):
        result = extract('Minh: Về bảo mật, cần làm kiểm tra quyền.')
        self.assertIsNone(result['items'][0]['owner'])
        self.assertEqual(result['items'][0]['status'], 'needs_confirmation')

    def test_parser_keeps_text_colons_and_source_line(self):
        turns = parse_transcript('\nLan: Về API, yêu cầu dùng URL: /v1.\n')
        self.assertEqual(turns[0]['line'], 2)
        self.assertIn('URL: /v1', turns[0]['text'])

    def test_bad_and_oversized_input_rejected(self):
        for raw in ['', 'Lan:', 'A: ' + 'x'*24001, '\n'.join(['A: x']*301)]:
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(ValueError):
                    parse_transcript(raw)

    def test_plain_mixed_and_anonymous_keep_unknown_identity(self):
        turns = parse_transcript('Em nhận làm kiểm thử.\nLan: Chốt B.\nNgười nói 2: Em nhận sửa lỗi.')
        self.assertEqual([t['speaker'] for t in turns], [None, 'Lan', None])
        self.assertEqual(turns[2]['speaker_label'], 'Người nói 2')
        result = extract('Người nói 2: Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.')
        self.assertEqual((result['items'][0]['owner'], result['items'][0]['status']), (None, 'needs_confirmation'))

    def test_sentence_colon_and_url_do_not_invent_speaker(self):
        for raw in ['Vấn đề: chưa mở quyền sandbox.', 'https://example.test/x', 'Chốt phương án: B.']:
            turn = parse_transcript(raw)[0]
            self.assertIsNone(turn['speaker'])
            self.assertEqual(turn['text'], raw)

    def test_model_references_copy_exact_source_without_generating_quotes(self):
        turns = parse_transcript('Em nhận làm kiểm thử trước thứ Sáu.\nLan: Chốt B nếu pháp chế duyệt.')
        references = [dict(turn_id='T2'), dict(turn_id='T1',kind='assign')]
        quotes = source_quotes(references, turns)
        self.assertEqual([q['quote'] for q in quotes],[turns[1]['text'],turns[0]['text']])
        with self.assertRaises(ValueError): source_quotes([dict(turn_id='T404')], turns)

    def test_pronoun_in_unnamed_utterance_is_not_an_owner_name(self):
        result=extract('Về kiểm thử, Em nhận làm kiểm thử trước thứ Sáu.')
        item=copy.deepcopy(result['items'][0])
        item.update(owner='Em',status='confirmed')
        self.assertEqual(validate_items([item],result['turns'])[0],[])

    def test_no_candidates_does_not_claim_semantic_model_was_called(self):
        with patch('meeting_trace.meeting.llm.llm_extract',return_value=([],[],'test-model')):
            with patch('meeting_trace.meeting.llm.provider_call') as network:
                result=extract('Chưa có thông tin để ghi nhận.','ollama')
                self.assertFalse(result['metadata']['semantic_verification'])
                network.assert_not_called()

    def test_no_key_means_no_network_and_no_fake_llm_result(self):
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.urlopen') as network:
            with self.assertRaises(ValueError):
                call_model('prompt', {}, STAGE_TWO, 'test', 'model')
            network.assert_not_called()

    def test_stage_one_bad_evidence_stops_before_stage_two(self):
        bad = {'topics': [{'topic': 'giá', 'events': [{'turn_id': 'T1', 'kind': 'finalize', 'quote': 'quote ảo'}]}]}
        with patch('meeting_trace.meeting.llm.call_model', return_value=bad) as call:
            with self.assertRaises(ValueError):
                llm_extract(self.turns, model='test-model')
            self.assertEqual(call.call_count, 1)

    def test_mocked_api_payload_and_completed_output(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'status': 'completed', 'output': [{'content': [{'type':'output_text', 'text':'{"items":[]}'}]}]}).encode()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-test-only'}), patch('urllib.request.urlopen', return_value=Response()) as network:
            self.assertEqual(call_model('p', {}, STAGE_TWO, 'test', 'model'), {'items': []})
            payload = json.loads(network.call_args.args[0].data)
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])

    def test_api_incomplete_refusal_and_invalid_json_rejected(self):
        bodies = [dict(status='incomplete'), dict(status='completed', output=[dict(content=[dict(type='refusal')])]),
                  dict(status='completed', output=[dict(content=[dict(type='output_text', text='{')])])]
        for body in bodies:
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self): return json.dumps(body).encode()
            with self.subTest(body=body), patch.dict(os.environ, {'OPENAI_API_KEY':'synthetic-test-only'}), patch('urllib.request.urlopen', return_value=Response()):
                with self.assertRaises(ValueError):
                    call_model('p', {}, STAGE_TWO, 'test', 'model')


if __name__ == '__main__':
    unittest.main()
