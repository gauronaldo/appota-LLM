# Meeting Trace — Meeting Intelligence MVP

Mission 2: **transcript → diễn biến → dữ liệu có evidence → kiểm chứng → duyệt từng mục → xuất**.

Mục tiêu là giữ kết luận cuối (A đổi sang B thì giữ B), công việc, vướng mắc, yêu cầu/phản hồi và nội dung chưa chốt. Model được huấn luyện sẵn; project triển khai pipeline, schema, kiểm tra bằng chứng, workflow duyệt và đánh giá.

## Chạy trên máy

Python 3.10+, source không cần pip dependency. Với LLM local, cần Ollama đang chạy và model đã cài:

```bash
git clone https://github.com/gauronaldo/appota-LLM.git
cd appota-LLM
ollama list
python src
```

Mở http://127.0.0.1:8501. Windows có thể dùng run.cmd; nếu cổng bận: `python src --port 8502`. Dừng bằng Ctrl+C.

UI mặc định **Qwen local · Ollama**, model **qwen2.5:7b**. Model khác đã cài có thể nhập trong ô Model. App chỉ gọi http://127.0.0.1:11434, không tự tải model hoặc chuyển sang cloud. Quy tắc local là baseline chạy được không cần Ollama.

1. Chọn mẫu, bấm **Nạp transcript**, rồi **Phân tích**. Mỗi dòng một lượt; tên người nói tùy chọn.
2. Đối chiếu evidence và diễn biến. Kết quả tự động chưa được con người duyệt.
3. Xác nhận từng mục, sửa hoặc loại bỏ. Mục cách ly cũng phải được xử lý; có thể sửa chủ đề, loại, trạng thái, nội dung, người nhận, hạn và evidence.
4. Mỗi lần sửa/khôi phục làm mất xác nhận cũ. Với LLM, xác nhận sẽ kiểm chứng lại.
5. Chỉ khi mọi mục đã xác nhận hoặc loại bỏ mới xuất **JSON + biên bản Markdown**. Server kiểm tra điều kiện xuất; cờ trên browser không cấp quyền duyệt.

Phiên duyệt lưu trong RAM server, hết hạn sau hai giờ hoặc khi server khởi động lại. Không có đăng nhập hay lưu trữ production. File xuất giữ bản tự động, các mục bị loại và audit chỉnh sửa. CLI `extract` tạo **bản nháp để kiểm tra**, không phải bản đã duyệt.

## Flow và kiểm chứng

- Parser gán T1, T2… và số dòng. Thiếu tên/nhãn ẩn danh giữ `speaker=null`; `speaker_label` chỉ để phân biệt lượt, không trở thành owner.
- LLM bước 1 gom chủ đề và diễn biến; bước 2 tạo thông tin cuối, giữ điều kiện và gộp một việc được nhắc lại. Không nạp fixture kỳ vọng vào prompt.
- Model chỉ chọn ID evidence/history; code lấy quote trực tiếp từ text của ID đó. Code kiểm tra schema, ID thật, quote nguyên văn và người nhận/hạn có evidence. Model vẫn có thể chọn sai ID hoặc suy diễn sai nội dung.
- LLM bước 3 kiểm tra: nội dung được hỗ trợ, đúng chủ đề, còn hiệu lực ở cuối họp, đủ điều kiện, giao việc/người nhận/hạn đúng. `fail` hoặc `uncertain` đưa vào review queue. Verdict sai ID/schema/evidence không được tin.
- Người dùng vẫn duyệt từng mục. Bộ kiểm chứng dùng cùng model, có thể sai cùng extractor; `semantic_verification=true` nghĩa là **đã chạy kiểm tra**, không bảo đảm chính xác.
- Baseline regex không chứng nhận paraphrase hoặc suy luận; sửa nội dung không khớp câu nguồn bị chặn để dùng LLM kiểm chứng.

Một item gồm id/topic/type/status/content/owner/due/evidence/reason/history. Deadline giữ cụm thời gian nguyên văn; thiếu để null. `status=confirmed` tự động khác `human_review.state=confirmed`.

Adapter Ollama dùng chat API, schema trong format, temperature=0, seed=42. Tham chiếu [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs). Structured JSON không tự bảo đảm đúng ngữ nghĩa.

## Kiểm thử và giới hạn số liệu

Suite v2 giữ nguyên **20 transcript, 20 kỳ vọng và manifest hash**: 12 có tên, 3 nhãn ẩn danh, 4 không nhãn, 1 trộn; bốn nhóm × năm case. Transcript tổng hợp, chưa được gán nhãn độc lập.

Baseline ban đầu **6/20** được giữ cùng source/freeze tại `data/benchmarks/baselines/v2-initial/`. Phiên mới đánh giá lại **bộ đã xem**; 12 dev / 8 split holdout cũ không còn được gọi là kiểm thử kín độc lập. Không sửa kỳ vọng để nâng điểm.

- Quy tắc: [dev JSON](data/benchmarks/results/local/dev_report.json), [kiểm tra lại JSON](data/benchmarks/results/local/holdout_report.json).
- Qwen chạy thật: [dev JSON](data/benchmarks/results/ollama/dev_report.json), [kiểm tra lại JSON](data/benchmarks/results/ollama/holdout_report.json).
- [Probe kiểm chứng riêng](data/benchmarks/safety/ollama_probes.json). Có accept/reject khớp 6/7, nhưng nhiều lý do/tiêu chí sai và bác nhầm một mục đúng; không coi là độ chính xác ngữ nghĩa 86%.
- Output nguyên bản: `data/benchmarks/results/local/`, `data/benchmarks/results/ollama/`.

Chấm một-một vẫn dùng chủ đề/nội dung chuỗi, trạng thái, owner/due, ID evidence và điều kiện. Cách diễn đạt tương đương có thể bị đánh trượt; xem cả lỗi từng case. Kết quả tự động chưa đo độ chính xác sau PM duyệt hoặc thời gian hoàn tất công việc. Kiểm thử kỹ thuật xanh không đồng nghĩa benchmark ngữ nghĩa đạt.

| Phiên | Phát triển | Split kiểm tra lại | Tổng |
| --- | --- | --- | --- |
| Quy tắc ban đầu | 6/12 | 0/8 | 6/20 |
| Quy tắc sau sửa parser | 7/12 | 0/8 | 7/20 |
| Qwen 2.5 7B chạy thật | 1/12 | 0/8 | 1/20 |

**Qwen hiện chưa đạt chất lượng cần để chứng minh giả thuyết cốt lõi.** Có lỗi định dạng/chủ đề theo quy ước chấm, và lỗi ngữ nghĩa thật về loại, trạng thái, bỏ sót và verifier. 53 kiểm thử kỹ thuật qua chỉ xác nhận cơ chế code, nguồn dữ liệu và export gate. Mỗi report có Kỳ vọng → Thực tế → Đạt/Chưa đạt → Điều học được; UI đọc cùng dữ liệu để hiển thị.

Case 02 A → B → A đạt toàn bộ. Case 09 nhận đúng Lan gửi báo cáo dù không có người nói nhưng due có thêm “trước”; case 10 nhận đúng một cột nhưng tên topic khác. Case 12 còn sai type decision cho nội dung chưa chốt; case 05 output bị cắt nên pipeline từ chối. Qwen decision TP/FP/FN là 3/3/5 (precision 0,5; recall 0,375). Một tỷ lệ case thấp không có nghĩa chỉ 5% phát biểu đúng; các lỗi ngữ nghĩa thật vẫn cần giải quyết.

Lượt inference nguyên bản/source/freeze lưu tại baselines/qwen-v2-live. Sau chạy, code bổ sung chặn owner là đại từ chưa xác định và sửa flag kiểm chứng khi bước đó bị bỏ qua vì không có candidate hợp lệ. Lệnh revalidate hậu kiểm trên output đã lưu, không gọi model mới, không nâng mục cách ly, không sửa nội dung và không đổi điểm 1/20. Report giữ core hashes/timestamp inference gốc cùng provenance hậu kiểm riêng.

```bash
python src test
python src evaluate --split dev --verify-only
python src evaluate --split holdout --verify-only
python src extract data/examples/01_change_ab.txt --engine ollama --model qwen2.5:7b --output runtime/draft.json
python src evaluate --engine ollama --model qwen2.5:7b --split dev
python src evaluate --engine ollama --model qwen2.5:7b --split holdout
python src package --verify
python src revalidate
python src verify-probes --engine ollama --model qwen2.5:7b
```

Chạy evaluation LLM gọi model thật, có thể chậm và không bảo đảm tái lập byte dù temperature=0. Lỗi API/schema/evidence được ghi thất bại, không dùng kết quả quy tắc thay thế. Freeze revision mới là `freeze-v2.json`; freeze cũ giữ nguyên.

## OpenAI tùy chọn

Đặt OPENAI_API_KEY và OPENAI_MODEL ở biến môi trường trước khi chạy server; app không tự load .env. Chọn engine openai hoặc truyền `--engine openai`. Chế độ này gửi transcript đến OpenAI; chế độ ollama ở máy. Không ghi key vào source hoặc chat. OpenAI chưa chạy API thật trong lượt này.

Adapter dùng Responses API và Structured Outputs, store=false. Tham chiếu [official OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Hạn chế

- Qwen 7B vẫn có thể bỏ sót, gắn nhầm chủ đề, chọn sai evidence, bỏ điều kiện hoặc nhận nhầm cam kết. Kiểm chứng bằng cùng model chưa phải người gán nhãn độc lập.
- Parser dùng dấu hai chấm và tên viết hoa để đoán nhãn; các tiền tố giống tên có thể mơ hồ. Một dòng tương ứng một lượt, chưa nhận diện speaker từ audio.
- Quy tắc local vẫn yếu với tham chiếu, đồng thuận ngầm, giao việc tự nhiên và việc lặp.
- Mục sai được cách ly có thể làm giảm recall. Phải sửa có bằng chứng hoặc loại bỏ; không có nút xác nhận tất cả.
- Chưa có audio/video, Jira/Notion, kho tri thức, auth, nghiên cứu PM hoặc kiểm thử với transcript thật ẩn danh. Server chỉ nghe loopback; hiện chạy local, chưa deploy online.

## Source showcase

```text
src/meeting_trace/
  meeting/       parser, local/LLM pipeline, schema, verifier, review workflow
  web/           HTTP local và UI
  evaluation/    runner, scoring, reporting
  tools/         test runner, source packager
tests/           unit, integration, regression, fixture kỳ vọng
data/examples/   transcript v2 và index
data/benchmarks/ freeze mới/cũ, baseline và kết quả thực tế
.github/         CI
```

Source và tool đều ở src; không có scripts. Repo/package không gom virtualenv, cache, API key, export người dùng, Word nguồn hoặc ghi chú riêng.

Tài liệu trình bày/báo cáo Markdown giữ ở workspace local, ngoài Git, theo việc thư mục docs đã được xóa trên remote. Packager có thể bổ sung tài liệu local nếu có; bản clone không cần docs để chạy hoặc kiểm thử.

## Ba câu trả lời Mission 2

**Phần chọn chứng minh:** kết luận cuối theo chủ đề, điều kiện và evidence, rồi duyệt trước xuất. Một tình huống A → B → A đã chạy đúng; số liệu hiện tại chưa đủ để kết luận giải pháp khả thi với cuộc họp tự nhiên.

**Đổi so với Mission 1:** thêm baseline regex lúc chưa có key, rồi dùng Qwen local, parser không bắt buộc tên, verifier và duyệt trên server. Suite tự nhiên hơn phơi bày giới hạn, nên giữ kỳ vọng và lịch sử thất bại. Lượt đánh giá lại không được nhận là tập kín độc lập.

**Dễ sai và cách tránh dữ liệu không tồn tại:** tham chiếu chủ đề, đồng thuận gián tiếp, loại/trạng thái và cam kết có điều kiện. Code lấy quote từ ID, kiểm tra schema/người/hạn, giữ null và cách ly lỗi; model kiểm tra ý nghĩa, người dùng phải duyệt từng mục. Verifier cùng model vẫn sai nên chưa bảo đảm không tạo dữ liệu sai.

AI hỗ trợ source, UI, schema, prompt, test, fixture tổng hợp và tài liệu. Không train/fine-tune; gán nhãn chưa được kiểm tra độc lập. Tác giả cần tự đối chiếu và bổ sung phần đã thực sự kiểm chứng cùng video tối đa 5 phút.
