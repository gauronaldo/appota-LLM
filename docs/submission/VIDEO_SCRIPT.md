# Kịch bản video Mission 2 — suite v2

Khung 4 phút 40 giây, chừa 20 giây. Tác giả tự quay và cần tập có bấm giờ. Bản này thay kịch bản suite v1; không dùng số liệu 8/10 hoặc các ID lượt nói cũ.

Trước quay: chạy `python src`, mở localhost:8501, chọn local. Khi đổi mẫu, bấm Nạp transcript rồi Phân tích. Không quay key hoặc tài liệu riêng. Nếu dùng replay, nói rõ đang xem kết quả lưu sẵn.

| Mốc | Thao tác | Lời nói gợi ý |
| --- | --- | --- |
| 0:00–0:30 | Màn hình đầu | “Transcript có đề xuất, phản đối và kết luận. Ghi nhầm phương án đã bỏ thành quyết định có thể khiến nhóm làm sai hướng. Tôi tập trung vào kết luận cuối và nguồn để kiểm tra.” |
| 0:30–1:00 | Chỉ bộ local | “Core loop là transcript, diễn biến theo chủ đề, dữ liệu có cấu trúc và evidence. LLM hai bước đã có code, nhưng chưa chạy API thật. Demo hôm nay là bộ quy tắc local, chưa chứng minh chất lượng AI.” |
| 1:00–2:00 | Mẫu Bỏ máy chủ riêng, chọn dịch vụ quản lý | “Nhóm bàn A rồi chốt B. Kết quả chỉ giữ B là quyết định, A nằm trong diễn biến. Bấm evidence tìm câu gốc. Việc cấu hình có Lan và hạn thứ Sáu; người dùng đối chiếu, xác nhận hoặc sửa, rồi xuất JSON có lịch sử.” Mở history, bấm evidence của quyết định và việc cấu hình. Không đọc cả transcript. |
| 2:00–2:50 | Mẫu Quay lại chuyện lưu trữ sau khi bàn lịch demo | “Đây là lỗi thật. Người nói quay lại lưu trữ bằng ‘chuyện đầu tiên’, nhưng local gắn câu chốt B vào lịch demo. Quote vẫn đúng chữ. Kiểm tra nguồn chưa bảo đảm hiểu đúng ngữ cảnh.” Chỉ chủ đề sai và câu quay lại trong transcript. |
| 2:50–3:20 | Mẫu Người nhận được nêu trong nội dung, không biết ai nói | “Câu Lan gửi báo cáo vẫn có việc và người nhận, dù không biết ai phát biểu. Parser hiện chưa nhận input không nhãn, nên case này thất bại. Tôi giữ nó trong test, không thêm tên để thuật toán dễ chạy.” Bấm Phân tích để hiện lỗi, hoặc replay và báo rõ đó là lỗi đã lưu. |
| 3:20–3:55 | Bộ kiểm thử | “Suite v2 gồm 20 hội thoại với ngữ cảnh riêng, có tên, nhãn ẩn danh, không nhãn và dữ liệu trộn. Local đạt 6/12 phát triển và 0/8 kín. Tỷ lệ thấp cho thấy bộ quy tắc còn phụ thuộc dữ liệu tường minh; đây là kết quả để chẩn đoán giới hạn, không phải chất lượng LLM.” |
| 3:55–4:40 | README hoặc giữ UI | “Tôi chưa sửa engine theo các lỗi mới. Bước tiếp là hỗ trợ input thiếu người nói, xử lý danh tính/công việc lặp, chạy LLM và kiểm tra ngữ nghĩa thật. Cần hoàn thiện duyệt trước xuất, so với một prompt mạnh và đo thời gian PM hoàn thành biên bản. Prototype đã có luồng dữ liệu và truy vết, nhưng chất lượng với hội thoại tự nhiên chưa đạt.” |

Các mốc là ngân sách thời gian, không bảo đảm tốc độ nói. Nếu vượt, cắt việc mở JSON và rút bộ kiểm thử xuống một câu; giữ demo tốt, lỗi thật và thông tin LLM chưa chạy. Không nói “AI chính xác 30%”, “có evidence nên đúng” hoặc “hệ thống chỉ cho xuất sau khi duyệt xong”. 6/20 là tỷ lệ case local trên suite tổng hợp, không phải độ chính xác AI.
