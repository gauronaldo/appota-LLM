"""Render the public submission report from saved results and disclosed reviews.

No model calls, rescoring, label changes or inference retries.
"""
import argparse
import json
from html import escape

from ..config import PATHS
from .revalidate import canonical_hash

BASE = 'data/benchmarks/comparisons/qwen2.5-7b'
REVIEWS = 'data/benchmarks/reviews'


def read(relative):
    return json.loads((PATHS.root / relative).read_text(encoding='utf-8'))


def text(value):
    return escape(str(value)).replace('\n', ' ')


def load_suite(suite):
    arms = {}
    for arm in ['baseline_b', 'pipeline']:
        report = read(f'{BASE}/{suite}/{arm}_report.json')
        review = read(f'{REVIEWS}/{suite}_{arm}.json')
        if not report['completed'] or report['total'] != report['expected_total']:
            raise ValueError('Benchmark incomplete: ' + suite + '/' + arm)
        scores = {row['id']: row for row in report['cases']}
        grades = {row['id']: row for row in review['cases']}
        if len(scores) != report['total'] or set(scores) != set(grades) or len(grades) != review['total']:
            raise ValueError('Review coverage mismatch: ' + suite + '/' + arm)
        if review['semantic_passed'] != sum(row['semantic_pass'] for row in grades.values()):
            raise ValueError('Review count mismatch')
        if review['independent'] or review['human_performed'] or not review['authorized_by_author']:
            raise ValueError('Reviewer attribution changed')
        outputs = {}
        for id, grade in grades.items():
            result = read(grade['source'])
            if canonical_hash(result) != grade['source_canonical_sha256']:
                raise ValueError('Reviewed output changed: ' + id)
            outputs[id] = result
        arms[arm] = dict(report=report, review=review, scores=scores, grades=grades, outputs=outputs)
    if set(arms['baseline_b']['scores']) != set(arms['pipeline']['scores']):
        raise ValueError('Arm coverage mismatch')
    return arms


def describe_item(item):
    refs = ', '.join(ev['turn_id'] for ev in item['evidence']) or 'không có'
    history = ', '.join(ev['turn_id'] for ev in item['history']) or 'không có'
    return (f"{text(item['type'])}/{text(item['topic'])}: {text(item['content'])} "
            f"({text(item['status'])}; người={text(item['owner'])}; hạn={text(item['due'])}). "
            f"Evidence: {text(refs)}. Diễn biến: {text(history)}.")


def render():
    suites = {suite: load_suite(suite) for suite in ['v2', 'holdout-v3']}
    lines = ['# Bộ kiểm thử Mission 2', '',
        'Sinh bằng `python src report` từ JSON đã lưu. Không gọi model hoặc thay kỳ vọng.', '',
        '## Kết quả và người chấm', '',
        '| Bộ dữ liệu | Cấu hình | Chấm tự động, toàn case | Đọc ngữ nghĩa, toàn case |',
        '| --- | --- | --- | --- |']
    for suite, arms in suites.items():
        for arm, data in arms.items():
            report, review = data['report'], data['review']
            label = 'B: một prompt' if arm == 'baseline_b' else 'C: pipeline ba bước'
            lines.append(f"| {suite} | {label} | {report['passed']}/{report['total']} | {review['semantic_passed']}/{review['total']} |")
    lines += ['',
        '**Người chấm đọc: Codex/AI được tác giả ủy quyền. Không độc lập, không phải chấm bởi người thật.** '
        'Đã đọc transcript, nhãn kỳ vọng, kết quả và candidates cách ly; không hỏi Qwen để chấm. '
        'Ngữ nghĩa có thể đạt khi candidate đúng nhưng chưa thành item hợp lệ. Vì thế 8/20 và 5/20 không phải tỷ lệ dữ liệu dùng được sau duyệt. '
        '`ready_without_edit` trong JSON đo tuân thủ đầy đủ hợp đồng fixture, không đo thao tác xuất của người dùng.', '',
        'Điểm tự động giữ nguyên: đối chiếu một-một type/topic/chuỗi nội dung/status/owner/due/evidence/conditions/history, '
        'có mục cách ly hoặc dư thì trượt. Chấm đọc cho phép tên cùng đối tượng/cách viết tương đương, '
        'nhưng không tha lỗi trạng thái, sai chủ đề, mất điều kiện, thiếu việc hoặc evidence không hỗ trợ kết luận cuối. '
        'Không sửa output, nhãn hay scorer sau khi xem kết quả.', '',
        'Case tốt: C/02 giữ đúng A → B → A và đạt tự động. Case khó: lời nhận việc khi thiếu danh tính, '
        'đồng thuận ngầm, lựa chọn có điều kiện. Case thất bại: C/05 bị cắt output; H02 mất điều kiện ở pipeline. '
        'Chi tiết đủ 26 tình huống ở dưới.', '',
        '## Phương pháp và giới hạn', '',
        '- Cùng `qwen2.5:7b` Q4_K_M qua Ollama; temperature=0, seed=42, num_ctx=8192, num_predict=4000. Không API/cloud, chưa có phép thử model mạnh hơn.',
        '- B dùng một lần gọi model để trích xuất rồi guard literal/schema; C gom chủ đề → trích xuất → kiểm chứng bằng cùng model rồi guard. C có thể gọi ít hơn ba lần khi không có candidate/lỗi. Không nạp gold vào prompt.',
        '- V2: B chạy thật mới 20 case; C tái sử dụng 20 output chạy thật đã lưu và hậu kiểm bằng code. Hai nhánh không chạy cùng thời điểm. B dùng hướng dẫn tiếng Anh, C tiếng Việt: đây là so sánh hai cấu hình, chưa cô lập tác động số bước hay ngôn ngữ prompt. Không so latency như thí nghiệm có kiểm soát.',
        '- V2 là bộ đã xem, 8 case holdout cũ không còn kín. Sáu case v3 được viết và gán nhãn trước inference; mỗi case chạy đúng một lượt cho mỗi nhánh, không retry/tune sau đó. Nhãn do AI tạo, chưa kiểm tra độc lập; đây là holdout mới đối với quá trình chỉnh pipeline, không phải tập mù của bên thứ ba.',
        '- Kết quả hiện chưa chứng minh giả thuyết chất lượng. Chấm đọc giảm ảnh hưởng của so chuỗi nhưng vẫn thấy nhiều lỗi ngữ nghĩa; không đủ cơ sở nói ba bước tốt hơn một prompt hoặc thiết kế chắc chắn không khả thi.', '',
        f"Nguồn: [rubric]({REVIEWS}/rubric.json), [protocol v2]({BASE}/v2/protocol.json), "
        f"[protocol v3]({BASE}/holdout-v3/protocol.json), [manifest v3](data/holdout-v3/manifest.json).", '']
    for suite, arms in suites.items():
        lines += ['## ' + ('20 case v2 — bộ kiểm tra lại' if suite == 'v2' else '6 case v3 — lượt đánh giá cuối'), '']
        for id, score in arms['pipeline']['scores'].items():
            transcript = f'data/examples/{id}.txt' if suite == 'v2' else f'data/holdout-v3/{id}.txt'
            gold = f'tests/fixtures/{id}.expected.json' if suite == 'v2' else f'tests/fixtures/holdout-v3/{id}.expected.json'
            lines += [f"### {id} — {text(score['title'])}", '',
                f'[Transcript]({transcript}) · [Kỳ vọng JSON]({gold})', '',
                '**Kỳ vọng:** ' + text(score['expectation']), '']
            for arm, label in [('baseline_b', 'B — prompt đơn'), ('pipeline', 'C — pipeline')]:
                data = arms[arm]
                actual, grade, scored = data['outputs'][id], data['grades'][id], data['scores'][id]
                lines += [f'**Kết quả thực tế {label}:**', '']
                if actual.get('error'):
                    lines.append('- Lỗi: ' + text(actual['error']['message']))
                for item in actual['items']:
                    lines.append('- Nhận: ' + describe_item(item))
                for blocked in actual['review_queue']:
                    lines.append('- Cách ly: ' + describe_item(blocked['item']) + ' Lỗi guard: ' + text('; '.join(blocked['errors'])))
                if not actual['items'] and not actual['review_queue'] and not actual.get('error'):
                    lines.append('- Không có mục.')
                strict = 'Đạt' if scored['passed'] else 'Chưa đạt'
                semantic = 'Đạt' if grade['semantic_pass'] else 'Chưa đạt'
                lines += ['', f"**Đạt/Chưa đạt:** tự động **{strict}**; đọc ngữ nghĩa **{semantic}**. Phân loại: {text(grade['error_class'])}.", '',
                    '**Nhận xét chấm đọc:** ' + text(grade['reason']), '',
                    '**Lỗi chấm tự động:** ' + (text('; '.join(scored['errors'])) or 'Không có.'), '',
                    f"[Output]({grade['source']}) · [Bảng chấm đọc]({REVIEWS}/{suite}_{arm}.json)", '']
            lines += ['**Điều học được:** ' + text(score['lesson']), '']
    lines += ['## Tái tạo báo cáo và kiểm tra code', '',
        '```bash', 'python src test', 'python src report --check',
        'python src compare --suite v2 --model qwen2.5:7b --report-only',
        'python src compare --suite holdout-v3 --model qwen2.5:7b --report-only', '```', '',
        'Các lệnh trên không gọi model. Không chạy lại/tune v3 rồi vẫn gọi kết quả mới là kiểm thử kín. '
        'Một vòng phát triển tiếp theo cần bộ mới và protocol mới. Kết quả duyệt/xuất từng mục chưa được đánh giá trên đủ 26 case.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = render()
    target = PATHS.root / 'TESTS.md'
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != report:
            parser.exit(1, 'TESTS.md differs from saved JSON. Run python src report.\n')
    else:
        target.write_text(report, encoding='utf-8', newline='\n')
    print('TESTS.md matches saved results.' if args.check else 'Generated TESTS.md.')


if __name__ == '__main__':
    main()
