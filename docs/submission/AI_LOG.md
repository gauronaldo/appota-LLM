# Nhật ký AI và phạm vi kiểm chứng

Codex hỗ trợ viết source, giao diện, schema, prompt, validator, test, tài liệu và các hội thoại tổng hợp. Không huấn luyện/fine-tune model trong project; API LLM chưa được chạy thật.

Suite v1 ban đầu có câu tường minh và đoạn nhiễu chung; được lưu riêng ở workspace local. Theo yêu cầu tác giả, suite v2 được viết lại thành 20 hội thoại có ngữ cảnh riêng, bốn nhóm và bốn dạng thông tin người nói. Kỳ vọng được viết và hash trước lượt chạy, có rà nội dung bởi cùng tác giả AI; chưa có người gán nhãn độc lập. Engine/prompt không chỉnh theo kết quả v2.

Đã chạy local v2: 6/12 phát triển, 0/8 kín. Báo cáo giữ lỗi input, topic, owner, điều kiện và công việc lặp. Evaluator được bổ sung ghi lỗi input thành case chưa đạt, chấm điều kiện, và báo riêng nhóm/định dạng. API mock tests không được coi là bằng chứng chất lượng LLM.

Showcase chỉ đưa lên Git source, dữ liệu tổng hợp, kỳ vọng, output v2, cấu hình CI và tài liệu nộp cần thiết. Không đưa môi trường chạy, key, export người dùng, tài liệu Word nguồn hoặc ghi chú cá nhân vào repo.

Tác giả cần bổ sung bằng việc thực sự đã làm:

- Tôi tự đọc/chạy những phần nào: …
- Tôi xác minh kỳ vọng và các case thiếu người nói như thế nào: …
- Nội dung do AI tạo tôi đã sửa hoặc không đồng ý: …
- Model và kết quả API thật khi có key: …
- Link video sau khi tự quay: …

Không đổi các ô trên thành khẳng định đã kiểm tra nếu chưa thực hiện.
