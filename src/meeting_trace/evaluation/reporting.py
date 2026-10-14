"""Render actual benchmark outcomes; input errors remain failed cases."""
import json

from ..config import PATHS

GROUPS = {'change':'Đổi phương án', 'indirect':'Chốt gián tiếp / cam kết',
          'unresolved':'Chưa thống nhất', 'clear':'Chốt / giao việc rõ'}
FORMATS = {'named':'Có tên', 'labels':'Nhãn ẩn danh', 'plain':'Không có người nói', 'mixed':'Trộn có/không nhãn'}


def render_tests(engine):
    base = PATHS.benchmarks / 'results' / engine
    reports = [json.loads((base / f'{s}_report.json').read_text(encoding='utf-8'))
               for s in ['dev', 'holdout'] if (base / f'{s}_report.json').exists()]
    total = sum(r['total'] for r in reports)
    passed = sum(r['passed'] for r in reports)
    lines = ['# Bộ kiểm thử Mission 2 — suite v2', '',
             f'Bộ đã chạy: **{engine}**. Kết quả thực tế: **{passed}/{total}** case đạt.', '',
             'Suite v2 có 20 hội thoại tiếng Việt tổng hợp, 15–24 lượt mỗi case, chia bốn nhóm × năm case. Mỗi cuộc họp có ngữ cảnh riêng; không chèn chung một đoạn hội thoại nhiễu hoặc bắt mọi câu lặp “Về chủ đề”. Đây không phải transcript thu từ người dùng thật và chưa được người gán nhãn độc lập kiểm tra.', '',
             'Có tên rõ, nhãn Người nói 1/2, không có nhãn và dữ liệu trộn. Giữ nguyên 12 phát triển / 8 kiểm tra lại. Đây là **đánh giá lại bộ đã xem**, không phải tập kín độc lập. Kỳ vọng/hash v2 không đổi. Baseline ban đầu 6/20 và source/freeze cũ được lưu ở data/benchmarks/baselines/v2-initial.', '',
             'Parser nhận transcript thiếu người nói; speaker=null, không biến nhãn ẩn danh thành owner. Lỗi input/API/schema/evidence vẫn ghi Chưa đạt, không loại khỏi mẫu số. Bản LLM có bước kiểm tra nội dung, chủ đề, hiệu lực, điều kiện và giao việc; kết quả fail/uncertain được cách ly.', '',
             'Matching một-một theo loại/chủ đề/nội dung, kiểm tra trạng thái, owner, due, ID evidence và điều kiện được gán nhãn. Matching chuỗi có thể đánh trượt cách diễn đạt tương đương; số liệu không thay thế đánh giá ngữ nghĩa bởi người đọc. Nhãn ẩn danh chưa được coi là tên người nhận đã xác minh.', '',
             'Metric trung gian dựa trên ID và evidence của quyết định sai; một câu chốt bị gắn sai chủ đề vẫn có thể không làm metric này tăng. Xem cả precision/recall và sai lệch từng case.', '',
             ('**Bản quy tắc chưa xác minh đầy đủ ngữ nghĩa.**' if engine == 'local' else '**Báo cáo từ LLM chạy thật; kiểm chứng bằng cùng model vẫn có thể bỏ lọt lỗi.**') + ' Chấm tự động có thể đánh trượt cách diễn đạt tương đương. Chưa đo thời gian PM duyệt hoặc baseline LLM A/B/C.', '']
    for r in reports:
        m = r['metrics']
        lines += [f'## {"Phát triển" if r["split"] == "dev" else "Kiểm tra lại (split holdout cũ)"}', '',
                  f'Đạt **{r["passed"]}/{r["total"]}**; decision precision **{m["decision_precision"]}**, recall **{m["decision_recall"]}**. TP/FP/FN: {m["decision_tp"]}/{m["decision_fp"]}/{m["decision_fn"]}. '
                  f'Trung gian nâng sai: {m["intermediate_promoted"]}/{m["intermediate_total"]}; owner/due ngoài kỳ vọng: {m["invented_owner_due"]}.', '',
                  f'Run UTC: {r["run_at"]}; dataset {r["dataset_version"]}; prompt {r["prompt_version"]}; model {r["model"]}.', '']
        if r.get('postvalidation'):
            lines += ['', 'Hậu kiểm code trên output LLM đã lưu, không gọi model mới và không nâng mục cách ly thành hợp lệ. Core hashes trong report gốc thuộc lượt inference; postvalidation.core_hashes thuộc guard hiện tại. Output/source/freeze inference gốc được giữ tại data/benchmarks/baselines/qwen-v2-live.', '',
                      ]
        lines += ['| Nhóm | Đạt / tổng |', '| --- | --- |']
        lines += [f'| {GROUPS.get(g,g)} | {v["passed"]}/{v["total"]} |' for g,v in r['groups'].items()]
        lines += ['', '| Dữ liệu người nói | Đạt / tổng |', '| --- | --- |']
        lines += [f'| {FORMATS.get(g,g)} | {v["passed"]}/{v["total"]} |' for g,v in r['input_formats'].items()]
        lines.append('')
        for c in r['cases']:
            lines += [f'### {c["id"]} — {c["title"]}', '',
                      f'- **Kỳ vọng:** {c["expectation"]}',
                      f'- **Kết quả thực tế:** {c["actual"]}',
                      f'- **Đạt/Chưa đạt:** {"Đạt" if c["passed"] else "Chưa đạt"}',
                      f'- **Điều học được:** {c["lesson"]}', '']
            if c['errors']:
                lines += ['Sai lệch: ' + '; '.join(c['errors']), '']
    target = PATHS.reports / ('TESTS.md' if engine == 'local' else f'TESTS_{engine.upper()}.md')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8', newline='\n')
