# Bộ kiểm thử Mission 2 — suite v2

Bộ đã chạy: **local**. Kết quả thực tế: **6/20** case đạt.

Suite v2 có 20 hội thoại tiếng Việt tổng hợp, 15–24 lượt mỗi case, chia bốn nhóm × năm case. Mỗi cuộc họp có ngữ cảnh riêng; không chèn chung một đoạn hội thoại nhiễu hoặc bắt mọi câu lặp “Về chủ đề”. Đây không phải transcript thu từ người dùng thật và chưa được người gán nhãn độc lập kiểm tra.

Có tên rõ, nhãn Người nói 1/2, không có nhãn và dữ liệu trộn. 12 case phát triển / 8 case kín. Kỳ vọng và hash được viết trước khi chạy engine; không chỉnh core/prompt theo suite mới. Bộ v1 cũ được giữ riêng ở workspace local, không trộn số liệu 8/10 cũ với kết quả v2.

Input parser hiện bắt buộc người nói. Case không được parser hỗ trợ vẫn có kết quả kỳ vọng và được ghi **Chưa đạt**, kèm lỗi thật; không loại khỏi mẫu số và không nhận kết quả rỗng là đạt.

Matching một-một theo loại/chủ đề/nội dung, kiểm tra trạng thái, owner, due, ID evidence và điều kiện được gán nhãn. Matching chuỗi có thể đánh trượt cách diễn đạt tương đương; số liệu không thay thế đánh giá ngữ nghĩa bởi người đọc. Nhãn ẩn danh chưa được coi là tên người nhận đã xác minh.

Metric trung gian dựa trên ID và evidence của quyết định sai; một câu chốt bị gắn sai chủ đề vẫn có thể không làm metric này tăng. Xem cả precision/recall và sai lệch từng case.

**Chưa có kết quả LLM API thật. Số liệu local không chứng minh chất lượng AI, không phải phép đo thời gian PM duyệt hoặc baseline LLM A/B/C.**

## Phát triển

Đạt **6/12**; decision precision **0.8**, recall **0.8**. TP/FP/FN: 4/1/1. Trung gian nâng sai: 0/11; owner/due ngoài kỳ vọng: 3.

Run UTC: 2026-10-14T07:24:59.494950+00:00; dataset 2.0; prompt 1.0.

| Nhóm | Đạt / tổng |
| --- | --- |
| Đổi phương án | 2/3 |
| Chốt / giao việc rõ | 1/3 |
| Chốt gián tiếp / cam kết | 1/3 |
| Chưa thống nhất | 2/3 |

| Dữ liệu người nói | Đạt / tổng |
| --- | --- |
| Nhãn ẩn danh | 0/3 |
| Có tên | 6/8 |
| Không có người nói | 0/1 |

### 01_change_ab — Bỏ máy chủ riêng, chọn dịch vụ quản lý

- **Kỳ vọng:** decision/lưu trữ: phương án B (confirmed, owner=None, due=None, conditions=[]); action/triển khai: bản cấu hình (confirmed, owner=Lan, due=thứ Sáu, conditions=[])
- **Kết quả thực tế:** decision/lưu trữ: Chốt dùng phương án B cho bản thử. Chưa mua máy chủ riêng ở đợt này. (confirmed, owner=None, due=None); action/triển khai: Em nhận làm bản cấu hình trước thứ Sáu. (confirmed, owner=Lan, due=thứ Sáu)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Giữ B là quyết định cuối; hội thoại không cần nhắc lại tên chủ đề ở mọi lượt.

### 02_change_aba — Lịch demo đổi sang chiều rồi quay lại buổi sáng

- **Kỳ vọng:** decision/lịch demo: phương án A (confirmed, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** decision/lịch demo: chốt quay về phương án A, sáng thứ Năm. (confirmed, owner=None, due=None)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Một lần chốt giữa cuộc họp có thể bị thay; phải theo dõi lần quay lại A.

### 03_switch_condition — Đổi nhà cung cấp nhưng giữ điều kiện phê duyệt

- **Kỳ vọng:** decision/email: gói B (confirmed, owner=None, due=None, conditions=['nếu pháp chế duyệt'])
- **Kết quả thực tế:** decision/chưa xác định chủ đề: Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu. (confirmed, owner=None, due=None)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Điều kiện là một phần của quyết định; không được biến chọn có điều kiện thành quyền triển khai ngay.

Sai lệch: Thiếu/sai decision: email / gói B; Mục ngoài kỳ vọng: decision / chưa xác định chủ đề / Chốt chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu.

### 06_ambiguous_ok — Một câu ok có thể chỉ là đã nghe

- **Kỳ vọng:** unresolved/thanh toán: ví điện tử (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** unresolved/thanh toán: Chưa chốt chuyện thêm ví điện tử ở đợt này. (unresolved, owner=None, due=None)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Ok có thể là tín hiệu nghe được, không phải đồng thuận; lời cuối xác nhận đề xuất chưa chốt.

### 07_let_me_check — Để em xem lỗi này chưa thành lời nhận sửa

- **Kỳ vọng:** issue/đăng nhập: chưa tái hiện (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/đăng nhập: xem lỗi (needs_confirmation, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** issue/chưa xác định chủ đề: Vướng mắc là chưa tái hiện được lỗi đăng nhập trên môi trường thử. (needs_confirmation, owner=None, due=None)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Không biến ý định xem xét thành cam kết sửa; cần giữ sự mơ hồ để PM xác nhận.

Sai lệch: Thiếu/sai issue: đăng nhập / chưa tái hiện; Thiếu/sai unresolved: đăng nhập / xem lỗi; Mục ngoài kỳ vọng: issue / chưa xác định chủ đề / Vướng mắc là chưa tái hiện được lỗi đăng nhập trên môi trường thử.

### 08_self_commit_label — Có cam kết rõ nhưng chỉ có nhãn người nói

- **Kỳ vọng:** action/giỏ hàng: xem lỗi (needs_confirmation, owner=None, due=chiều nay, conditions=[])
- **Kết quả thực tế:** Không có mục
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Cam kết và hạn có thật; nhãn người nói chưa phải tên người nhận việc đã xác minh.

Sai lệch: Thiếu/sai action: giỏ hàng / xem lỗi

### 11_unresolved_budget — Thiếu báo giá nên chưa chọn phương án

- **Kỳ vọng:** unresolved/hạ tầng: hoãn lựa chọn (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** unresolved/hạ tầng: Chưa chốt phương án hạ tầng; hoãn lựa chọn đến khi đủ báo giá. (unresolved, owner=None, due=None)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Thiếu dữ liệu để chọn không được biến thành quyết định hoặc việc chuyển dữ liệu.

### 12_reopen_confirmed — Mở lại quyết định đã chốt vì thông tin mới

- **Kỳ vọng:** unresolved/phát hành: hoãn bản 2.1 (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** unresolved/phát hành: Chưa chốt lịch phát hành nữa; hoãn bản 2.1 để đánh giá lỗi hoàn tiền. (unresolved, owner=None, due=None)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Lời hoãn sau cùng làm lần chốt trước hết hiệu lực; không tự biến lịch cũ thành hạn sửa lỗi.

### 13_speakerless_pending — Transcript không nhãn kết thúc mà chưa chọn

- **Kỳ vọng:** unresolved/xuất báo cáo: chưa thống nhất (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** Lỗi pipeline: Dòng 1: cần định dạng Người nói: nội dung.
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Dữ liệu không có nhãn người nói vẫn đủ để nhận ra chưa có kết luận; cần báo lỗi parser như một thất bại hỗ trợ input.

Sai lệch: Pipeline không xử lý được input: Dòng 1: cần định dạng Người nói: nội dung.; Thiếu/sai unresolved: xuất báo cáo / chưa thống nhất

### 16_clear_decision — Chốt lịch phát hành sau khi xác nhận đủ điều kiện

- **Kỳ vọng:** decision/phát hành: bản 2.1 (confirmed, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** decision/phát hành: chốt đưa bản 2.1 lên vào thứ Hai. (confirmed, owner=None, due=None)
- **Đạt/Chưa đạt:** Đạt
- **Điều học được:** Tình huống tường minh vẫn cần có trong suite để kiểm tra kết luận còn hiệu lực khi cuộc họp kết thúc.

### 17_clear_assignment — Quyết định và công việc thiếu một trường được tách riêng

- **Kỳ vọng:** decision/báo cáo: biểu đồ đường (confirmed, owner=None, due=None, conditions=[]); request_feedback/nhãn biểu đồ: chữ quá nhỏ (needs_confirmation, owner=None, due=None, conditions=[]); action/tài liệu: cập nhật tài liệu (confirmed, owner=Lan, due=None, conditions=[]); action/bảo mật: rà soát quyền truy cập (needs_confirmation, owner=None, due=thứ Hai, conditions=[]); issue/đăng nhập: chưa có quyền sandbox (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/phân quyền: cách cấp quyền (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** decision/báo cáo: Chốt dùng biểu đồ đường trên màn hình báo cáo. (confirmed, owner=None, due=None); request_feedback/nhãn biểu đồ: phản hồi của khách là chữ quá nhỏ khi xem trên điện thoại. (needs_confirmation, owner=None, due=None); action/tài liệu: Em nhận cập nhật tài liệu sử dụng. (confirmed, owner=Lan, due=None); action/tài liệu: Đúng, hôm nay em nhận việc nhưng chưa cam kết thời hạn cụ thể. (confirmed, owner=Lan, due=cụ thể); action/bảo mật: Cần làm rà soát quyền truy cập trước thứ Hai. (needs_confirmation, owner=None, due=thứ Hai); issue/đăng nhập: Vướng mắc là chưa có quyền sandbox để thử luồng đăng nhập của khách. (needs_confirmation, owner=None, due=None); unresolved/phân quyền: Chưa thống nhất cách cấp quyền cho khách, giữ câu hỏi đó cho buổi trao đổi tiếp. (unresolved, owner=None, due=None)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Thiếu hạn và thiếu người là hai trường hợp khác nhau; giữ null thay vì chuyển thông tin từ việc bên cạnh.

Sai lệch: Mục ngoài kỳ vọng: action / tài liệu / Đúng, hôm nay em nhận việc nhưng chưa cam kết thời hạn cụ thể.

### 18_anonymous_assignment — Cam kết đã rõ, danh tính người nhận chưa rõ

- **Kỳ vọng:** action/kiểm thử: kiểm thử hồi quy (needs_confirmation, owner=None, due=thứ Sáu, conditions=[])
- **Kết quả thực tế:** action/kiểm thử: Em nhận làm kiểm thử hồi quy trước thứ Sáu. (confirmed, owner=Người nói 2, due=thứ Sáu)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Không đồng nhất nhãn diarization với tên thật; có thể giữ evidence nhưng owner cần để null.

Sai lệch: kiểm thử: status kỳ vọng 'needs_confirmation', thực tế 'confirmed'; kiểm thử: owner kỳ vọng None, thực tế 'Người nói 2'

## Tập kín

Đạt **0/8**; decision precision **0.0**, recall **0.0**. TP/FP/FN: 0/1/3. Trung gian nâng sai: 0/6; owner/due ngoài kỳ vọng: 0.

Run UTC: 2026-10-14T07:25:00.280682+00:00; dataset 2.0; prompt 1.0.

| Nhóm | Đạt / tổng |
| --- | --- |
| Đổi phương án | 0/2 |
| Chốt / giao việc rõ | 0/2 |
| Chốt gián tiếp / cam kết | 0/2 |
| Chưa thống nhất | 0/2 |

| Dữ liệu người nói | Đạt / tổng |
| --- | --- |
| Trộn có/không nhãn | 0/1 |
| Có tên | 0/4 |
| Không có người nói | 0/3 |

### 04_interleaved — Quay lại chuyện lưu trữ sau khi bàn lịch demo

- **Kỳ vọng:** decision/lưu trữ: phương án B (confirmed, owner=None, due=None, conditions=[]); unresolved/lịch demo: chiều thứ Tư (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** decision/lịch demo: Chốt dùng phương án B cho phần đó. (confirmed, owner=None, due=None)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Đại từ và tham chiếu quay lại chủ đề có thể làm local gắn câu chốt đúng chữ vào sai chủ đề.

Sai lệch: Thiếu/sai decision: lưu trữ / phương án B; Thiếu/sai unresolved: lịch demo / chiều thứ Tư; Mục ngoài kỳ vọng: decision / lịch demo / Chốt dùng phương án B cho phần đó.

### 05_unnamed_reversal — Đổi cổng thanh toán trong transcript không có người nói

- **Kỳ vọng:** decision/thanh toán: cổng B (confirmed, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** Lỗi pipeline: Dòng 1: cần định dạng Người nói: nội dung.
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Transcript vẫn có kết luận rõ dù thiếu người nói; parser hiện tại phải được đánh giá là chưa hỗ trợ, không biến lỗi input thành kết quả trống đạt.

Sai lệch: Pipeline không xử lý được input: Dòng 1: cần định dạng Người nói: nội dung.; Thiếu/sai decision: thanh toán / cổng B

### 09_named_assignee_no_speaker — Người nhận được nêu trong nội dung, không biết ai nói

- **Kỳ vọng:** action/báo cáo: gửi báo cáo (confirmed, owner=Lan, due=thứ Sáu, conditions=[])
- **Kết quả thực tế:** Lỗi pipeline: Dòng 1: cần định dạng Người nói: nội dung.
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Không cần biết người phát biểu để nhận ra tên người được giao việc được nói rõ trong nội dung.

Sai lệch: Pipeline không xử lý được input: Dòng 1: cần định dạng Người nói: nội dung.; Thiếu/sai action: báo cáo / gửi báo cáo

### 10_indirect_consensus — Thống nhất qua nhiều lượt mà không nói từ chốt

- **Kỳ vọng:** decision/báo cáo: một cột (confirmed, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** Không có mục
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Đồng thuận có thể được thể hiện bằng nhiều lượt và lời kết luận gián tiếp, không chỉ từ khóa chốt.

Sai lệch: Thiếu/sai decision: báo cáo / một cột

### 14_request_not_assignment — Yêu cầu của khách không tự thành việc đã giao

- **Kỳ vọng:** request_feedback/báo cáo: bộ lọc theo tháng (needs_confirmation, owner=None, due=None, conditions=[]); unresolved/báo cáo: chưa thống nhất (unresolved, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** Lỗi pipeline: Dòng 2: cần định dạng Người nói: nội dung.
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Dữ liệu có và thiếu nhãn xen kẽ phải được đưa vào test; yêu cầu không tự tạo owner hoặc deadline.

Sai lệch: Pipeline không xử lý được input: Dòng 2: cần định dạng Người nói: nội dung.; Thiếu/sai request_feedback: báo cáo / bộ lọc theo tháng; Thiếu/sai unresolved: báo cáo / chưa thống nhất

### 15_conditional_task — Lời nhận việc còn phụ thuộc quyền truy cập

- **Kỳ vọng:** action/hoàn tiền: kiểm tra luồng hoàn tiền (needs_confirmation, owner=Lan, due=None, conditions=['Nếu đối tác mở quyền sandbox']); issue/sandbox: chưa mở quyền sandbox (needs_confirmation, owner=None, due=None, conditions=[])
- **Kết quả thực tế:** issue/chưa xác định chủ đề: Vướng mắc là đối tác chưa mở quyền sandbox cho nhóm. (needs_confirmation, owner=None, due=None)
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Lời nhận việc có điều kiện không được nâng thành cam kết vô điều kiện hoặc tự thêm hạn từ lịch demo.

Sai lệch: Thiếu/sai action: hoàn tiền / kiểm tra luồng hoàn tiền; Thiếu/sai issue: sandbox / chưa mở quyền sandbox; Mục ngoài kỳ vọng: issue / chưa xác định chủ đề / Vướng mắc là đối tác chưa mở quyền sandbox cho nhóm.

### 19_speakerless_commitment — Có việc và hạn, không có dữ liệu xác định người nhận

- **Kỳ vọng:** action/hướng dẫn: thay ảnh hướng dẫn (needs_confirmation, owner=None, due=ngày mai, conditions=[])
- **Kết quả thực tế:** Lỗi pipeline: Dòng 1: cần định dạng Người nói: nội dung.
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Một lời tự nhận rõ không cho phép bịa danh tính khi transcript không có người nói.

Sai lệch: Pipeline không xử lý được input: Dòng 1: cần định dạng Người nói: nội dung.; Thiếu/sai action: hướng dẫn / thay ảnh hướng dẫn

### 20_explicit_name_in_content — Người nói Huy giao việc cho Mai

- **Kỳ vọng:** action/báo cáo: gửi báo cáo (confirmed, owner=Mai, due=thứ Sáu, conditions=[])
- **Kết quả thực tế:** Không có mục
- **Đạt/Chưa đạt:** Chưa đạt
- **Điều học được:** Tên người nhận ở trong nội dung có thể khác người nói; không dùng vị trí đầu dòng để suy ra owner.

Sai lệch: Thiếu/sai action: báo cáo / gửi báo cáo
