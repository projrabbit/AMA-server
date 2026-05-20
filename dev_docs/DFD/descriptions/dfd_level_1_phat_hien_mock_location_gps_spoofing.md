# DFD Level 1 - Phát Hiện Mock Location / GPS Spoofing

Thuật toán: Để đảm bảo tính xác thực của dữ liệu chấm công, hệ thống tự động kiểm tra GPS, thiết bị và gương mặt khi có yêu cầu check-in hoặc check-out.

Bước 1: Hệ thống nhận dữ liệu GPS, tín hiệu thiết bị, ảnh gương mặt và liveness từ yêu cầu chấm công.

Bước 2: Hệ thống kiểm tra cờ mock location từ thiết bị, tra cứu lịch sử vị trí gần đây để phát hiện tốc độ di chuyển bất thường và kiểm tra trạng thái tin cậy của thiết bị.

Bước 3: Hệ thống lấy khuôn mặt mẫu của nhân viên từ kho dữ liệu và xác minh khớp gương mặt cùng kiểm tra liveness.

Bước 4: Nếu phát hiện GPS giả, thiết bị lạ hoặc gương mặt không khớp, hệ thống ghi nhận các cờ tương ứng và giảm điểm tin cậy.

Bước 5: Hệ thống tính điểm tin cậy tổng hợp, lưu kết quả kiểm tra vào kho dữ liệu phát hiện gian lận và trả kết quả về cho luồng xử lý chấm công.

Bước 6: Kết thúc.
