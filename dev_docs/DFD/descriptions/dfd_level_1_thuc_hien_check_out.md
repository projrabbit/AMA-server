# DFD Level 1 - Thực Hiện Check-out

Thuật toán: Để ghi nhận chấm công ra khi kết thúc ca làm việc, nhân viên cần thực hiện check-out qua Mobile App với xác minh vị trí GPS và gương mặt.

Bước 1: Nhân viên nhấn nút Check-out trên ứng dụng. Ứng dụng thu thập tọa độ GPS, ảnh selfie và thông tin thiết bị, sau đó gửi yêu cầu check-out.

Bước 2: Hệ thống tìm bản ghi check-in gần nhất của nhân viên trong ngày và tra cứu ca làm việc tương ứng.

Bước 3: Nếu chưa có bản ghi check-in hợp lệ, hệ thống trả lỗi và không xử lý tiếp.

Bước 4: Hệ thống kiểm tra hợp lệ bao gồm phát hiện giả mạo GPS, xác minh gương mặt và đối chiếu vùng geofence. Kết quả kiểm tra được lưu vào kho dữ liệu phát hiện gian lận.

Bước 5: Nếu phát hiện gian lận hoặc vị trí ngoài vùng geofence, hệ thống tạo bản ghi check-out bị từ chối và ghi Audit Log.

Bước 6: Nếu hợp lệ, hệ thống tạo bản ghi check-out được duyệt, đánh dấu về sớm nếu checkout trước giờ kết thúc ca, và ghi Audit Log.

Bước 7: Hệ thống trả kết quả check-out cho nhân viên.

Bước 8: Kết thúc.
