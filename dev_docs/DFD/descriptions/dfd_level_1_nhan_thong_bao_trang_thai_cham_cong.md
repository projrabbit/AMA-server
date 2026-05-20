# DFD Level 1 - Nhận Thông Báo Trạng Thái Chấm Công

Thuật toán: Để nhận biết kết quả sau khi thực hiện chấm công, nhân viên nhận thông báo phản hồi tức thời từ hệ thống.

Bước 1: Nhân viên gửi yêu cầu check-in hoặc check-out lên hệ thống.

Bước 2: Hệ thống xử lý nghiệp vụ chấm công và lưu bản ghi vào kho dữ liệu bản ghi chấm công.

Bước 3: Hệ thống lấy trạng thái bản ghi vừa tạo để xác định loại thông báo cần gửi.

Bước 4: Nếu chấm công được duyệt, hệ thống gửi thông báo thành công kèm vị trí hoặc tầng làm việc.

Bước 5: Nếu bị từ chối do ngoài geofence hoặc phát hiện gian lận, hệ thống gửi thông báo với lý do từ chối tương ứng. Nếu lỗi kết nối, ứng dụng hiển thị thông báo lỗi và cho phép thử lại.

Bước 6: Kết thúc.
