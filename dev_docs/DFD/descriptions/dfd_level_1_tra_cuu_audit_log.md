# DFD Level 1 - Tra Cứu Audit Log

Thuật toán: Để kiểm tra nhật ký thao tác trong hệ thống, Admin tra cứu Audit Log theo các điều kiện lọc.

Bước 1: Admin mở mục Audit Log và nhập điều kiện lọc gồm tài khoản thực hiện, loại hành động, khoảng thời gian và thực thể bị tác động.

Bước 2: Hệ thống truy vấn kho dữ liệu Audit Log theo điều kiện lọc, sắp xếp mới nhất trước.

Bước 3: Nếu không có kết quả, hệ thống hiển thị thông báo không tìm thấy log phù hợp.

Bước 4: Nếu có kết quả, hệ thống hiển thị bảng log gồm tài khoản, loại hành động, thực thể, địa chỉ IP và thời điểm tạo.

Bước 5: Admin có thể chọn một log để xem payload JSON đầy đủ ở chế độ chỉ đọc.

Bước 6: Kết thúc.
