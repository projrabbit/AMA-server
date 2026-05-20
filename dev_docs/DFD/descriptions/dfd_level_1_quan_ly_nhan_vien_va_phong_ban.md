# DFD Level 1 - Quản Lý Nhân Viên Và Phòng Ban

Thuật toán: Để quản lý nhân sự trong hệ thống, HR/Admin tạo, cập nhật hoặc vô hiệu hóa nhân viên và phòng ban.

Bước 1: HR/Admin nhập thông tin nhân viên mới gồm họ tên, phòng ban, chức vụ, email và ngày vào làm, sau đó gửi yêu cầu.

Bước 2: Hệ thống kiểm tra email có bị trùng trong kho dữ liệu nhân viên hay không.

Bước 3: Nếu email trùng, hệ thống trả lỗi và yêu cầu nhập email khác.

Bước 4: Nếu hợp lệ, hệ thống tạo hồ sơ nhân viên, tạo tài khoản liên kết, cập nhật thông tin phòng ban nếu cần và ghi Audit Log.

Bước 5: Nếu vô hiệu hóa nhân viên, hệ thống chuyển trạng thái nhân viên sang inactive, khóa tài khoản tương ứng và ghi Audit Log.

Bước 6: Hệ thống trả kết quả xử lý cho HR/Admin.

Bước 7: Kết thúc.
