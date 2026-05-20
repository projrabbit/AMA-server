# DFD Level 1 - Xem Và Xuất Báo Cáo Chấm Công

Thuật toán: Để theo dõi tình hình chấm công, HR/Admin/CEO xem báo cáo tổng hợp và xuất file nếu cần.

Bước 1: Người dùng chọn điều kiện lọc gồm khoảng thời gian, phòng ban hoặc nhân viên cụ thể, sau đó gửi yêu cầu xem báo cáo.

Bước 2: Hệ thống truy vấn kho dữ liệu bản ghi chấm công kết hợp thông tin nhân viên theo điều kiện lọc.

Bước 3: Nếu không có dữ liệu, hệ thống thông báo không có kết quả phù hợp.

Bước 4: Nếu có dữ liệu, hệ thống tổng hợp số ngày công, tổng giờ làm, số lần trễ, về sớm, vắng mặt và bản ghi bị từ chối, sau đó hiển thị bảng báo cáo.

Bước 5: Nếu người dùng yêu cầu xuất file, hệ thống truy vấn lại dữ liệu theo cùng bộ lọc, tạo file Excel hoặc PDF và trả file để tải về.

Bước 6: Kết thúc.
