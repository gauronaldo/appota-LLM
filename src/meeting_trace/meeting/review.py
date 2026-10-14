"""Authoritative, in-memory review workflow for the local MVP.

An edit invalidates approval; export never trusts client-supplied review states.
Sessions expire on server restart or after two hours. This is not authentication.
"""
import copy
import hashlib
import json
import secrets
import threading
import time
from datetime import datetime, timezone

from .core import check_candidates, validate_items


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(item):
    return hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ReviewStore:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def create(self, result):
        with self.lock:
            self.sessions = {k: v for k, v in self.sessions.items() if time.monotonic()-v['created'] < 7200}
            if len(self.sessions) >= 64:
                raise ValueError('Đã có 64 phiên; khởi động lại server để giải phóng phiên cũ.')
            token = secrets.token_urlsafe(32)
            records = []
            for item in result['items']:
                records.append(dict(item=copy.deepcopy(item), errors=[], state='pending'))
            for row in result['review_queue']:
                records.append(dict(item=copy.deepcopy(row['item']), errors=list(row['errors']), state='pending'))
            for index, record in enumerate(records):
                record.update(key=str(index), at=None, approved_digest=None, checks=[])
            session = dict(original=copy.deepcopy(result), records=records, audit=[], revision=0,
                           created=time.monotonic(), lock=threading.Lock())
            self.sessions[token] = session
        return self.view(token, session)

    def get(self, token):
        if not isinstance(token, str):
            raise ValueError('Thiếu phiên duyệt.')
        with self.lock:
            session = self.sessions.get(token)
        if not session or time.monotonic()-session['created'] > 7200:
            raise ValueError('Phiên không tồn tại/hết hạn; hãy phân tích lại transcript.')
        return session

    def view(self, token, session):
        result = copy.deepcopy(session['original'])
        result.update(session_id=token, revision=session['revision'], items=[], review_queue=[])
        for record in session['records']:
            item = copy.deepcopy(record['item'])
            item.update(review_key=record['key'], human_review=dict(state=record['state'], at=record['at']))
            if record['errors'] and record['state'] != 'removed':
                result['review_queue'].append(dict(item=item, errors=list(record['errors'])))
            else:
                result['items'].append(item)
        result['review_audit'] = copy.deepcopy(session['audit'])
        result['export_ready'] = not result.get('error') and all(
            r['state'] in ('confirmed', 'removed') for r in session['records'])
        return result

    def act(self, token, revision, key, action, changes=None, reason=''):
        session = self.get(token)
        with session['lock']:
            if revision != session['revision']:
                raise ValueError('Phiên đã thay đổi; nạp lại kết quả trước khi duyệt.')
            record = next((r for r in session['records'] if r['key'] == key), None)
            if record is None:
                raise ValueError('Mục duyệt không tồn tại.')
            before = copy.deepcopy(record['item'])
            original = session['original']
            if action == 'edit':
                allowed = {'topic', 'type', 'status', 'content', 'owner', 'due', 'evidence'}
                if not isinstance(changes, dict) or not changes or set(changes)-allowed or not reason.strip():
                    raise ValueError('Sửa cần các trường hợp lệ và lý do.')
                item = {**before, **copy.deepcopy(changes)}
                _, errors = validate_items([item], original['turns'], semantic_checked=original['metadata']['engine'] != 'local')
                record['item'] = item
                record['errors'] = [e for q in errors for e in q['errors']]
                record['state'] = 'edited'
            elif action == 'confirm':
                if record['state'] == 'removed':
                    raise ValueError('Khôi phục mục trước khi xác nhận.')
                _, errors, checks = check_candidates([before], original['turns'],
                    original['metadata']['engine'], original['metadata']['model'])
                if errors:
                    raise ValueError('Chưa thể duyệt: ' + '; '.join(e for q in errors for e in q['errors']))
                record.update(state='confirmed', errors=[], approved_digest=digest(before), checks=checks)
            elif action in ('remove', 'restore'):
                record['state'] = 'removed' if action == 'remove' else 'pending'
            else:
                raise ValueError('Thao tác duyệt không hợp lệ.')
            if action != 'confirm':
                record['approved_digest'] = None
                record['checks'] = []
            record['at'] = now()
            session['audit'].append(dict(review_key=key, item_id=before.get('id'), action=action,
                at=record['at'], before=before, after=copy.deepcopy(record['item']), reason=reason))
            session['revision'] += 1
            return self.view(token, session)

    def export(self, token, revision):
        session = self.get(token)
        with session['lock']:
            if revision != session['revision']:
                raise ValueError('Phiên đã thay đổi; hãy nạp lại trước khi xuất.')
            original = session['original']
            if original.get('error'):
                raise ValueError('Pipeline thất bại; không có bản ghi hợp lệ để xuất.')
            active = [r for r in session['records'] if r['state'] != 'removed']
            if any(r['state'] != 'confirmed' or r['approved_digest'] != digest(r['item']) for r in active):
                raise ValueError('Phải xác nhận từng mục hoặc loại bỏ; mục vừa sửa cần duyệt lại.')
            items = [copy.deepcopy(r['item']) for r in active]
            _, errors = validate_items(items, original['turns'], semantic_checked=original['metadata']['engine'] != 'local')
            if errors:
                raise ValueError('Không xuất: có mục sai schema/evidence hoặc trùng ID.')
            for item, record in zip(items, active):
                item['human_review'] = dict(state='confirmed', at=record['at'])
            result = dict(schema_version=original['schema_version'], metadata={**original['metadata'],
                'approved': True, 'approved_at': now(), 'human_changes': bool(session['audit']),
                'verification_after_review': 'llm_judgment' if original['metadata']['engine'] != 'local' else 'literal_rules'},
                turns=copy.deepcopy(original['turns']), items=items, review_queue=[],
                excluded_items=[copy.deepcopy(r['item']) for r in session['records'] if r['state'] == 'removed'],
                review_audit=copy.deepcopy(session['audit']), automated_snapshot=copy.deepcopy(original),
                semantic_checks=[c for r in active for c in r['checks']])
            lines = ['# Biên bản đã duyệt', '', f'Duyệt lúc: {result["metadata"]["approved_at"]}', '']
            for item in items:
                lines += [f'## {item["topic"]} · {item["type"]}', '', item['content'], '',
                          f'Trạng thái: {item["status"]}; người nhận: {item["owner"] or "chưa biết"}; hạn: {item["due"] or "chưa biết"}', '']
                lines += [f'- {ev["turn_id"]}: {ev["quote"]}' for ev in item['evidence']]
                lines.append('')
            result['minutes_markdown'] = '\n'.join(lines)
            return result
