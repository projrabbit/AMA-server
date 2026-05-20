# DFD Level 1 - Quản Lý Tòa Nhà Và Tầng

Thuật toán: Để cấu hình cơ sở hạ tầng cho geofence 3D, Admin tạo thông tin tòa nhà và tầng với tích hợp ArcGIS.

Bước 1: Admin nhập thông tin tòa nhà mới gồm tên, địa chỉ, tọa độ trung tâm, số tầng và Layer ID của ArcGIS, sau đó gửi yêu cầu.

Bước 2: Hệ thống xác thực Layer ID với ArcGIS Platform để đảm bảo layer tòa nhà tồn tại và hợp lệ.

Bước 3: Nếu Layer ID không hợp lệ, hệ thống trả lỗi tích hợp ArcGIS và yêu cầu Admin kiểm tra lại.

Bước 4: Nếu hợp lệ, hệ thống lưu thông tin tòa nhà vào kho dữ liệu tòa nhà và tầng, ghi Audit Log và hiển thị tòa nhà trên bản đồ 3D.

Bước 5: Admin tiếp tục thêm tầng cho tòa nhà bằng cách nhập số tầng, tên tầng và khoảng độ cao. Hệ thống lưu thông tin tầng và ghi Audit Log.

Bước 6: Hệ thống trả kết quả xử lý và danh sách tòa nhà/tầng đã cập nhật cho Admin.

Bước 7: Kết thúc.
