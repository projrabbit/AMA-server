# DFD Level 1 - Quản Lý Thiết Bị Tin Cậy

Thuật toán: Để kiểm soát thiết bị được phép chấm công, Admin xem danh sách thiết bị đã đăng ký và cập nhật trạng thái tin cậy.

Bước 1: Admin mở mục Quản lý Thiết bị. Hệ thống truy vấn danh sách thiết bị kết hợp thông tin nhân viên từ kho dữ liệu.

Bước 2: Hệ thống hiển thị danh sách thiết bị gồm nhân viên sở hữu, nền tảng, model, thời điểm đăng ký và trạng thái tin cậy.

Bước 3: Admin chọn thiết bị và yêu cầu đánh dấu tin cậy hoặc thu hồi tin cậy.

Bước 4: Nếu đánh dấu tin cậy, hệ thống cập nhật trạng thái tin cậy thành true trong kho dữ liệu thiết bị và ghi Audit Log.

Bước 5: Nếu thu hồi tin cậy, hệ thống cập nhật trạng thái tin cậy thành false và ghi Audit Log. Từ lần chấm công tiếp theo, thiết bị này sẽ kích hoạt cờ thiết bị lạ trong kiểm tra gian lận.

Bước 6: Hệ thống trả kết quả cập nhật cho Admin.

Bước 7: Kết thúc.
