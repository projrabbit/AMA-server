# DFD Level 1 - Quản Lý Geofence 3D

Thuật toán: Để thiết lập vùng chấm công hợp lệ, HR/Admin cần tạo hoặc chỉnh sửa geofence 3D trên bản đồ theo tòa nhà và tầng.

Bước 1: Hệ thống tải danh sách tòa nhà và tầng từ kho dữ liệu, sau đó khởi tạo bản đồ 3D từ ArcGIS Platform và hiển thị cho HR/Admin.

Bước 2: HR/Admin chọn tòa nhà, tầng và nhập thông tin vùng geofence mới, hoặc chọn vùng hiện có để xóa hoặc vô hiệu hóa.

Bước 3: Hệ thống kiểm tra xem vùng geofence mới có bị trùng lặp với các vùng đang hoạt động hay không.

Bước 4: Nếu bị trùng lặp, hệ thống trả cảnh báo xung đột để HR/Admin điều chỉnh lại.

Bước 5: Nếu hợp lệ, hệ thống lưu hoặc cập nhật geofence vào kho dữ liệu và ghi Audit Log.

Bước 6: Hệ thống trả kết quả xử lý và cập nhật bản đồ 3D.

Bước 7: Kết thúc.
