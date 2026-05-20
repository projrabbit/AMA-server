# DFD Level 1 - Thực Hiện Check-in

Thuật toán: Để ghi nhận chấm công vào ca làm việc, nhân viên cần thực hiện check-in qua Mobile App với xác minh vị trí GPS và gương mặt.

Bước 1: Nhân viên nhấn nút Check-in trên ứng dụng. Ứng dụng thu thập tọa độ GPS, ảnh selfie và thông tin thiết bị, sau đó gửi yêu cầu check-in.

Bước 2: Hệ thống tiếp nhận yêu cầu, tra cứu thông tin nhân viên, ca làm việc đang áp dụng và trạng thái thiết bị.

Bước 3: Hệ thống kiểm tra hợp lệ bao gồm phát hiện giả mạo GPS, xác minh gương mặt và đối chiếu vùng geofence. Kết quả kiểm tra được lưu vào kho dữ liệu phát hiện gian lận.

Bước 4: Nếu phát hiện gian lận hoặc vị trí ngoài vùng geofence, hệ thống tạo bản ghi chấm công bị từ chối với lý do tương ứng và ghi Audit Log.

Bước 5: Nếu hợp lệ, hệ thống tạo bản ghi chấm công được duyệt, tính trạng thái đi trễ và ghi Audit Log.

Bước 6: Hệ thống trả kết quả check-in thành công hoặc lý do từ chối cho nhân viên.

Bước 7: Kết thúc.
