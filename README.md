# Meeting Trace — Meeting Intelligence MVP

Prototype Mission 2: **transcript → diễn biến theo chủ đề → thông tin có cấu trúc → evidence → người dùng duyệt**.

Ví dụ, đầu cuộc họp đề xuất A nhưng cuối cùng chốt B: danh sách quyết định cần giữ B, còn A nằm trong diễn biến để đối chiếu. Đầu ra gồm quyết định, công việc, vướng mắc, yêu cầu/phản hồi và nội dung chưa chốt.

**Trạng thái thực tế:** có bản local chạy không cần key và pipeline LLM hai bước tùy chọn. **LLM chưa chạy API thật.** Suite v2 viết lại thành hội thoại tự nhiên hơn đạt **6/20 case trên local**; tập phát triển 6/12, tập kín 0/8. Đây là kết quả chẩn đoán giới hạn của bộ quy tắc, không phải chất lượng LLM hay sản phẩm đã sẵn sàng sử dụng.

## Chạy local

Cần Python **3.10+**, không cần cài dependency để chạy source:

```bash
git clone https://github.com/gauronaldo/appota-LLM.git
cd appota-LLM
python src
```

Mở <http://127.0.0.1:8501>. Windows có thể dùng `py -3 src`, hoặc bấm `run.cmd`. Nếu cổng bận: `python src --port 8502`. Dừng server bằng Ctrl+C.

1. Chọn **Bỏ máy chủ riêng, chọn dịch vụ quản lý**.
2. Bấm **Nạp transcript → Phân tích cuộc họp**.
3. Mở diễn biến A → B và bấm evidence để tìm câu gốc. Xem công việc cấu hình, người nhận Lan và hạn thứ Sáu.
4. Thử xác nhận, sửa, loại bỏ và xuất JSON. Bản tự động và lịch sử thay đổi được giữ riêng.
5. Chọn **Quay lại chuyện lưu trữ sau khi bàn lịch demo** để thấy lỗi thật: local gắn câu chốt vào chủ đề gần nhất.
6. Chọn một mẫu không người nói: parser hiện trả lỗi. **Xem kết quả đã chạy** hiển thị lỗi đã lưu; **Bộ kiểm thử** ghi case đó chưa đạt.

Dropdown chỉ chọn mẫu, chưa thay transcript; cần bấm Nạp transcript. JSON là dữ liệu/bản nháp có lịch sử, chưa phải biên bản chỉ được xuất sau khi mọi mục đã duyệt.

## Cách hoạt động

- Parser tách lượt nói và gán ID T1, T2… Bản hiện tại yêu cầu `Người nói: nội dung`, tối đa 300 lượt / 24.000 ký tự.
- Local nhận mẫu câu tường minh để gom chủ đề và phân loại phát biểu, rồi chọn lần chốt/hoãn cuối được nhận diện. Nó không hiểu đầy đủ đại từ, alias, phủ định hoặc câu giao việc tự nhiên.
- LLM dùng hai bước: gom chủ đề/phát biểu rồi xác định thông tin cuối từ diễn biến cùng transcript gốc. Prompt ở `src/meeting_trace/meeting/prompts.py`.
- Code kiểm tra schema, ID, trích dẫn nguyên văn, history và một số bằng chứng owner/deadline. Candidate lỗi được giữ kèm lý do, không tự xóa. **Khớp quote không bảo đảm kết luận đúng nghĩa.**
- UI hỗ trợ đối chiếu, duyệt từng mục và xuất JSON. `status=confirmed` của hệ thống khác với `human_review.state=confirmed` của người dùng.

Một item có `id`, `topic`, `type`, `status`, `content`, `owner`, `due`, `evidence`, `reason`, `history`. Các loại và bốn trạng thái được định nghĩa trong `schema.py`. Deadline giữ nguyên văn, không tự suy ngày cụ thể từ “ngày mai”. File xuất còn có `review_queue`, `review_audit`, `excluded_items` và `automated_snapshot`.

## Kiểm thử v2

20 hội thoại tổng hợp, mỗi case **15–24 lượt**, ngữ cảnh riêng và không dùng đoạn nhiễu chung. Bốn nhóm × năm case: đổi phương án, chốt gián tiếp/cam kết, chưa thống nhất, chốt/giao việc rõ. Dữ liệu gồm **12 case có tên, 3 nhãn ẩn danh, 4 không nhãn, 1 trộn**.

Kỳ vọng và hash được viết trước lượt chạy. 12 phát triển / 8 kín; engine và prompt không được chỉnh theo kết quả v2. Tác giả biết dữ liệu khi gán nhãn, nên đây không phải đánh giá mù hoặc độc lập. Bộ v1 và số liệu cũ được lưu riêng local, không đưa vào showcase này.

| Bộ local v2 | Đạt | Decision precision | Decision recall | TP / FP / FN |
| --- | --- | --- | --- | --- |
| Phát triển | 6/12 | 0,80 | 0,80 | 4 / 1 / 1 |
| Kín | 0/8 | 0,00 | 0,00 | 0 / 1 / 3 |

Lỗi input được tính là **chưa đạt**, vẫn nằm trong mẫu số, không thay bằng kết quả rỗng đạt. Phép chấm một-một có kiểm tra điều kiện được gán nhãn; so khớp chuỗi vẫn có thể đánh trượt diễn đạt tương đương. Metric owner/due ngoài kỳ vọng không đồng nghĩa mọi trường đó đều là tên/ngày không từng xuất hiện trong transcript: nó cũng phản ánh gán sai mục hoặc công việc lặp.

[Báo cáo từng case](docs/reports/TESTS.md) có Kỳ vọng → Thực tế → Đạt/Chưa đạt → Điều học được. JSON kết quả thật nằm trong `data/benchmarks/results/local/`.

```bash
python src test
python src evaluate --split dev --verify-only
python src evaluate --split holdout --verify-only
python src package --verify
```

34 kiểm tra unit/integration/regression qua xác nhận cơ chế code và tái lập kết quả. **CI xanh không có nghĩa 20 case ngữ nghĩa đều đạt.** `--verify-only` không ghi đè báo cáo/timestamp; bỏ cờ khi chủ động lưu lượt chạy mới. Freeze core và ánh xạ đường dẫn được giữ từ phiên trước; kỳ vọng v2 có manifest hash riêng. Không chạy lại freeze để che việc thay thuật toán.

## Bật LLM tùy chọn

Đặt API key và model vào môi trường **trước khi khởi động server**. Không đưa key vào transcript, source hoặc commit. `.env.example` chỉ là mẫu; app không tự load `.env`.

```powershell
$env:OPENAI_API_KEY = 'YOUR_KEY'
$env:OPENAI_MODEL = 'YOUR_SUPPORTED_MODEL_ID'
python src
```

Chọn **LLM hai bước** trên UI. Transcript sẽ được gửi tới OpenAI. Adapter dùng Responses API và Structured Outputs; model cần hỗ trợ các API đó và được tài khoản cho phép. Request đặt `store=false`, không phải tuyên bố toàn dịch vụ zero retention. Tham chiếu: [official OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

```bash
python src extract data/examples/01_change_ab.txt --engine openai --output runtime/llm-demo.json
python src evaluate --engine openai --split dev
python src evaluate --engine openai --split holdout
```

Kết quả LLM lưu riêng ở `data/benchmarks/results/openai` và `docs/reports/TESTS_LLM.md`. Chưa có key nên chưa có số liệu LLM, so sánh A/B/C, chi phí hoặc độ trễ. Test API hiện dùng mock. Case không nhãn sẽ vẫn thất bại trước khi gọi model do parser chưa hỗ trợ, và được báo rõ.

## Hạn chế và phần tiếp theo

- Parser chưa nhận transcript thiếu người nói hoặc trộn nhãn. Bộ v2 cố ý giữ những input này để phơi bày giới hạn, không ép thêm tên cho thuận thuật toán.
- Local nhận chủ đề bằng từ khóa, dễ gắn sai kết luận, bỏ sót đồng thuận ngầm, giao việc bằng câu tự nhiên và tạo công việc lặp khi một cam kết được nhắc lại.
- Nhãn Người nói 1/2 chưa phải danh tính người nhận đã xác minh. Local có thể ghi nhãn thành owner; đây là lỗi được ghi trong test.
- Chưa xác minh đầy đủ quote hỗ trợ kết luận/điều kiện và kết luận còn hiệu lực sau mọi cách bác bỏ gián tiếp.
- UI chưa bắt buộc duyệt xong trước xuất; chưa sửa chủ đề/loại/trạng thái/evidence hoặc sửa trực tiếp mục bị quarantine. Duyệt lưu trong tab, cần xuất trước reload/chạy lại.
- Chưa có file biên bản riêng, dữ liệu thật ẩn danh, gán nhãn độc lập, nghiên cứu PM, phép đo thời gian hoàn tất hoặc lỗi sau duyệt.
- Không làm audio/video, nhận diện người nói, Jira/Notion, kho tri thức hoặc đăng nhập. Server chỉ nghe loopback; không dùng trực tiếp để public hosting.

Bước tiếp theo là mở rộng input, kiểm chứng LLM thật cùng tầng kiểm tra ngữ nghĩa, hoàn thiện duyệt trước xuất rồi so với baseline một prompt mạnh. Không đổi kỳ vọng sau khi thấy kết quả để nâng tỷ lệ đạt.

## Source showcase

```text
src/                     entry point và package meeting_trace
  meeting_trace/
    meeting/             parser, local/LLM pipeline, schema, validator
    web/                 server và static UI
    evaluation/          runner, scoring, reporting
    tools/               test runner và source packager
tests/                   unit, integration, regression, 20 kỳ vọng và hash
data/examples/           20 transcript mẫu và index
data/benchmarks/         freeze, path mapping và kết quả v2
docs/                    kiến trúc, phát triển, báo cáo và tài liệu nộp
.github/workflows/       CI Windows/Linux
pyproject.toml           package metadata; không có runtime dependency
run.cmd / run.ps1        launcher Windows
```

Repo chỉ gồm source, fixture tổng hợp, kết quả tái lập và tài liệu cần để reviewer chạy/đánh giá. Không đưa virtualenv, cache, ZIP, export người dùng, tài liệu Word nguồn hoặc ghi chú đối chiếu nội bộ vào Git.

- [Kiến trúc](docs/architecture.md), [phát triển](docs/development.md).
- [Ba câu trả lời Mission 2](docs/submission/ANSWERS.md), [AI log](docs/submission/AI_LOG.md), [kịch bản video](docs/submission/VIDEO_SCRIPT.md).

**Bản thử hiện chạy local, chưa có demo online.** Prototype chưa thiết kế cho hosting public; hướng dẫn local ở trên là cách chạy được không cần key. Video do tác giả tự quay, chưa có link trong repo. Cấu hình CI được cung cấp cho GitHub; README không nhận một lượt chạy remote chưa được xác minh là đã qua.
