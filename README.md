# Meeting Trace — Meeting Intelligence MVP

Biến transcript thành quyết định cuối, công việc, vướng mắc, yêu cầu/phản hồi và nội dung chưa chốt, kèm bằng chứng.
Luồng: transcript → theo dõi diễn biến → trích xuất → kiểm tra → duyệt từng mục → xuất JSON/biên bản.
Qwen 7B: chấm tự động prompt đơn **0/20**, pipeline **1/20**; sáu case mới **0/6** ở cả hai nhánh.
Chạy ngay bằng **Python 3.10+**, `python src`; mặc định quy tắc local, không cần Ollama, API key hay pip dependency.
Giới hạn chính: **chưa chứng minh chất lượng cốt lõi**; [TESTS.md](TESTS.md) tách lỗi định dạng/ngữ nghĩa và công khai thất bại.

[DEBUG.md](DEBUG.md) phân tích từng tầng và đủ 26 case: đã tái hiện lỗi guard/verifier và lỗi scorer/contract. Các thử nghiệm debug riêng không thay điểm benchmark hay sửa pipeline đã đóng băng.

## Chạy thử trên máy

```bash
git clone https://github.com/gauronaldo/appota-LLM.git
cd appota-LLM
python src
```

Mở [http://127.0.0.1:8501](http://127.0.0.1:8501). Windows có thể dùng `run.cmd`; cổng bận thì `python src --port 8502`. Dừng bằng Ctrl+C.

Mặc định **Quy tắc local · chạy ngay** để trải nghiệm workflow. Đây là baseline regex, không đại diện cho khả năng hiểu của AI. Để chạy LLM thật, cần Ollama đang chạy và `qwen2.5:7b` đã được cài: kiểm tra `ollama list`, chọn **Qwen local · cần Ollama** trong UI. App chỉ gọi loopback `127.0.0.1:11434`, không tự tải model hay chuyển sang cloud. Nếu chưa cài Ollama/model, chọn lại quy tắc local.

1. Chọn mẫu → **Nạp transcript** → **Phân tích cuộc họp**. Mỗi dòng một lượt, tên người nói tùy chọn.
2. Đối chiếu evidence và lịch sử thay đổi. **Xem kết quả đã chạy** đọc JSON lưu sẵn, không phải inference mới.
3. Xác nhận, sửa hoặc loại từng mục, kể cả mục bị cách ly. Sửa sẽ mất xác nhận cũ; LLM kiểm chứng lại khi xác nhận.
4. Khi mọi mục đã xử lý, xuất JSON và biên bản Markdown. Server kiểm tra quyền xuất và giữ audit chỉnh sửa.

Phiên duyệt lưu trong RAM, hết hạn sau hai giờ hoặc khi server khởi động lại. `status=confirmed` do model gán không thay cho xác nhận của người dùng. CLI `extract` chỉ tạo bản nháp. Với baseline luật, nội dung sửa không khớp câu nguồn có thể bị chặn; dùng LLM để kiểm chứng paraphrase.

## Kết quả thực tế

| Bộ | Cấu hình | Chấm tự động toàn case | Đọc ngữ nghĩa toàn case |
| --- | --- | --- | --- |
| V2 — 20 case đã xem | B: một prompt Qwen | 0/20 | 8/20 |
| V2 — 20 case đã xem | C: pipeline Qwen | 1/20 | 5/20 |
| V3 — 6 case mới, chạy một lượt mỗi nhánh | B: một prompt Qwen | 0/6 | 1/6 |
| V3 — 6 case mới, chạy một lượt mỗi nhánh | C: pipeline Qwen | 0/6 | 0/6 |

**Chấm đọc bởi Codex/AI được tác giả ủy quyền, không độc lập, không phải chấm bởi người thật.** Đã đọc transcript, kỳ vọng, items và candidates cách ly. Chấm ngữ nghĩa có thể công nhận candidate đúng nhưng bị chặn schema; **8/20 và 5/20 không phải tỷ lệ dữ liệu dùng được sau duyệt**. Chưa đo đủ bộ sau người dùng sửa/duyệt.

Điểm tự động giữ nguyên gold/scorer: so chủ đề và chuỗi nội dung, loại/trạng thái, người/hạn, điều kiện, evidence và history; có mục cách ly hoặc dư thì trượt. Đọc ngữ nghĩa cho phép cách diễn đạt cùng đối tượng, vẫn phạt sai trạng thái, thiếu nội dung, nhầm chủ đề hoặc bỏ điều kiện. C/09 đúng Lan gửi trước thứ Sáu nhưng khác tiền tố deadline; C/10 đúng một cột nhưng khác tên topic; C/16 candidate phát hành đúng nhưng có due không hợp schema. C/02 A → B → A đạt tự động; C/05 bị cắt output; nhiều case khác còn lỗi hiểu thật.

Cùng `qwen2.5:7b` Q4_K_M, temperature=0, seed=42, context=8192, output tối đa=4000 token. V2 chạy B mới, C tái sử dụng output inference thật đã lưu và hậu kiểm code. B dùng hướng dẫn tiếng Anh, C tiếng Việt: **so sánh hai cấu hình này chưa cô lập tác động số bước**, không kiểm soát latency đồng thời. V3 chạy thật cả hai nhánh, mỗi case đúng một lượt, không retry hoặc chỉnh pipeline sau khi xem kết quả.

V2 có 20 hội thoại tổng hợp: 12 có tên, 3 nhãn ẩn danh, 4 không nhãn, 1 trộn. Tám case holdout cũ đã được xem nên không còn kín. V3 có sáu hội thoại mới, gán nhãn trước inference và giữ nguyên đến cuối; kín với quá trình chỉnh pipeline, **chưa phải tập mù/gán nhãn độc lập**. Chưa chạy model mạnh hơn vì phạm vi chỉ local; chưa đủ cơ sở khẳng định nhiều bước giúp hay hại, hoặc thiết kế không khả thi trên model khác.

- [TESTS.md — đủ 26 tình huống](TESTS.md): Kỳ vọng → Thực tế → Đạt/Chưa đạt → Điều học được, cả B và C.
- [So sánh Qwen, JSON và protocol](data/benchmarks/comparisons/qwen2.5-7b/), [chấm đọc và rubric](data/benchmarks/reviews/).
- [Bộ mới và manifest](data/holdout-v3/manifest.json), [kỳ vọng v3](tests/fixtures/holdout-v3/).
- [Luật ban đầu 6/20](data/benchmarks/baselines/v2-initial/), [luật sau sửa parser 7/20](data/benchmarks/results/local/), [Qwen gốc và hậu kiểm](data/benchmarks/results/ollama/).
- [Probe verifier riêng](data/benchmarks/safety/ollama_probes.json): accept/reject khớp 6/7 nhưng lý do còn sai; không coi là độ chính xác ngữ nghĩa 86%.

## Project triển khai gì?

Model đã được huấn luyện sẵn, project không train/fine-tune. Phần triển khai biến đầu ra model thành dữ liệu có thể kiểm tra và duyệt:

- Parser gán T1, T2…; thiếu tên/nhãn ẩn danh giữ `speaker=null`. Nhãn “Người nói 2” không trở thành người nhận việc.
- Pipeline C: gom chủ đề/diễn biến → trích xuất kết luận cuối → kiểm chứng nội dung, chủ đề, hiệu lực, điều kiện và giao việc. Baseline B dùng một prompt, không có bước model kiểm chứng.
- Model chọn ID evidence/history; code lấy quote trực tiếp từ transcript, kiểm tra schema, ID, người nhận và hạn có nguồn. Không nạp kỳ vọng test vào prompt.
- Lỗi hoặc verdict không chắc chắn chuyển sang hàng chờ duyệt. Verifier dùng cùng Qwen vẫn có thể bỏ lọt sai và bác nhầm đúng; chạy kiểm chứng không đồng nghĩa đã đúng.
- Server quản lý xác nhận từng mục, vô hiệu xác nhận khi sửa và chặn xuất khi còn mục chưa xử lý. Bản xuất lưu nguồn, bản tự động và audit.

Item có `id/topic/type/status/content/owner/due/evidence/reason/history`. Điều kiện phải giữ trong content; thời gian/người chưa rõ để null. Parser là heuristic theo dòng, chưa nhận diện speaker từ audio. Luật yếu với tham chiếu, đồng thuận ngầm và hội thoại tự nhiên. Chưa có auth, lưu trữ production, tích hợp công việc hay kiểm thử transcript thật.

## Kiểm tra và tái tạo báo cáo

```bash
python src test
python src report --check
python src evaluate --split dev --verify-only
python src evaluate --split holdout --verify-only
python src package --verify
```

Các lệnh này không gọi LLM. `python src report` sinh TESTS.md từ JSON đã lưu, kiểm tra nguồn chấm đọc không bị đổi. Kiểm thử kỹ thuật xanh xác nhận cơ chế code, không thay cho benchmark chất lượng.

```bash
python src extract data/examples/01_change_ab.txt --engine ollama --model qwen2.5:7b --output runtime/draft.json
python src compare --suite v2 --model qwen2.5:7b --report-only
python src compare --suite holdout-v3 --model qwen2.5:7b --report-only
```

`extract` gọi model mới; hai lệnh `--report-only` chỉ đọc output. Protocol v3 đã hoàn tất: không chạy lại/tune rồi gọi bộ đó là kín. Vòng cải tiến tiếp theo cần bộ mới. Hash/protocol và lịch sử baseline ở JSON để đối chiếu; không retry nhằm chọn kết quả đẹp.

Adapter OpenAI có sẵn nhưng chưa chạy thật. Tự đặt `OPENAI_API_KEY` và `OPENAI_MODEL` trong biến môi trường nếu muốn dùng; không gửi key vào chat/source, app không tự đọc `.env`. Engine OpenAI gửi transcript tới provider. Bản đánh giá hiện tại chỉ dùng Ollama local.

## Source và bài nộp

```text
src/meeting_trace/
  meeting/       parser, schema, baseline B, pipeline C, verifier, review
  web/           server local và UI
  evaluation/    scoring, comparison, báo cáo từ JSON
  tools/         test runner, package, ghi nhận chấm đọc
tests/           unit, integration, regression, kỳ vọng cố định
data/            transcript tổng hợp, benchmark và kết quả thật
TESTS.md         báo cáo test đọc được, sinh từ JSON
.github/         CI
```

Source/tool ở `src`, không có `scripts`. Không đưa virtualenv, cache, key, export người dùng, Word nguồn hoặc ghi chú riêng lên repo. `docs/` giữ local theo lựa chọn của tác giả; báo cáo bắt buộc công khai là TESTS.md tại root. Packager có thể thêm tài liệu local nếu có, bản clone không cần docs.

**Bản chạy thử:** local theo phạm vi đã chọn; chưa deploy online. Có thể trải nghiệm workflow không cần tải model vài GB. **Video tối đa 5 phút:** chưa có link được cung cấp; còn cần tác giả quay và bổ sung để hoàn tất bài nộp.

## Ba câu trả lời Mission 2

**1. Phần quan trọng nhất và vì sao chọn:** Tôi chọn giữ đúng kết luận cuối theo chủ đề, điều kiện và bằng chứng, rồi duyệt trước xuất. Giữ quyết định đã bị hủy hoặc bỏ điều kiện sẽ tạo dữ liệu sai cho công việc. C/02 chứng minh được chuỗi A → B → A; code chứng minh được liên kết nguồn và cổng duyệt/xuất. Tuy vậy, kết quả toàn bộ Qwen và sáu case mới chưa đủ xác nhận giả thuyết về chất lượng. Muốn kết luận khả thi cần kiểm thử model mạnh hơn và transcript thật có nhãn độc lập.

**2. Thay đổi so với Mission 1 và nguyên nhân:** Tôi thêm baseline luật lúc chưa có API, thử Qwen local, cho phép thiếu nhãn người nói và giữ bất định danh tính. Hội thoại tự nhiên hơn làm lộ sai loại, trạng thái, giao việc và điều kiện, nên thêm kiểm chứng và duyệt trên server. Xem lại holdout cũ làm mất tính kín; tôi ghi rõ thay đổi và tạo sáu case mới có nhãn trước khi chạy một lần cuối. Tôi cũng hiện thực baseline B để đối chiếu C: chấm đọc B tốt hơn trong phép thử này, nhưng prompt/ngôn ngữ và thời điểm khác nhau nên chưa kết luận nguyên nhân nằm ở số bước.

**3. Thông tin dễ sai và cách tránh dữ liệu không tồn tại:** Dễ sai nhất là lời nhận việc có điều kiện/thiếu danh tính, chủ đề khi trao đổi đan xen và trạng thái sau khi mở lại quyết định. Project giữ null, lấy quote từ ID thật, kiểm tra người/hạn có nguồn, cách ly lỗi và yêu cầu duyệt từng mục. H02 cho thấy verifier cùng model vẫn cho qua action mất điều kiện; có evidence không đồng nghĩa content đúng nghĩa. Vì vậy MVP chưa tự đẩy dữ liệu vào công việc; cần đối chiếu nguồn, cải tiến trên bộ phát triển mới và đánh giá tiếp trước khi sử dụng tự động.

AI hỗ trợ code, prompt, fixture tổng hợp, tài liệu và chấm đọc theo ủy quyền của tác giả. Chấm không độc lập; nhãn chưa được kiểm tra bởi người thứ ba.
