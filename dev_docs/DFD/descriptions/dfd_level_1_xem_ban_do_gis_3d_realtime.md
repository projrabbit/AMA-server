# DFD Level 1 - Xem Bản Đồ GIS 3D Real-time

Thuật toán: Để theo dõi vị trí nhân viên đang làm việc, HR/Admin xem bản đồ GIS 3D với marker cập nhật theo thời gian gần thực.

Bước 1: HR/Admin mở tab Bản đồ 3D và thiết lập bộ lọc nếu cần theo tòa nhà, tầng hoặc phòng ban.

Bước 2: Hệ thống truy vấn danh sách nhân viên đang check-in và chưa check-out trong ngày, lấy tọa độ và tầng làm việc của từng người.

Bước 3: Hệ thống lấy Layer ID tòa nhà từ kho dữ liệu để load layer tương ứng trên ArcGIS Platform.

Bước 4: Hệ thống gửi dữ liệu marker và Layer ID đến ArcGIS Platform để hiển thị bản đồ 3D với vị trí từng nhân viên.

Bước 5: Hệ thống trả bản đồ 3D real-time cho HR/Admin. Sau mỗi 30 giây, hệ thống tự động làm mới dữ liệu vị trí.

Bước 6: Kết thúc.
