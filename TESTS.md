# Bộ kiểm thử Mission 2

Sinh bằng `python src report` từ JSON đã lưu. Không gọi model hoặc thay kỳ vọng.

## Kết quả và người chấm

| Bộ dữ liệu | Cấu hình | Chấm tự động, toàn case | Đọc ngữ nghĩa, toàn case |
| --- | --- | --- | --- |
| v2 | B: một prompt | 0/20 | 8/20 |
| v2 | C: pipeline ba bước | 1/20 | 5/20 |
| holdout-v3 | B: một prompt | 0/6 | 1/6 |
| holdout-v3 | C: pipeline ba bước | 0/6 | 0/6 |

**Người chấm đọc: Codex/AI được tác giả ủy quyền. Không độc lập, không phải chấm bởi người thật.** Đã đọc transcript, nhãn kỳ vọng, kết quả và candidates cách ly; không hỏi Qwen để chấm. Ngữ nghĩa có thể đạt khi candidate đúng nhưng chưa thành item hợp lệ. Vì thế 8/20 và 5/20 không phải tỷ lệ dữ liệu dùng được sau duyệt. `ready_without_edit` trong JSON đo tuân thủ đầy đủ hợp đồng fixture, không đo thao tác xuất của người dùng.

Điểm tự động giữ nguyên: đối chiếu một-một type/topic/chuỗi nội dung/status/owner/due/evidence/conditions/history, có mục cách ly hoặc dư thì trượt. Chấm đọc cho phép tên cùng đối tượng/cách viết tương đương, nhưng không tha lỗi trạng thái, sai chủ đề, mất điều kiện, thiếu việc hoặc evidence không hỗ trợ kết luận cuối. Không sửa output, nhãn hay scorer sau khi xem kết quả.

Case tốt: C/02 giữ đúng A → B → A và đạt tự động. Case khó: lời nhận việc khi thiếu danh tính, đồng thuận ngầm, lựa chọn có điều kiện. Case thất bại: C/05 bị cắt output; H02 mất điều kiện ở pipeline. Chi tiết đủ 26 tình huống ở dưới.

## Phương pháp và giới hạn

- Cùng `qwen2.5:7b` Q4_K_M qua Ollama; temperature=0, seed=42, num_ctx=8192, num_predict=4000. Không API/cloud, chưa có phép thử model mạnh hơn.
- B dùng một lần gọi model để trích xuất rồi guard literal/schema; C gom chủ đề → trích xuất → kiểm chứng bằng cùng model rồi guard. C có thể gọi ít hơn ba lần khi không có candidate/lỗi. Không nạp gold vào prompt.
- V2: B chạy thật mới 20 case; C tái sử dụng 20 output chạy thật đã lưu và hậu kiểm bằng code. Hai nhánh không chạy cùng thời điểm. B dùng hướng dẫn tiếng Anh, C tiếng Việt: đây là so sánh hai cấu hình, chưa cô lập tác động số bước hay ngôn ngữ prompt. Không so latency như thí nghiệm có kiểm soát.
- V2 là bộ đã xem, 8 case holdout cũ không còn kín. Sáu case v3 được viết và gán nhãn trước inference; mỗi case chạy đúng một lượt cho mỗi nhánh, không retry/tune sau đó. Nhãn do AI tạo, chưa kiểm tra độc lập; đây là holdout mới đối với quá trình chỉnh pipeline, không phải tập mù của bên thứ ba.
- Kết quả hiện chưa chứng minh giả thuyết chất lượng. Chấm đọc giảm ảnh hưởng của so chuỗi nhưng vẫn thấy nhiều lỗi ngữ nghĩa; không đủ cơ sở nói ba bước tốt hơn một prompt hoặc thiết kế chắc chắn không khả thi.

Nguồn: [rubric](data/benchmarks/reviews/rubric.json), [protocol v2](data/benchmarks/comparisons/qwen2.5-7b/v2/protocol.json), [protocol v3](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/protocol.json), [manifest v3](data/holdout-v3/manifest.json).

## 20 case v2 — bộ kiểm tra lại

### 01_change_ab — Bỏ máy chủ riêng, chọn dịch vụ quản lý

[Transcript](data/examples/01_change_ab.txt) · [Kỳ vọng JSON](tests/fixtures/01_change_ab.expected.json)

**Kỳ vọng:** decision/lưu trữ: phương án B (confirmed, owner=None, due=None, conditions=[]); action/triển khai: bản cấu hình (confirmed, owner=Lan, due=thứ Sáu, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Lựa chọn phương án lưu trữ cho bản thử: Dùng phương án B cho bản thử. Chưa mua máy chủ riêng ở đợt này. (confirmed; người=None; hạn=None). Evidence: T13, T14. Diễn biến: T3, T6, T8, T12.
- Cách ly: action/Cấu hình cho bản thử: Lan nhận làm bản cấu hình trước thứ Sáu. (confirmed; người=None; hạn=None). Evidence: T15, T16. Diễn biến: không có. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng/schema.

**Nhận xét chấm đọc:** Giữ B cuối ở T13/T14 và lịch sử bỏ máy chủ riêng. Candidate Lan nhận cấu hình trước thứ Sáu có cả tên/hạn trong content và evidence T15/T16, nhưng owner/due để null nên bị chặn. Đúng nghĩa candidate, chưa đủ trường cấu trúc.

**Lỗi chấm tự động:** Thiếu/sai decision: lưu trữ / phương án B; Thiếu/sai action: triển khai / bản cấu hình; Mục ngoài kỳ vọng: decision / Lựa chọn phương án lưu trữ cho bản thử / Dùng phương án B cho bản thử. Chưa mua máy chủ riêng ở đợt này.; 1 mục không qua validator; Thiếu diễn biến T13

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/01_change_ab.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: decision/lưu trữ: Chốt dùng phương án B cho bản thử. Chưa mua máy chủ riêng ở đợt này. (confirmed; người=Lan; hạn=None). Evidence: T13, T8, T12, T10, T11. Diễn biến: T8, T10, T11, T12, T13. Lỗi guard: Chỉ công việc được có người nhận hoặc hạn

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Candidate chọn B đúng nhưng gắn owner Lan vào decision; mất việc cấu hình tại T16 và không giữ đề xuất A. Không thể coi chỉ là lỗi định dạng.

**Lỗi chấm tự động:** Thiếu/sai decision: lưu trữ / phương án B; Thiếu/sai action: triển khai / bản cấu hình; 1 mục không qua validator; Thiếu diễn biến T3; Thiếu diễn biến T8; Thiếu diễn biến T13

[Output](data/benchmarks/results/ollama/01_change_ab.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Giữ B là quyết định cuối; hội thoại không cần nhắc lại tên chủ đề ở mọi lượt.

### 02_change_aba — Lịch demo đổi sang chiều rồi quay lại buổi sáng

[Transcript](data/examples/02_change_aba.txt) · [Kỳ vọng JSON](tests/fixtures/02_change_aba.expected.json)

**Kỳ vọng:** decision/lịch demo: phương án A (confirmed, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Lịch demo: Chốt lịch demo sáng thứ Năm. (confirmed; người=None; hạn=None). Evidence: T2, T4, T5, T6, T7, T8. Diễn biến: T2, T4, T5, T6, T7, T8.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Câu sáng thứ Năm trùng kết luận cuối, nhưng evidence chỉ đến T8: tại đó đã đổi sang chiều. Không dẫn T15 chốt lại sáng, nên đúng câu chưa chứng minh được hiểu lần đảo cuối.

**Lỗi chấm tự động:** Thiếu/sai decision: lịch demo / phương án A; Mục ngoài kỳ vọng: decision / Lịch demo / Chốt lịch demo sáng thứ Năm.; Thiếu diễn biến T15

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/02_change_aba.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/lịch demo: Về lịch demo, chốt phương án A, sáng thứ Năm. (confirmed; người=None; hạn=None). Evidence: T15, T16. Diễn biến: T2, T3, T6, T8, T12, T15.

**Đạt/Chưa đạt:** tự động **Đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Đạt.

**Nhận xét chấm đọc:** T15 chốt lại sáng thứ Năm; evidence/history giữ T2, T8, T15. Không nâng lịch chiều thành kết luận cuối.

**Lỗi chấm tự động:** Không có.

[Output](data/benchmarks/results/ollama/02_change_aba.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Một lần chốt giữa cuộc họp có thể bị thay; phải theo dõi lần quay lại A.

### 03_switch_condition — Đổi nhà cung cấp nhưng giữ điều kiện phê duyệt

[Transcript](data/examples/03_switch_condition.txt) · [Kỳ vọng JSON](tests/fixtures/03_switch_condition.expected.json)

**Kỳ vọng:** decision/email: gói B (confirmed, owner=None, due=None, conditions=[&#x27;nếu pháp chế duyệt&#x27;])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/Chọn nhà cung cấp cho đợt ra mắt: Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu. (unresolved; người=None; hạn=None). Evidence: T12. Diễn biến: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ điều kiện pháp chế nhưng ghi lựa chọn B thành unresolved/unresolved thay cho quyết định có điều kiện. Không gộp hai loại này sau khi xem output.

**Lỗi chấm tự động:** Thiếu/sai decision: email / gói B; Mục ngoài kỳ vọng: unresolved / Chọn nhà cung cấp cho đợt ra mắt / Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/03_switch_condition.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/lưu trữ: Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu. (confirmed; người=None; hạn=None). Evidence: T12. Diễn biến: T5, T6, T7, T12.
- Nhận: issue/hợp đồng pháp chế: Hợp đồng B đã được bên pháp chế xem chưa? (unresolved; người=None; hạn=None). Evidence: T8, T9. Diễn biến: T8, T9.
- Cách ly: action/thời gian ký hợp đồng: Mình dừng ở đây, chưa ký trong hôm nay. (confirmed; người=None; hạn=None). Evidence: T17. Diễn biến: T17. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ B và điều kiện ở T12, nhưng gắn chủ đề lưu trữ thay cho lựa chọn dịch vụ email T1; tạo candidate ký hợp đồng từ câu chưa ký T17. Câu hỏi pháp chế là thông tin có thật, không tự coi nó là hallucination.

**Lỗi chấm tự động:** Thiếu/sai decision: email / gói B; Mục ngoài kỳ vọng: decision / lưu trữ / Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu.; Mục ngoài kỳ vọng: issue / hợp đồng pháp chế / Hợp đồng B đã được bên pháp chế xem chưa?; 1 mục không qua validator

[Output](data/benchmarks/results/ollama/03_switch_condition.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Điều kiện là một phần của quyết định; không được biến chọn có điều kiện thành quyền triển khai ngay.

### 04_interleaved — Quay lại chuyện lưu trữ sau khi bàn lịch demo

[Transcript](data/examples/04_interleaved.txt) · [Kỳ vọng JSON](tests/fixtures/04_interleaved.expected.json)

**Kỳ vọng:** decision/lưu trữ: phương án B (confirmed, owner=None, due=None, conditions=[]); unresolved/lịch demo: chiều thứ Tư (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Lưu trữ: Chốt dùng phương án B cho phần đó. (confirmed; người=None; hạn=None). Evidence: T15, T16. Diễn biến: T1, T2, T3, T4, T5, T6, T15.
- Nhận: unresolved/Lịch trình bày: Về lịch demo, hay mình chuyển sang chiều thứ Tư cho họ tiện? (unresolved; người=None; hạn=None). Evidence: T8, T9, T10, T17. Diễn biến: T8, T9, T10, T17.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Giữ B cho lưu trữ và đề xuất demo chiều thứ Tư ở trạng thái unresolved, evidence có T17 còn mở. Lịch trình bày/lịch demo là cùng đối tượng; tên topic khác fixture.

**Lỗi chấm tự động:** Thiếu/sai unresolved: lịch demo / chiều thứ Tư; Mục ngoài kỳ vọng: unresolved / Lịch trình bày / Về lịch demo, hay mình chuyển sang chiều thứ Tư cho họ tiện?

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/04_interleaved.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/lưu trữ: Chốt dùng phương án B cho phần lưu trữ. (confirmed; người=None; hạn=None). Evidence: T15. Diễn biến: T15, T16.
- Nhận: issue/lịch demo: Lịch demo sẽ được xác định sau khi hỏi khách hàng. (unresolved; người=None; hạn=None). Evidence: T8, T17. Diễn biến: T8, T17.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Nhận đúng B thuộc lưu trữ T15, nhưng lịch demo còn mở T8/T17 bị ghi thành issue và mất phương án chiều thứ Tư trong content.

**Lỗi chấm tự động:** Thiếu/sai unresolved: lịch demo / chiều thứ Tư; Mục ngoài kỳ vọng: issue / lịch demo / Lịch demo sẽ được xác định sau khi hỏi khách hàng.

[Output](data/benchmarks/results/ollama/04_interleaved.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Đại từ và tham chiếu quay lại chủ đề có thể làm local gắn câu chốt đúng chữ vào sai chủ đề.

### 05_unnamed_reversal — Đổi cổng thanh toán trong transcript không có người nói

[Transcript](data/examples/05_unnamed_reversal.txt) · [Kỳ vọng JSON](tests/fixtures/05_unnamed_reversal.expected.json)

**Kỳ vọng:** decision/thanh toán: cổng B (confirmed, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Chuyển cổng thanh toán: Chốt chuyển sang cổng B cho đợt thử tiếp theo. (confirmed; người=None; hạn=None). Evidence: T14, T10. Diễn biến: T10, T14.
- Nhận: issue/环境问题报告: 如果在测试环境中出现问题，则必须上报，不得自行更改回A网关。 (unresolved; người=None; hạn=None). Evidence: T16. Diễn biến: T16.
- Cách ly: action/保留在用的支付网关: Cổng A vẫn giữ cho giao dịch cũ, không xóa lịch sử. (confirmed; người=None; hạn=None). Evidence: T15. Diễn biến: T15. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ cổng B đúng T14 nhưng biến chính sách giữ A cho giao dịch cũ thành action mới và giả định có lỗi thành issue; nội dung phụ trả bằng tiếng Trung. Không tính chỉ một quyết định đúng là cả case đạt.

**Lỗi chấm tự động:** Thiếu/sai decision: thanh toán / cổng B; Mục ngoài kỳ vọng: decision / Chuyển cổng thanh toán / Chốt chuyển sang cổng B cho đợt thử tiếp theo.; Mục ngoài kỳ vọng: issue / 环境问题报告 / 如果在测试环境中出现问题，则必须上报，不得自行更改回A网关。; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/05_unnamed_reversal.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Lỗi: Ollama chưa hoàn tất hoặc output bị cắt ngắn.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Hệ thống.

**Nhận xét chấm đọc:** Model output bị cắt; không có kết quả để nhận là hiểu đúng. Parser đã nhận input không nhãn.

**Lỗi chấm tự động:** Pipeline không xử lý được input: Ollama chưa hoàn tất hoặc output bị cắt ngắn.; Thiếu/sai decision: thanh toán / cổng B

[Output](data/benchmarks/results/ollama/05_unnamed_reversal.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Transcript vẫn có kết luận rõ dù thiếu người nói; parser hiện tại phải được đánh giá là chưa hỗ trợ, không biến lỗi input thành kết quả trống đạt.

### 06_ambiguous_ok — Một câu ok có thể chỉ là đã nghe

[Transcript](data/examples/06_ambiguous_ok.txt) · [Kỳ vọng JSON](tests/fixtures/06_ambiguous_ok.expected.json)

**Kỳ vọng:** unresolved/thanh toán: ví điện tử (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Cách ly: unresolved/Thanh toán: Bản demo còn dùng chuyển khoản thủ công. (unresolved; người=None; hạn=None). Evidence: không có. Diễn biến: T17. Lỗi guard: reason đang trống; Không có evidence
- Cách ly: issue/Thanh toán - ví điện tử: Đề xuất thêm ví điện tử ở đợt thử này để khách bớt thao tác. (unresolved; người=None; hạn=None). Evidence: không có. Diễn biến: T2, T13. Lỗi guard: reason đang trống; Không có evidence

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Hai candidates không có evidence/reason; đề xuất ví chưa chốt bị ghi thành issue. Không có bản ghi đầy đủ cho nội dung mở chính.

**Lỗi chấm tự động:** Thiếu/sai unresolved: thanh toán / ví điện tử; 2 mục không qua validator; Thiếu diễn biến T2; Thiếu diễn biến T13

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/06_ambiguous_ok.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/thanh toán: Phần thanh toán hiện tại vẫn chạy như cũ. (confirmed; người=None; hạn=None). Evidence: T17. Diễn biến: T2, T17.
- Nhận: issue/ví điện tử: Đề xuất thêm ví điện tử ở đợt thử này để khách bớt thao tác. (unresolved; người=None; hạn=None). Evidence: T2, T14. Diễn biến: T2, T16, T14.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** T13 chưa chốt ví điện tử; output ghi đề xuất ví thành issue và giữ thanh toán cũ thành decision. Chưa thể hiện đúng nội dung chưa chốt chính.

**Lỗi chấm tự động:** Thiếu/sai unresolved: thanh toán / ví điện tử; Mục ngoài kỳ vọng: decision / thanh toán / Phần thanh toán hiện tại vẫn chạy như cũ.; Mục ngoài kỳ vọng: issue / ví điện tử / Đề xuất thêm ví điện tử ở đợt thử này để khách bớt thao tác.; Thiếu diễn biến T13

[Output](data/benchmarks/results/ollama/06_ambiguous_ok.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Ok có thể là tín hiệu nghe được, không phải đồng thuận; lời cuối xác nhận đề xuất chưa chốt.

### 07_let_me_check — Để em xem lỗi này chưa thành lời nhận sửa

[Transcript](data/examples/07_let_me_check.txt) · [Kỳ vọng JSON](tests/fixtures/07_let_me_check.expected.json)

**Kỳ vọng:** issue/đăng nhập: chưa tái hiện (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/đăng nhập: xem lỗi (needs_confirmation, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: issue/Lỗi đăng nhập chưa tái hiện được: Vướng mắc là chưa tái hiện được lỗi đăng nhập trên môi trường thử. (unresolved; người=None; hạn=None). Evidence: T12, T13, T14, T15. Diễn biến: T12, T13, T14, T15.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ blocker chưa tái hiện, nhưng status unresolved khác needs_confirmation và bỏ nội dung điều tra chưa được giao. Không bịa sửa lỗi là điểm tốt, chưa đủ cả case.

**Lỗi chấm tự động:** Thiếu/sai issue: đăng nhập / chưa tái hiện; Thiếu/sai unresolved: đăng nhập / xem lỗi; Mục ngoài kỳ vọng: issue / Lỗi đăng nhập chưa tái hiện được / Vướng mắc là chưa tái hiện được lỗi đăng nhập trên môi trường thử.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/07_let_me_check.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: issue/báo cáo lỗi: Có khách báo đăng nhập hai lần mới vào được, nhưng chưa xác định nguyên nhân cụ thể. (unresolved; người=None; hạn=None). Evidence: T12, T13, T14, T15. Diễn biến: T12, T13, T14, T15.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Không bịa việc sửa là điểm tốt, nhưng thiếu blocker chưa tái hiện T12 và thiếu trạng thái/diễn biến xem lỗi chưa được giao T4/T10. Chưa biết nguyên nhân không đồng nghĩa chưa tái hiện.

**Lỗi chấm tự động:** Thiếu/sai issue: đăng nhập / chưa tái hiện; Thiếu/sai unresolved: đăng nhập / xem lỗi; Mục ngoài kỳ vọng: issue / báo cáo lỗi / Có khách báo đăng nhập hai lần mới vào được, nhưng chưa xác định nguyên nhân cụ thể.

[Output](data/benchmarks/results/ollama/07_let_me_check.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Không biến ý định xem xét thành cam kết sửa; cần giữ sự mơ hồ để PM xác nhận.

### 08_self_commit_label — Có cam kết rõ nhưng chỉ có nhãn người nói

[Transcript](data/examples/08_self_commit_label.txt) · [Kỳ vọng JSON](tests/fixtures/08_self_commit_label.expected.json)

**Kỳ vọng:** action/giỏ hàng: xem lỗi (needs_confirmation, owner=None, due=chiều nay, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: issue/Lỗi tổng tiền giỏ hàng không cập nhật: Người nói 2 sẽ tìm nguyên nhân lỗi và báo cáo trong chiều nay. (confirmed; người=None; hạn=None). Evidence: T8, T10. Diễn biến: T8, T10.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Lời nhận xem lỗi/báo chiều nay bị ghi issue/confirmed thay action/needs_confirmation khi danh tính chưa biết. Hạn cũng chưa vào trường due.

**Lỗi chấm tự động:** Thiếu/sai action: giỏ hàng / xem lỗi; Mục ngoài kỳ vọng: issue / Lỗi tổng tiền giỏ hàng không cập nhật / Người nói 2 sẽ tìm nguyên nhân lỗi và báo cáo trong chiều nay.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/08_self_commit_label.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: action/lỗi giỏ hàng: Để em xem lỗi này và báo lại chiều nay. (confirmed; người=None; hạn=None). Evidence: T8. Diễn biến: T8, T15. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Đúng lời xem lỗi/báo chiều nay T8, nhưng status confirmed với owner null thay cho needs_confirmation; due cũng bị mất khỏi trường cấu trúc. Guard chặn.

**Lỗi chấm tự động:** Thiếu/sai action: giỏ hàng / xem lỗi; 1 mục không qua validator

[Output](data/benchmarks/results/ollama/08_self_commit_label.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Cam kết và hạn có thật; nhãn người nói chưa phải tên người nhận việc đã xác minh.

### 09_named_assignee_no_speaker — Người nhận được nêu trong nội dung, không biết ai nói

[Transcript](data/examples/09_named_assignee_no_speaker.txt) · [Kỳ vọng JSON](tests/fixtures/09_named_assignee_no_speaker.expected.json)

**Kỳ vọng:** action/báo cáo: gửi báo cáo (confirmed, owner=Lan, due=thứ Sáu, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Cách ly: action/Báo cáo cho khách: Lan gửi báo cáo trước thứ Sáu, bao gồm bản số liệu và phần ghi chú. (confirmed; người=Lan; hạn=None). Evidence: T7, T8, T9. Diễn biến: T1, T2, T3, T4, T5, T6, T7. Lỗi guard: reason đang trống

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng/schema.

**Nhận xét chấm đọc:** Candidate giữ đúng Lan, báo cáo và trước thứ Sáu trong content; evidence T9 giao việc có thật. due null và reason trống làm guard chặn, cần chuẩn hóa trường thay vì suy luận thêm việc mới.

**Lỗi chấm tự động:** Thiếu/sai action: báo cáo / gửi báo cáo; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/09_named_assignee_no_speaker.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: action/báo cáo: Lan gửi báo cáo cho khách trước thứ Sáu, bao gồm bản số liệu đã đối soát và phần ghi chú về giao dịch treo. (confirmed; người=Lan; hạn=trước thứ Sáu). Evidence: T7, T9. Diễn biến: T1, T7, T9.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** T9 giao Lan gửi báo cáo trước thứ Sáu; output giữ đúng người/việc/hạn/phần ghi chú. due có tiền tố trước khác quy ước fixture, không đổi nghĩa deadline.

**Lỗi chấm tự động:** báo cáo: due kỳ vọng &#x27;thứ Sáu&#x27;, thực tế &#x27;trước thứ Sáu&#x27;

[Output](data/benchmarks/results/ollama/09_named_assignee_no_speaker.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Không cần biết người phát biểu để nhận ra tên người được giao việc được nói rõ trong nội dung.

### 10_indirect_consensus — Thống nhất qua nhiều lượt mà không nói từ chốt

[Transcript](data/examples/10_indirect_consensus.txt) · [Kỳ vọng JSON](tests/fixtures/10_indirect_consensus.expected.json)

**Kỳ vọng:** decision/báo cáo: một cột (confirmed, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Thay đổi bố cục màn hình báo cáo trên điện thoại: Chuyển sang một cột cho màn hình báo cáo, không thay đổi dữ liệu gốc. (confirmed; người=None; hạn=None). Evidence: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13. Diễn biến: T7.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Giữ một cột, dữ liệu không đổi, evidence bao gồm T13 đồng thuận cuối. Topic dài hơn báo cáo nhưng cùng màn hình điện thoại.

**Lỗi chấm tự động:** Thiếu/sai decision: báo cáo / một cột; Mục ngoài kỳ vọng: decision / Thay đổi bố cục màn hình báo cáo trên điện thoại / Chuyển sang một cột cho màn hình báo cáo, không thay đổi dữ liệu gốc.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/10_indirect_consensus.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/màn hình báo cáo: Màn hình báo cáo sẽ sử dụng một cột thay vì hai cột. (confirmed; người=None; hạn=None). Evidence: T7, T13. Diễn biến: T2, T7, T13.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** T7/T13 đồng thuận dùng một cột. Màn hình báo cáo là tên cụ thể của đối tượng báo cáo, không phải nhầm sang một chủ đề khác.

**Lỗi chấm tự động:** Thiếu/sai decision: báo cáo / một cột; Mục ngoài kỳ vọng: decision / màn hình báo cáo / Màn hình báo cáo sẽ sử dụng một cột thay vì hai cột.

[Output](data/benchmarks/results/ollama/10_indirect_consensus.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Đồng thuận có thể được thể hiện bằng nhiều lượt và lời kết luận gián tiếp, không chỉ từ khóa chốt.

### 11_unresolved_budget — Thiếu báo giá nên chưa chọn phương án

[Transcript](data/examples/11_unresolved_budget.txt) · [Kỳ vọng JSON](tests/fixtures/11_unresolved_budget.expected.json)

**Kỳ vọng:** unresolved/hạ tầng: hoãn lựa chọn (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/Lựa chọn hạ tầng: Hoãn lựa chọn đến khi đủ báo giá. (unresolved; người=None; hạn=None). Evidence: T13, T14. Diễn biến: T1, T2, T6, T9, T13.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Giữ hoãn chọn hạ tầng đến khi đủ báo giá ở unresolved/unresolved và evidence T13. Không tạo assignment chuyển dữ liệu; chỉ khác tên topic.

**Lỗi chấm tự động:** Thiếu/sai unresolved: hạ tầng / hoãn lựa chọn; Mục ngoài kỳ vọng: unresolved / Lựa chọn hạ tầng / Hoãn lựa chọn đến khi đủ báo giá.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/11_unresolved_budget.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: unresolved/hạ tầng: Chưa chốt phương án hạ tầng; hoãn lựa chọn đến khi đủ báo giá. (needs_confirmation; người=None; hạn=None). Evidence: T13. Diễn biến: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Content hoãn lựa chọn là đúng và không tạo việc chuyển dữ liệu, nhưng status needs_confirmation thay unresolved khác quy ước trạng thái đã chọn cho nội dung rõ ràng chưa chốt.

**Lỗi chấm tự động:** hạ tầng: status kỳ vọng &#x27;unresolved&#x27;, thực tế &#x27;needs_confirmation&#x27;

[Output](data/benchmarks/results/ollama/11_unresolved_budget.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Thiếu dữ liệu để chọn không được biến thành quyết định hoặc việc chuyển dữ liệu.

### 12_reopen_confirmed — Mở lại quyết định đã chốt vì thông tin mới

[Transcript](data/examples/12_reopen_confirmed.txt) · [Kỳ vọng JSON](tests/fixtures/12_reopen_confirmed.expected.json)

**Kỳ vọng:** unresolved/phát hành: hoãn bản 2.1 (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: issue/Lỗi hoàn tiền: Lỗi tái hiện được ở hai giao dịch liên tiếp, số tiền hoàn bị ghi hai lần. (unresolved; người=None; hạn=None). Evidence: T4, T6, T7, T8, T10. Diễn biến: T4, T6, T7, T8, T10.
- Cách ly: unresolved/Phát hành bản 2.1: Chốt phát hành bản 2.1 vào thứ Hai. (confirmed; người=None; hạn=None). Evidence: T3, T8, T10, T12. Diễn biến: T3, T8, T10, T12. Lỗi guard: Nội dung chưa chốt không thể có trạng thái đã xác định

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Candidate vẫn giữ câu phát hành thứ Hai từ T3, dù evidence có T12 hoãn. unresolved/confirmed mâu thuẫn và bị chặn; không phải chỉ lỗi viết tên topic. Issue hoàn tiền có nguồn.

**Lỗi chấm tự động:** Thiếu/sai unresolved: phát hành / hoãn bản 2.1; Mục ngoài kỳ vọng: issue / Lỗi hoàn tiền / Lỗi tái hiện được ở hai giao dịch liên tiếp, số tiền hoàn bị ghi hai lần.; 1 mục không qua validator; Thiếu diễn biến T3; Thiếu diễn biến T12

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/12_reopen_confirmed.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/phát hành: Chưa chốt lịch phát hành bản 2.1; hoãn để đánh giá lỗi hoàn tiền. (needs_confirmation; người=None; hạn=None). Evidence: T8, T12. Diễn biến: T3, T8, T12.
- Nhận: issue/lỗi hoàn tiền: Lỗi hoàn tiền tái hiện được ở hai giao dịch liên tiếp, số tiền hoàn bị ghi hai lần. (unresolved; người=None; hạn=None). Evidence: T4, T5, T6. Diễn biến: T4, T5, T6, T7, T10, T12.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ câu hoãn T12 nhưng type decision thay unresolved. Issue hoàn tiền có bằng chứng T6, không phạt chỉ vì gold chưa liệt kê; lỗi chính vẫn là loại của kết luận mở lại.

**Lỗi chấm tự động:** Thiếu/sai unresolved: phát hành / hoãn bản 2.1; Mục ngoài kỳ vọng: decision / phát hành / Chưa chốt lịch phát hành bản 2.1; hoãn để đánh giá lỗi hoàn tiền.; Mục ngoài kỳ vọng: issue / lỗi hoàn tiền / Lỗi hoàn tiền tái hiện được ở hai giao dịch liên tiếp, số tiền hoàn bị ghi hai lần.

[Output](data/benchmarks/results/ollama/12_reopen_confirmed.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Lời hoãn sau cùng làm lần chốt trước hết hiệu lực; không tự biến lịch cũ thành hạn sửa lỗi.

### 13_speakerless_pending — Transcript không nhãn kết thúc mà chưa chọn

[Transcript](data/examples/13_speakerless_pending.txt) · [Kỳ vọng JSON](tests/fixtures/13_speakerless_pending.expected.json)

**Kỳ vọng:** unresolved/xuất báo cáo: chưa thống nhất (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/cách xuất báo cáo: Cần hiểu rõ mục đích sử dụng dữ liệu trước khi quyết định cách tải. (unresolved; người=None; hạn=None). Evidence: T1, T2, T3, T4, T5, T6, T7, T9, T10, T12. Diễn biến: T12.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Ghi cần hiểu mục đích trước khi quyết định cách tải với unresolved/unresolved; evidence T12 nêu chưa thống nhất. Nội dung cùng câu hỏi mở, khác chuỗi chưa thống nhất và tên topic fixture.

**Lỗi chấm tự động:** Thiếu/sai unresolved: xuất báo cáo / chưa thống nhất; Mục ngoài kỳ vọng: unresolved / cách xuất báo cáo / Cần hiểu rõ mục đích sử dụng dữ liệu trước khi quyết định cách tải.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/13_speakerless_pending.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: unresolved/cách xuất báo cáo: Hôm nay chưa thống nhất cách xuất báo cáo, mình giữ cả hai lựa chọn để hỏi khách. (needs_confirmation; người=None; hạn=None). Evidence: T12, T13, T14. Diễn biến: T12, T13, T14.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Tên cách xuất báo cáo là cùng đối tượng; content chưa thống nhất đúng T12. Tuy nhiên status needs_confirmation thay unresolved vẫn là sai trạng thái, không tính toàn case đạt.

**Lỗi chấm tự động:** Thiếu/sai unresolved: xuất báo cáo / chưa thống nhất; Mục ngoài kỳ vọng: unresolved / cách xuất báo cáo / Hôm nay chưa thống nhất cách xuất báo cáo, mình giữ cả hai lựa chọn để hỏi khách.

[Output](data/benchmarks/results/ollama/13_speakerless_pending.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Dữ liệu không có nhãn người nói vẫn đủ để nhận ra chưa có kết luận; cần báo lỗi parser như một thất bại hỗ trợ input.

### 14_request_not_assignment — Yêu cầu của khách không tự thành việc đã giao

[Transcript](data/examples/14_request_not_assignment.txt) · [Kỳ vọng JSON](tests/fixtures/14_request_not_assignment.expected.json)

**Kỳ vọng:** request_feedback/báo cáo: bộ lọc theo tháng (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/báo cáo: chưa thống nhất (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Cách ly: issue/Yêu cầu mới từ khách hàng: Khách hàng muốn có bộ lọc theo tháng trên màn hình báo cáo. (unresolved; người=None; hạn=None). Evidence: không có. Diễn biến: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16. Lỗi guard: reason đang trống; Không có evidence

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Candidate giữ yêu cầu bộ lọc nhưng gán issue, không evidence và thiếu câu chưa chọn trường thời gian T12. Không tạo assignment là đúng nhưng chưa đủ trích xuất.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: báo cáo / bộ lọc theo tháng; Thiếu/sai unresolved: báo cáo / chưa thống nhất; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/14_request_not_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: issue/bộ lọc theo thời gian: Yêu cầu từ khách cần làm rõ trước khi giao việc. (unresolved; người=None; hạn=None). Evidence: T10, T9, T12. Diễn biến: T10, T9, T12.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Không biến yêu cầu thành assignment là đúng, nhưng mất nội dung bộ lọc theo tháng T2 và câu chưa thống nhất trường thời gian T12; chỉ còn một issue chung chung.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: báo cáo / bộ lọc theo tháng; Thiếu/sai unresolved: báo cáo / chưa thống nhất; Mục ngoài kỳ vọng: issue / bộ lọc theo thời gian / Yêu cầu từ khách cần làm rõ trước khi giao việc.

[Output](data/benchmarks/results/ollama/14_request_not_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Dữ liệu có và thiếu nhãn xen kẽ phải được đưa vào test; yêu cầu không tự tạo owner hoặc deadline.

### 15_conditional_task — Lời nhận việc còn phụ thuộc quyền truy cập

[Transcript](data/examples/15_conditional_task.txt) · [Kỳ vọng JSON](tests/fixtures/15_conditional_task.expected.json)

**Kỳ vọng:** action/hoàn tiền: kiểm tra luồng hoàn tiền (needs_confirmation, owner=Lan, due=None, conditions=[&#x27;Nếu đối tác mở quyền sandbox&#x27;]); issue/sandbox: chưa mở quyền sandbox (needs_confirmation, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: issue/Vướng mắc là đối tác chưa mở quyền sandbox cho nhóm.: Đối tác chưa mở quyền sandbox. (confirmed; người=None; hạn=None). Evidence: T11. Diễn biến: T11.
- Nhận: unresolved/Nếu quyền không được mở thì mình phải bàn lại cách kiểm tra.: 如果权限未开放，则需要重新讨论测试方法。 (unresolved; người=None; hạn=None). Evidence: T13, T14. Diễn biến: T13, T14.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Bỏ lời Lan nhận kiểm tra hoàn tiền khi có sandbox T6; giữ blocker nhưng confirmed sai quy ước, thêm nội dung tiếng Trung. Không thay action có điều kiện bằng câu bàn lại cách thử.

**Lỗi chấm tự động:** Thiếu/sai action: hoàn tiền / kiểm tra luồng hoàn tiền; Thiếu/sai issue: sandbox / chưa mở quyền sandbox; Mục ngoài kỳ vọng: issue / Vướng mắc là đối tác chưa mở quyền sandbox cho nhóm. / Đối tác chưa mở quyền sandbox.; Mục ngoài kỳ vọng: unresolved / Nếu quyền không được mở thì mình phải bàn lại cách kiểm tra. / 如果权限未开放，则需要重新讨论测试方法。

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/15_conditional_task.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: issue/vướng mắc: Đối tác chưa mở quyền sandbox cho nhóm, dẫn đến việc không thể chạy luồng tích hợp từ đầu đến cuối. (unresolved; người=None; hạn=None). Evidence: T11, T13. Diễn biến: T4, T5, T6, T7, T8.
- Nhận: issue/luồng tích hợp: Nhóm chưa chạy được luồng tích hợp từ đầu đến cuối. (unresolved; người=None; hạn=None). Evidence: T4, T5, T6, T7, T8. Diễn biến: T4, T5, T6, T7, T8.
- Nhận: issue/quyền truy cập: Lỗi này thuộc quyền truy cập, chưa phải lỗi của luồng hoàn tiền. (confirmed; người=None; hạn=None). Evidence: T15, T16. Diễn biến: T15, T16.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ vấn đề quyền truy cập, nhưng bỏ công việc Lan nhận kiểm tra hoàn tiền khi có sandbox T6. Ba issue không thay thế action có điều kiện.

**Lỗi chấm tự động:** Thiếu/sai action: hoàn tiền / kiểm tra luồng hoàn tiền; Thiếu/sai issue: sandbox / chưa mở quyền sandbox; Mục ngoài kỳ vọng: issue / vướng mắc / Đối tác chưa mở quyền sandbox cho nhóm, dẫn đến việc không thể chạy luồng tích hợp từ đầu đến cuối.; Mục ngoài kỳ vọng: issue / luồng tích hợp / Nhóm chưa chạy được luồng tích hợp từ đầu đến cuối.; Mục ngoài kỳ vọng: issue / quyền truy cập / Lỗi này thuộc quyền truy cập, chưa phải lỗi của luồng hoàn tiền.

[Output](data/benchmarks/results/ollama/15_conditional_task.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Lời nhận việc có điều kiện không được nâng thành cam kết vô điều kiện hoặc tự thêm hạn từ lịch demo.

### 16_clear_decision — Chốt lịch phát hành sau khi xác nhận đủ điều kiện

[Transcript](data/examples/16_clear_decision.txt) · [Kỳ vọng JSON](tests/fixtures/16_clear_decision.expected.json)

**Kỳ vọng:** decision/phát hành: bản 2.1 (confirmed, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Phát hành bản 2.1: Đưa bản 2.1 lên phát hành vào thứ Hai. (confirmed; người=None; hạn=None). Evidence: T11, T12. Diễn biến: T1, T6, T8, T10, T11.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Quyết định 2.1 thứ Hai có evidence T11/T12, owner/due null hợp schema. Topic Phát hành bản 2.1 khác tên ngắn của fixture.

**Lỗi chấm tự động:** Thiếu/sai decision: phát hành / bản 2.1; Mục ngoài kỳ vọng: decision / Phát hành bản 2.1 / Đưa bản 2.1 lên phát hành vào thứ Hai.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/16_clear_decision.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: decision/phát hành: Chốt đưa bản 2.1 lên vào thứ Hai. (confirmed; người=None; hạn=thứ Hai). Evidence: T11, T8, T9, T10, T12. Diễn biến: T8, T9, T10, T11, T12. Lỗi guard: Chỉ công việc được có người nhận hoặc hạn

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng/schema.

**Nhận xét chấm đọc:** Candidate giữ đúng quyết định phát hành 2.1 vào thứ Hai T11. due không được phép nằm trên decision nên bị guard chặn; thời điểm đó có thật, không phải ngày bịa. Ngữ nghĩa candidate đúng nhưng chưa dùng được.

**Lỗi chấm tự động:** Thiếu/sai decision: phát hành / bản 2.1; 1 mục không qua validator

[Output](data/benchmarks/results/ollama/16_clear_decision.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Tình huống tường minh vẫn cần có trong suite để kiểm tra kết luận còn hiệu lực khi cuộc họp kết thúc.

### 17_clear_assignment — Quyết định và công việc thiếu một trường được tách riêng

[Transcript](data/examples/17_clear_assignment.txt) · [Kỳ vọng JSON](tests/fixtures/17_clear_assignment.expected.json)

**Kỳ vọng:** decision/báo cáo: biểu đồ đường (confirmed, owner=None, due=None, conditions=[]); request_feedback/nhãn biểu đồ: chữ quá nhỏ (needs_confirmation, owner=None, due=None, conditions=[]); action/tài liệu: cập nhật tài liệu (confirmed, owner=Lan, due=None, conditions=[]); action/bảo mật: rà soát quyền truy cập (needs_confirmation, owner=None, due=thứ Hai, conditions=[]); issue/đăng nhập: chưa có quyền sandbox (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/phân quyền: cách cấp quyền (unresolved, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Biểu đồ cho báo cáo: Dùng biểu đồ đường trên màn hình báo cáo. (confirmed; người=None; hạn=None). Evidence: T5, T6, T7. Diễn biến: T1, T2, T3, T5.
- Nhận: action/Rà soát quyền truy cập: Rà soát quyền truy cập trước thứ Hai. (needs_confirmation; người=None; hạn=trước thứ Hai). Evidence: T12, T13. Diễn biến: không có.
- Nhận: issue/Luồng thử đăng nhập: Chưa có quyền sandbox để thử luồng đăng nhập của khách. (unresolved; người=None; hạn=None). Evidence: T19, T20. Diễn biến: không có.
- Nhận: issue/Phân quyền cho khách: Chưa thống nhất cách cấp quyền cho khách. (unresolved; người=None; hạn=None). Evidence: T22, T23. Diễn biến: không có.
- Cách ly: action/Cập nhật tài liệu sử dụng: Lan cập nhật tài liệu sử dụng. (confirmed; người=None; hạn=None). Evidence: T8, T9. Diễn biến: không có. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Có biểu đồ đường và audit trước thứ Hai; mất phản hồi chữ nhỏ, owner Lan không vào trường, sandbox và phân quyền sai loại/trạng thái. Case nhiều nhóm chưa đủ.

**Lỗi chấm tự động:** Thiếu/sai decision: báo cáo / biểu đồ đường; Thiếu/sai request_feedback: nhãn biểu đồ / chữ quá nhỏ; Thiếu/sai action: tài liệu / cập nhật tài liệu; Thiếu/sai action: bảo mật / rà soát quyền truy cập; Thiếu/sai issue: đăng nhập / chưa có quyền sandbox; Thiếu/sai unresolved: phân quyền / cách cấp quyền; Mục ngoài kỳ vọng: decision / Biểu đồ cho báo cáo / Dùng biểu đồ đường trên màn hình báo cáo.; Mục ngoài kỳ vọng: action / Rà soát quyền truy cập / Rà soát quyền truy cập trước thứ Hai.; Mục ngoài kỳ vọng: issue / Luồng thử đăng nhập / Chưa có quyền sandbox để thử luồng đăng nhập của khách.; Mục ngoài kỳ vọng: issue / Phân quyền cho khách / Chưa thống nhất cách cấp quyền cho khách.; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/17_clear_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/báo cáo: Chốt dùng biểu đồ đường trên màn hình báo cáo. (confirmed; người=None; hạn=None). Evidence: T5, T6. Diễn biến: T1, T2, T3, T4, T5.
- Nhận: action/tài liệu: Cần hướng dẫn dùng bố cục mới. (needs_confirmation; người=Lan; hạn=None). Evidence: T8, T9. Diễn biến: T8, T9.
- Nhận: action/bảo mật: Cần rà soát quyền truy cập trước thứ Hai. (needs_confirmation; người=None; hạn=None). Evidence: T12, T13. Diễn biến: T12, T13, T15.
- Nhận: issue/luồng thử đăng nhập: Chưa có quyền sandbox để thử luồng đăng nhập của khách. (unresolved; người=None; hạn=None). Evidence: T19, T20. Diễn biến: T19, T20.
- Nhận: issue/phân quyền: Chưa thống nhất cách cấp quyền cho khách, giữ câu hỏi đó cho buổi trao đổi tiếp. (unresolved; người=None; hạn=None). Evidence: T22, T23. Diễn biến: T22, T23.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Đúng biểu đồ đường và giữ người nhận Lan, nhưng mất phản hồi nhãn chữ T7; sai status việc tài liệu đã nhận T9; mất due T13 và ghi phân quyền chưa chốt thành issue.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: nhãn biểu đồ / chữ quá nhỏ; Thiếu/sai action: tài liệu / cập nhật tài liệu; bảo mật: due kỳ vọng &#x27;thứ Hai&#x27;, thực tế None; Thiếu/sai issue: đăng nhập / chưa có quyền sandbox; Thiếu/sai unresolved: phân quyền / cách cấp quyền; Mục ngoài kỳ vọng: action / tài liệu / Cần hướng dẫn dùng bố cục mới.; Mục ngoài kỳ vọng: issue / luồng thử đăng nhập / Chưa có quyền sandbox để thử luồng đăng nhập của khách.; Mục ngoài kỳ vọng: issue / phân quyền / Chưa thống nhất cách cấp quyền cho khách, giữ câu hỏi đó cho buổi trao đổi tiếp.

[Output](data/benchmarks/results/ollama/17_clear_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Thiếu hạn và thiếu người là hai trường hợp khác nhau; giữ null thay vì chuyển thông tin từ việc bên cạnh.

### 18_anonymous_assignment — Cam kết đã rõ, danh tính người nhận chưa rõ

[Transcript](data/examples/18_anonymous_assignment.txt) · [Kỳ vọng JSON](tests/fixtures/18_anonymous_assignment.expected.json)

**Kỳ vọng:** action/kiểm thử: kiểm thử hồi quy (needs_confirmation, owner=None, due=thứ Sáu, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Cách ly: action/Kiểm thử hồi quy: Người nói 2 nhận làm kiểm thử hồi quy trước thứ Sáu. (confirmed; người=Người nói 2; hạn=thứ Sáu). Evidence: T6, T7. Diễn biến: không có. Lỗi guard: Người phụ trách thiếu bằng chứng giao việc hoặc tự nhận việc

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Người nói 2 được dùng làm owner/confirmed; đây là nhãn chứ chưa phải danh tính. Guard chặn, cần giữ null và needs_confirmation.

**Lỗi chấm tự động:** Thiếu/sai action: kiểm thử / kiểm thử hồi quy; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/18_anonymous_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: action/kiểm thử: Kiểm thử ba loại khuyến mãi: giảm phần trăm, giảm tiền và mua theo bộ. Mỗi loại cần thử cả lúc thêm và xóa sản phẩm. (confirmed; người=Người nói 2; hạn=trước thứ Sáu). Evidence: T6, T9. Diễn biến: T5, T6, T14. Lỗi guard: Người phụ trách thiếu bằng chứng giao việc hoặc tự nhận việc

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Công việc có thật T6, nhưng owner Người nói 2 không phải danh tính; status confirmed sai với actor chưa biết. Guard chặn trước khi xuất.

**Lỗi chấm tự động:** Thiếu/sai action: kiểm thử / kiểm thử hồi quy; 1 mục không qua validator

[Output](data/benchmarks/results/ollama/18_anonymous_assignment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Không đồng nhất nhãn diarization với tên thật; có thể giữ evidence nhưng owner cần để null.

### 19_speakerless_commitment — Có việc và hạn, không có dữ liệu xác định người nhận

[Transcript](data/examples/19_speakerless_commitment.txt) · [Kỳ vọng JSON](tests/fixtures/19_speakerless_commitment.expected.json)

**Kỳ vọng:** action/hướng dẫn: thay ảnh hướng dẫn (needs_confirmation, owner=None, due=ngày mai, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Cách ly: action/Thay ảnh hướng dẫn: Người nhận việc thay ba ảnh hướng dẫn và kiểm tra lại thứ tự bước trước ngày mai. (confirmed; người=None; hạn=trước ngày mai). Evidence: T4, T5. Diễn biến: T4, T5. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ việc thay ảnh/hạn nhưng confirmed với owner null sai khi không xác định người nói. Guard chặn, chưa giải quyết bất định danh tính.

**Lỗi chấm tự động:** Thiếu/sai action: hướng dẫn / thay ảnh hướng dẫn; 1 mục không qua validator

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/19_speakerless_commitment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: action/hướng dẫn: Thay ảnh hướng dẫn cho ba bước. (confirmed; người=Speaker null (T5); hạn=ngày mai). Evidence: T5, T7. Diễn biến: T5, T7. Lỗi guard: Người phụ trách thiếu bằng chứng giao việc hoặc tự nhận việc

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Công việc/hạn có nguồn T5, nhưng owner Speaker null (T5) là định danh tự tạo; cần null và needs_confirmation. Guard chặn.

**Lỗi chấm tự động:** Thiếu/sai action: hướng dẫn / thay ảnh hướng dẫn; 1 mục không qua validator

[Output](data/benchmarks/results/ollama/19_speakerless_commitment.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Một lời tự nhận rõ không cho phép bịa danh tính khi transcript không có người nói.

### 20_explicit_name_in_content — Người nói Huy giao việc cho Mai

[Transcript](data/examples/20_explicit_name_in_content.txt) · [Kỳ vọng JSON](tests/fixtures/20_explicit_name_in_content.expected.json)

**Kỳ vọng:** action/báo cáo: gửi báo cáo (confirmed, owner=Mai, due=thứ Sáu, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: action/Gửi báo cáo đã đối soát: Mai gửi báo cáo đã đối soát trước thứ Sáu. (confirmed; người=Mai; hạn=thứ Sáu). Evidence: T9, T10. Diễn biến: không có.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Mai gửi báo cáo đúng T9/T10, hạn thứ Sáu đúng và không tạo việc đối soát mới. Topic dài hơn báo cáo, không nhầm đối tượng.

**Lỗi chấm tự động:** Thiếu/sai action: báo cáo / gửi báo cáo; Mục ngoài kỳ vọng: action / Gửi báo cáo đã đối soát / Mai gửi báo cáo đã đối soát trước thứ Sáu.

[Output](data/benchmarks/comparisons/qwen2.5-7b/v2/baseline_b/20_explicit_name_in_content.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: action/báo cáo tháng: Mai gửi báo cáo đã đối soát trước thứ Sáu. (confirmed; người=Mai; hạn=thứ Sáu). Evidence: T9, T10. Diễn biến: T9, T10.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Huy giao Mai ở T9, Mai xác nhận T10. Output đúng Mai/việc/hạn; báo cáo tháng và báo cáo cùng đối tượng, chỉ khác tên topic so với fixture.

**Lỗi chấm tự động:** Thiếu/sai action: báo cáo / gửi báo cáo; Mục ngoài kỳ vọng: action / báo cáo tháng / Mai gửi báo cáo đã đối soát trước thứ Sáu.

[Output](data/benchmarks/results/ollama/20_explicit_name_in_content.json) · [Bảng chấm đọc](data/benchmarks/reviews/v2_pipeline.json)

**Điều học được:** Tên người nhận ở trong nội dung có thể khác người nói; không dùng vị trí đầu dòng để suy ra owner.

## 6 case v3 — lượt đánh giá cuối

### H01_reminders — Đổi kênh nhắc lịch sau khi kiểm tra chi phí

[Transcript](data/holdout-v3/H01_reminders.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H01_reminders.expected.json)

**Kỳ vọng:** decision/nhắc lịch: thông báo trong ứng dụng (confirmed, owner=None, due=None, conditions=[&#x27;chỉ cho lịch đã xác nhận&#x27;])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Phương án nhắn lịch cho tuần thử nghiệm: Dùng thông báo trong ứng dụng, chỉ cho lịch đã xác nhận. SMS không dùng ở tuần thử này. (confirmed; người=None; hạn=None). Evidence: T15. Diễn biến: T3, T6, T15.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Đạt**. Phân loại: Định dạng.

**Nhận xét chấm đọc:** Giữ đúng thông báo trong ứng dụng chỉ cho lịch xác nhận T15, lịch sử SMS bị bỏ T3/T6. Topic nhắn lịch là cách viết lệch của nhắc lịch, cùng đối tượng.

**Lỗi chấm tự động:** Thiếu/sai decision: nhắc lịch / thông báo trong ứng dụng; Mục ngoài kỳ vọng: decision / Phương án nhắn lịch cho tuần thử nghiệm / Dùng thông báo trong ứng dụng, chỉ cho lịch đã xác nhận. SMS không dùng ở tuần thử này.; Thiếu diễn biến T2; Thiếu diễn biến T7

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H01_reminders.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/lịch demo: Chốt dùng thông báo trong ứng dụng, chỉ cho lịch đã xác nhận. SMS không dùng ở tuần thử này. (confirmed; người=None; hạn=None). Evidence: T15. Diễn biến: T15, T16, T17.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Nội dung nhắc lịch và điều kiện đúng T15 nhưng gắn lịch demo, là đối tượng khác; history bỏ diễn biến SMS T3/T6/T7. Verifier cùng model vẫn cho qua.

**Lỗi chấm tự động:** Thiếu/sai decision: nhắc lịch / thông báo trong ứng dụng; Mục ngoài kỳ vọng: decision / lịch demo / Chốt dùng thông báo trong ứng dụng, chỉ cho lịch đã xác nhận. SMS không dùng ở tuần thử này.; Thiếu diễn biến T2; Thiếu diễn biến T7

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H01_reminders.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Giữ kênh cuối và phạm vi lịch đã xác nhận; không tự tạo cơ chế SMS dự phòng.

### H02_conditional_export — Giao việc bằng tên trong transcript không có người nói

[Transcript](data/holdout-v3/H02_conditional_export.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H02_conditional_export.expected.json)

**Kỳ vọng:** request_feedback/xuất dữ liệu: CSV đã mã hóa (needs_confirmation, owner=None, due=None, conditions=[]); issue/pháp chế: chưa xác nhận (needs_confirmation, owner=None, due=None, conditions=[]); action/xuất dữ liệu: CSV đã mã hóa (needs_confirmation, owner=Ngọc, due=thứ Năm, conditions=[&#x27;sau khi pháp chế xác nhận&#x27;])

**Kết quả thực tế B — prompt đơn:**

- Nhận: action/Danh sách khách cho đợt thử: Ngọc xuất bản CSV đã mã hóa sau khi pháp chế xác nhận, hạn trước thứ Năm. (confirmed; người=Ngọc; hạn=trước thứ Năm). Evidence: T14, T15. Diễn biến: T6, T13, T14.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ điều kiện trong content nhưng action confirmed thay needs_confirmation; bỏ phản hồi CSV mã hóa và blocker pháp chế. Không chỉ sai tiền tố deadline.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: xuất dữ liệu / CSV đã mã hóa; Thiếu/sai issue: pháp chế / chưa xác nhận; Thiếu/sai action: xuất dữ liệu / CSV đã mã hóa; Mục ngoài kỳ vọng: action / Danh sách khách cho đợt thử / Ngọc xuất bản CSV đã mã hóa sau khi pháp chế xác nhận, hạn trước thứ Năm.

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H02_conditional_export.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: action/danh sách khách: Danh sách khách của đợt thử cần gửi cho đối tác để họ kiểm tra số liệu. (confirmed; người=Ngọc; hạn=trước thứ Năm). Evidence: T14, T16. Diễn biến: T6, T7, T8.
- Nhận: issue/pháp chế: Vướng mắc là pháp chế chưa xác nhận quyền xuất bản danh sách. (unresolved; người=None; hạn=None). Evidence: T6, T13. Diễn biến: T6, T13.
- Nhận: issue/hạn giao: Nếu trả lời của pháp chế đến muộn, hạn giao cũng cần được trao đổi lại. (unresolved; người=None; hạn=None). Evidence: T17. Diễn biến: T17.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Action mất CSV mã hóa và điều kiện pháp chế trong content, confirmed thay needs_confirmation; phản hồi bị bỏ và blocker sai trạng thái. Evidence chứa điều kiện không bù cho content đã bỏ điều kiện.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: xuất dữ liệu / CSV đã mã hóa; pháp chế: status kỳ vọng &#x27;needs_confirmation&#x27;, thực tế &#x27;unresolved&#x27;; Thiếu/sai action: xuất dữ liệu / CSV đã mã hóa; Mục ngoài kỳ vọng: action / danh sách khách / Danh sách khách của đợt thử cần gửi cho đối tác để họ kiểm tra số liệu.; Mục ngoài kỳ vọng: issue / hạn giao / Nếu trả lời của pháp chế đến muộn, hạn giao cũng cần được trao đổi lại.

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H02_conditional_export.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Tên người nhận đến từ nội dung giao việc; cam kết phụ thuộc pháp chế chưa thể coi là công việc vô điều kiện.

### H03_reopened_backup — Quyết định sao lưu được mở lại vì dung lượng

[Transcript](data/holdout-v3/H03_reopened_backup.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H03_reopened_backup.expected.json)

**Kỳ vọng:** unresolved/sao lưu: chưa chốt số ngày giữ bản sao (unresolved, owner=None, due=None, conditions=[]); issue/dung lượng: chưa có số liệu dung lượng (needs_confirmation, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/Thời gian giữ bản sao lưu: Hôm nay chưa chốt số ngày giữ bản sao, cả bảy, mười bốn và ba mươi ngày đều chưa được chọn. (unresolved; người=None; hạn=None). Evidence: T12, T13, T14, T15, T16, T17, T18. Diễn biến: T3, T12.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ chưa chốt số ngày và không hồi sinh 30 ngày, nhưng bỏ issue thiếu dung lượng T11. Lịch sử có T3/T12 nhưng thiếu lần đề xuất 14 ngày trong history.

**Lỗi chấm tự động:** Thiếu/sai unresolved: sao lưu / chưa chốt số ngày giữ bản sao; Thiếu/sai issue: dung lượng / chưa có số liệu dung lượng; Mục ngoài kỳ vọng: unresolved / Thời gian giữ bản sao lưu / Hôm nay chưa chốt số ngày giữ bản sao, cả bảy, mười bốn và ba mươi ngày đều chưa được chọn.; Thiếu diễn biến T8; Thiếu diễn biến T13; Thiếu diễn biến T16

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H03_reopened_backup.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: unresolved/lưu trữ: Hôm nay chưa chốt số ngày giữ bản sao, cả bảy, mười bốn và ba mươi ngày đều chưa được chọn. (needs_confirmation; người=None; hạn=None). Evidence: T16. Diễn biến: T3, T8, T12.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ chưa chốt số ngày, nhưng needs_confirmation thay unresolved và mất issue dung lượng T11. Không dùng đúng một câu nội dung để nhận cả case đạt.

**Lỗi chấm tự động:** Thiếu/sai unresolved: sao lưu / chưa chốt số ngày giữ bản sao; Thiếu/sai issue: dung lượng / chưa có số liệu dung lượng; Mục ngoài kỳ vọng: unresolved / lưu trữ / Hôm nay chưa chốt số ngày giữ bản sao, cả bảy, mười bốn và ba mươi ngày đều chưa được chọn.; Thiếu diễn biến T13; Thiếu diễn biến T16

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H03_reopened_backup.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Không giữ quyết định đã hủy; một phương án thay thế được nhắc đến chưa trở thành lựa chọn cuối.

### H04_discount_request — Phản hồi kinh doanh và lời nhận việc có điều kiện

[Transcript](data/holdout-v3/H04_discount_request.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H04_discount_request.expected.json)

**Kỳ vọng:** request_feedback/hạn mức giảm giá: 20% (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/hạn mức giảm giá: chưa chốt tăng hạn mức giảm giá (unresolved, owner=None, due=None, conditions=[]); action/hạn mức giảm giá: cập nhật bảng hạn mức giảm giá (needs_confirmation, owner=Huy, due=thứ Hai, conditions=[&#x27;Nếu tài chính xác nhận&#x27;])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/Hạn mức giảm giá: Phản hồi về tăng hạn mức giảm giá chưa chốt, chờ tài chính xác nhận. (unresolved; người=None; hạn=None). Evidence: T1, T2, T3, T4, T5, T6, T7, T8, T9. Diễn biến: T2, T10.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ câu chưa chốt tăng, nhưng bỏ phản hồi 20% và công việc Huy nhận có điều kiện T11. Một câu unresolved chưa bao phủ ba nhóm kỳ vọng.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: hạn mức giảm giá / 20%; Thiếu/sai unresolved: hạn mức giảm giá / chưa chốt tăng hạn mức giảm giá; Thiếu/sai action: hạn mức giảm giá / cập nhật bảng hạn mức giảm giá; Mục ngoài kỳ vọng: unresolved / Hạn mức giảm giá / Phản hồi về tăng hạn mức giảm giá chưa chốt, chờ tài chính xác nhận.

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H04_discount_request.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Cách ly: action/hạn mức giảm giá: Phần hạn mức giảm giá chưa chốt tăng trong buổi này. (confirmed; người=None; hạn=None). Evidence: T10, T9. Diễn biến: T10, T9. Lỗi guard: Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Ghi câu chưa chốt thành action confirmed không owner; guard chặn. Mất phản hồi 20% và việc Huy nhận có điều kiện.

**Lỗi chấm tự động:** Thiếu/sai request_feedback: hạn mức giảm giá / 20%; Thiếu/sai unresolved: hạn mức giảm giá / chưa chốt tăng hạn mức giảm giá; Thiếu/sai action: hạn mức giảm giá / cập nhật bảng hạn mức giảm giá; 1 mục không qua validator; Thiếu diễn biến T2; Thiếu diễn biến T10

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H04_discount_request.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Yêu cầu của kinh doanh chưa là quyết định; việc được nhận có điều kiện phải giữ điều kiện và chưa tự chuyển thành vô điều kiện.

### H05_webhook_limit — Chốt giới hạn webhook và người gửi báo cáo

[Transcript](data/holdout-v3/H05_webhook_limit.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H05_webhook_limit.expected.json)

**Kỳ vọng:** decision/webhook: gửi lại (confirmed, owner=None, due=None, conditions=[&#x27;tối đa ba lần&#x27;, &#x27;cách nhau 30 giây&#x27;, &#x27;trạng thái thất bại&#x27;]); action/kiểm tra webhook: báo cáo kiểm tra webhook (confirmed, owner=Mai, due=thứ Sáu, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: decision/Giới hạn gửi lại webhook: Gửi lại tối đa ba lần, cách nhau 30 giây; sau đó vẫn lỗi thì giữ trạng thái thất bại. (confirmed; người=None; hạn=None). Evidence: T13, T6, T7. Diễn biến: T1, T2, T3, T4, T5, T6, T7.
- Nhận: action/Báo cáo kiểm tra webhook: Mai gửi báo cáo kiểm tra webhook cho nhóm sau khi thử cấu hình này nhé. (confirmed; người=Mai; hạn=None). Evidence: T14, T15. Diễn biến: T14, T15.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Quyết định giới hạn đúng và giữ mọi điều kiện. Action Mai có nguồn T14/T15 nhưng due null và content cũng không giữ thứ Sáu; mất thông tin hạn, không chỉ sai cách viết trường.

**Lỗi chấm tự động:** Thiếu/sai decision: webhook / gửi lại; Thiếu/sai action: kiểm tra webhook / báo cáo kiểm tra webhook; Mục ngoài kỳ vọng: decision / Giới hạn gửi lại webhook / Gửi lại tối đa ba lần, cách nhau 30 giây; sau đó vẫn lỗi thì giữ trạng thái thất bại.; Mục ngoài kỳ vọng: action / Báo cáo kiểm tra webhook / Mai gửi báo cáo kiểm tra webhook cho nhóm sau khi thử cấu hình này nhé.; Thiếu diễn biến T13

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H05_webhook_limit.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: decision/webhook: Chốt gửi lại tối đa ba lần, cách nhau 30 giây; sau đó vẫn lỗi thì giữ trạng thái thất bại. (confirmed; người=None; hạn=None). Evidence: T13. Diễn biến: T6, T13.
- Nhận: action/webhook: Mai gửi báo cáo kiểm tra webhook cho nhóm sau khi thử cấu hình này nhé. (needs_confirmation; người=None; hạn=None). Evidence: T14, T15. Diễn biến: không có.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Định dạng + ngữ nghĩa.

**Nhận xét chấm đọc:** Giới hạn ba lần/30 giây/thất bại đúng. Việc Mai đã nhận bị để owner/due null và needs_confirmation, content mất thứ Sáu. Thiếu đề xuất gửi vô hạn T2 trong history.

**Lỗi chấm tự động:** Thiếu/sai action: kiểm tra webhook / báo cáo kiểm tra webhook; Mục ngoài kỳ vọng: action / webhook / Mai gửi báo cáo kiểm tra webhook cho nhóm sau khi thử cấu hình này nhé.; Thiếu diễn biến T2

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H05_webhook_limit.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Giữ giới hạn số lần/khoảng cách và trạng thái sau thất bại; giao và nhận cùng một báo cáo là một công việc.

### H06_unsettled_rota — Ok và để em xem chưa tạo người phụ trách lịch trực

[Transcript](data/holdout-v3/H06_unsettled_rota.txt) · [Kỳ vọng JSON](tests/fixtures/holdout-v3/H06_unsettled_rota.expected.json)

**Kỳ vọng:** unresolved/lịch trực: chưa thống nhất lịch trực (unresolved, owner=None, due=None, conditions=[]); issue/lịch làm việc: chưa có lịch làm việc (needs_confirmation, owner=None, due=None, conditions=[])

**Kết quả thực tế B — prompt đơn:**

- Nhận: unresolved/Lịch trực hỗ trợ trong đợt mở thử: Cần cân nhắc hai phương án: luân phiên hai người hoặc chia ca ba người, dựa trên lịch làm việc của nhóm hỗ trợ. (unresolved; người=None; hạn=None). Evidence: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18. Diễn biến: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Không bịa người trực/assignment, giữ hai phương án ở unresolved; bỏ issue chưa có lịch làm việc T10, nên chưa đủ case.

**Lỗi chấm tự động:** Thiếu/sai unresolved: lịch trực / chưa thống nhất lịch trực; Thiếu/sai issue: lịch làm việc / chưa có lịch làm việc; Mục ngoài kỳ vọng: unresolved / Lịch trực hỗ trợ trong đợt mở thử / Cần cân nhắc hai phương án: luân phiên hai người hoặc chia ca ba người, dựa trên lịch làm việc của nhóm hỗ trợ.

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/baseline_b/H06_unsettled_rota.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_baseline_b.json)

**Kết quả thực tế C — pipeline:**

- Nhận: unresolved/lịch trực hỗ trợ: Hôm nay chưa thống nhất lịch trực; chưa giao ai chốt danh sách. (needs_confirmation; người=None; hạn=None). Evidence: T10, T17, T18. Diễn biến: T10, T17, T18.

**Đạt/Chưa đạt:** tự động **Chưa đạt**; đọc ngữ nghĩa **Chưa đạt**. Phân loại: Ngữ nghĩa.

**Nhận xét chấm đọc:** Giữ câu chưa thống nhất nhưng status needs_confirmation thay unresolved, bỏ issue lịch làm việc và diễn biến hai/ba người. Không bịa assignment là điểm tốt.

**Lỗi chấm tự động:** Thiếu/sai unresolved: lịch trực / chưa thống nhất lịch trực; Thiếu/sai issue: lịch làm việc / chưa có lịch làm việc; Mục ngoài kỳ vọng: unresolved / lịch trực hỗ trợ / Hôm nay chưa thống nhất lịch trực; chưa giao ai chốt danh sách.; Thiếu diễn biến T2; Thiếu diễn biến T7

[Output](data/benchmarks/comparisons/qwen2.5-7b/holdout-v3/pipeline/H06_unsettled_rota.json) · [Bảng chấm đọc](data/benchmarks/reviews/holdout-v3_pipeline.json)

**Điều học được:** Không biến ok/để em xem thành một công việc đã giao; giữ thiếu danh tính thay vì tạo người phụ trách.

## Tái tạo báo cáo và kiểm tra code

```bash
python src test
python src report --check
python src compare --suite v2 --model qwen2.5:7b --report-only
python src compare --suite holdout-v3 --model qwen2.5:7b --report-only
```

Các lệnh trên không gọi model. Không chạy lại/tune v3 rồi vẫn gọi kết quả mới là kiểm thử kín. Một vòng phát triển tiếp theo cần bộ mới và protocol mới. Kết quả duyệt/xuất từng mục chưa được đánh giá trên đủ 26 case.
