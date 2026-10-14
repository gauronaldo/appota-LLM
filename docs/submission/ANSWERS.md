# Ba câu trả lời Mission 2

Bản nháp theo trạng thái code và suite v2. Tác giả cần sửa giọng và bổ sung những kiểm tra mình thực sự tự làm.

## 1. Phần quan trọng nhất chọn để hiện thực hóa là gì

Tôi chọn kết luận cuối theo chủ đề và evidence dẫn về transcript. Một phương án được nêu lúc đầu không thể được dùng như quyết định nếu cuối cuộc họp nó đã bị thay thế. Prototype tách diễn biến khỏi kết luận, chuẩn hóa dữ liệu và cho người dùng đối chiếu từng mục. Luồng local chạy được với những tình huống tường minh; pipeline LLM hai bước đã có code nhưng chưa chạy API thật. Vì vậy, điều đã chứng minh là khả năng tổ chức dữ liệu và truy vết ở mức prototype, chưa phải chất lượng AI. Nếu LLM xử lý đúng các chủ đề bị ngắt và kết luận có điều kiện trên bộ kiểm thử mới, hướng này mới có bằng chứng mạnh hơn về khả năng áp dụng cho cuộc họp thực.

## 2. Đã đổi gì so với Mission 1 và vì sao

Tôi bổ sung bộ quy tắc local để có bản chạy không cần API key, còn LLM là chế độ riêng. Đây là thay đổi so với chủ trương dùng prompt phân tích ngữ nghĩa trong Mission 1. Sau khi rà lại dữ liệu, tôi nhận ra bộ cũ có nhiều câu quá tường minh và cùng đoạn nhiễu lặp lại. Tôi viết suite v2 gồm 20 hội thoại có ngữ cảnh riêng, thêm nhãn ẩn danh, thiếu người nói và dữ liệu trộn. Kết quả local giảm còn 6/20; tôi giữ số liệu này vì nó bộc lộ giới hạn thật. Tôi cũng đổi evaluator để lỗi input vẫn là case chưa đạt, thay vì dừng cả bộ hoặc loại case khó khỏi mẫu số. Engine không được chỉnh theo suite mới.

## 3. Thông tin nào dễ ghi sai nhất và đang tránh dữ liệu không tồn tại thế nào

Các tham chiếu quay lại chủ đề, giao việc bằng câu tự nhiên và danh tính người nhận chưa rõ dễ sai nhất. Local có thể gắn câu chốt đúng chữ vào sai chủ đề, coi nhãn Người nói 2 là tên người nhận hoặc tạo công việc lặp khi một cam kết được nhắc lại. Tôi giữ evidence, history và bản tự động gốc, kiểm tra ID/quote/người/hạn bằng code rồi cho người dùng đối chiếu. Ground truth v2 yêu cầu giữ điều kiện và để owner null khi chỉ có nhãn chưa xác minh. Những biện pháp đó giúp phát hiện lỗi, chưa bảo đảm ngữ nghĩa đúng. Phần còn phải làm là hỗ trợ input thiếu nhãn, chạy LLM thật, xác minh kết luận và bắt buộc duyệt trước khi xuất biên bản đã duyệt.
