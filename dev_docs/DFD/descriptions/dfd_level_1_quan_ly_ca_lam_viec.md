# DFD Level 1 - Quản Lý Ca Làm Việc

Thuật toán: Để cấu hình thời gian làm việc cho nhân viên, HR/Admin cần tạo, chỉnh sửa và gán ca làm việc.

Bước 1: HR/Admin nhập thông tin ca mới gồm tên ca, giờ bắt đầu, giờ kết thúc và ngưỡng cho phép trễ hoặc về sớm, sau đó gửi yêu cầu.

Bước 2: Hệ thống kiểm tra xung đột thời gian với các ca đang hoạt động trong kho dữ liệu ca làm việc.

Bước 3: Nếu có xung đột, hệ thống trả cảnh báo để HR/Admin điều chỉnh lại.

Bước 4: Nếu hợp lệ, hệ thống lưu ca làm việc và ghi Audit Log.

Bước 5: HR/Admin chọn nhân viên và gán ca. Hệ thống cập nhật thông tin gán ca vào kho dữ liệu nhân viên và ghi Audit Log.

Bước 6: Hệ thống trả kết quả xử lý ca cho HR/Admin.

Bước 7: Kết thúc.
