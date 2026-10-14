"""Optional real OpenAI Responses API adapter; not used by local runs.

No SDK dependency. No key saved, printed, or accepted in browser payloads.
"""
import json
import os
import urllib.error
import urllib.request

from .core import validate_topics
from .prompts import STAGE_ONE_PROMPT, STAGE_TWO_PROMPT
from .schema import STAGE_ONE, STAGE_TWO


def call_model(prompt, data, schema, name, model):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise ValueError('Chưa có OPENAI_API_KEY. Hãy dùng chế độ local hoặc đặt key ở biến môi trường.')
    payload = dict(model=model, store=False, max_output_tokens=10000,
                   input=[dict(role='system', content=prompt),
                          dict(role='user', content=json.dumps(data, ensure_ascii=False))],
                   text=dict(format=dict(type='json_schema', name=name, strict=True, schema=schema)))
    req = urllib.request.Request('https://api.openai.com/v1/responses',
                                 data=json.dumps(payload).encode(), method='POST',
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Never print response bodies or headers which may contain private data.
        raise ValueError(f'OpenAI HTTP {error.code}: kiểm tra model, key, quota và quyền API.') from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Không kết nối được OpenAI hoặc đã hết thời gian chờ. Không tạo kết quả thay thế.') from None
    if result.get('status') != 'completed':
        raise ValueError('API chưa hoàn tất; không sử dụng JSON bị cắt ngắn.')
    chunks = []
    for output in result.get('output', []):
        for content in output.get('content', []):
            if content.get('type') == 'refusal':
                raise ValueError('Model từ chối xử lý. Không tạo dữ liệu thay thế.')
            if content.get('type') == 'output_text':
                chunks.append(content['text'])
    try:
        return json.loads(''.join(chunks))
    except (ValueError, TypeError):
        raise ValueError('API không trả JSON hợp lệ.') from None


def llm_extract(turns, model=None):
    model = model or os.environ.get('OPENAI_MODEL', '').strip()
    if not model:
        raise ValueError('Đặt OPENAI_MODEL thành model tài khoản của bạn được quyền dùng, hỗ trợ Structured Outputs.')
    stage_one = call_model(STAGE_ONE_PROMPT, {'turns': turns}, STAGE_ONE, 'meeting_events', model)
    if not isinstance(stage_one, dict) or 'topics' not in stage_one:
        raise ValueError('Bước 1 thiếu topics.')
    topics = stage_one['topics']
    validate_topics(topics, turns)
    stage_two = call_model(STAGE_TWO_PROMPT, {'turns': turns, 'topics': topics}, STAGE_TWO, 'meeting_items', model)
    if not isinstance(stage_two, dict) or not isinstance(stage_two.get('items'), list):
        raise ValueError('Bước 2 thiếu items. Không tạo dữ liệu thay thế.')
    return topics, stage_two['items'], model
