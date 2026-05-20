# DFD Level 1 - Phát Hiện Chấm Công Hộ

Thuật toán: Để phát hiện khả năng chấm công thay người khác, hệ thống tự động kiểm tra lịch sử sử dụng thiết bị và tốc độ di chuyển khi có yêu cầu chấm công.

Bước 1: Hệ thống nhận thông tin thiết bị, mã nhân viên, tọa độ và thời điểm từ yêu cầu chấm công.

Bước 2: Hệ thống truy vấn lịch sử sử dụng thiết bị để kiểm tra xem thiết bị có được dùng cho nhân viên khác trong khoảng thời gian ngắn hay không.

Bước 3: Hệ thống tra cứu vị trí chấm công gần nhất của nhân viên và tính tốc độ di chuyển giữa hai lần chấm công liên tiếp.

Bước 4: Nếu thiết bị dùng chung cho nhiều nhân viên hoặc tốc độ di chuyển vượt ngưỡng thực tế, hệ thống đánh dấu nghi ngờ chấm công hộ với lý do tương ứng.

Bước 5: Hệ thống cập nhật kết quả vào kho dữ liệu phát hiện gian lận, ghi cảnh báo vào Audit Log và trả kết quả về để HR xem xét tại mục quản lý ngoại lệ.

Bước 6: Kết thúc.
