# DFD Level 1 - Đăng Nhập Hệ Thống

Thuật toán: Để truy cập hệ thống, người dùng cần thực hiện đăng nhập bằng tài khoản đã được cấp.

Bước 1: Người dùng nhập tên đăng nhập và mật khẩu, sau đó gửi yêu cầu đăng nhập.

Bước 2: Hệ thống tiếp nhận thông tin và truy vấn kho dữ liệu tài khoản để kiểm tra sự tồn tại và trạng thái của tài khoản.

Bước 3: Nếu tài khoản không tồn tại, bị khóa hoặc mật khẩu sai, hệ thống trả thông báo lỗi và yêu cầu người dùng nhập lại.

Bước 4: Nếu thông tin hợp lệ, hệ thống ghi nhật ký đăng nhập vào Audit Log.

Bước 5: Hệ thống cấp JWT token kèm vai trò và điều hướng người dùng đến màn hình chính tương ứng với quyền của tài khoản.

Bước 6: Kết thúc.
