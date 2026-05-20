# DFD Level 1 - Quản Lý Ngoại Lệ Chấm Công

Thuật toán: Để xử lý các bản ghi chấm công bất thường, HR/Admin xem danh sách ngoại lệ và quyết định phê duyệt thủ công nếu phù hợp.

Bước 1: HR/Admin mở mục Ngoại lệ. Hệ thống truy vấn các bản ghi chấm công có trạng thái bị từ chối, đi trễ hoặc về sớm.

Bước 2: Hệ thống hiển thị danh sách ngoại lệ cho HR/Admin xem xét.

Bước 3: HR/Admin chọn một bản ghi để xem chi tiết. Hệ thống lấy thêm thông tin từ kho dữ liệu phát hiện gian lận gồm lý do từ chối, tọa độ và các cờ gian lận.

Bước 4: Nếu HR/Admin phê duyệt thủ công, hệ thống cập nhật trạng thái bản ghi thành được duyệt và ghi Audit Log.

Bước 5: Nếu HR/Admin chọn giữ nguyên từ chối, hệ thống không thay đổi trạng thái bản ghi.

Bước 6: Hệ thống trả kết quả xử lý cho HR/Admin.

Bước 7: Kết thúc.
