# Phát triển và tái lập kết quả

Cần Python 3.10+. Source chạy không cần pip hoặc SDK bên thứ ba:

```bash
python src
python src --port 8502
python src extract data/examples/01_change_ab.txt --output runtime/demo.json
python src test
python src evaluate --split dev --verify-only
python src evaluate --split holdout --verify-only
python src package --verify
```

Các lệnh chạy tại root. Có thể dùng đường dẫn tuyệt đối tới thư mục `src` khi đang ở thư mục khác. Launcher Windows gọi cùng entry point. File input/output tương đối của CLI được hiểu theo cwd.

`tests/unit` kiểm tra parser, validator, API mock và scorer; `integration` kiểm tra HTTP/entry points; `regression` so hash và tái lập output suite v2, kể cả lỗi input. Test kỹ thuật xanh không có nghĩa benchmark ngữ nghĩa đều đạt.

20 fixture gồm transcript ở `data/examples`, kỳ vọng/manifest ở `tests/fixtures`; `conditions` là các chuỗi điều kiện phải giữ trong nội dung output. Có bốn nhóm × năm case và 12 phát triển / 8 kín. Những case thiếu người nói là input muốn hỗ trợ, không phải test mong đợi parser từ chối; hiện chúng được ghi chưa đạt.

`--verify-only` đối chiếu output và điểm số, không đổi timestamp/báo cáo. Bỏ cờ khi muốn lưu lượt chạy mới. Lỗi config/provider không được giả thành số liệu LLM. Fixtures được viết trước khi chạy; không sửa kỳ vọng để làm xanh test ngữ nghĩa. Muốn đổi thuật toán cần version/freeze mới và đánh giá mới, giữ lịch sử riêng.

Source ZIP dùng danh sách root/source/data/test và tài liệu cần cho showcase. Không gom toàn workspace: bỏ môi trường, Git metadata, cache, ZIP khác, runtime export, tài liệu Word và ghi chú cá nhân. `python src package --verify` giải nén ZIP vào thư mục sạch rồi chạy test và hai baseline checks.

`pyproject.toml` cũng khai báo package/CLI entry points. `python -m pip install -e .` là tùy chọn, có thể cần setuptools từ registry; chưa kiểm chứng cài wheel trong môi trường hiện tại. Khi cài ngoài checkout, dùng `MEETING_TRACE_PROJECT_ROOT` để trỏ tới project data.

CI Windows/Linux, Python 3.10/3.12 chạy các lệnh trên. Đây là cấu hình; kiểm tra trạng thái Actions thực tế trước khi nhận remote CI đã qua.
