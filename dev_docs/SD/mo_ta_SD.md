# Mô Tả Sequence Diagram - Hệ Thống Chấm Công Thông Minh

Tài liệu này mô tả các Sequence Diagram trong thư mục `SD/`. Nội dung diễn giải theo từng use case, tập trung vào thứ tự tương tác giữa tác nhân, giao diện, API Server, các service liên quan và database.

## Danh Sách Sequence Diagram

| STT | File sơ đồ | Nội dung |
| --- | --- | --- |
| 1 | `SD/UC01_Login.puml` | UC-01 Đăng nhập hệ thống |
| 2 | `SD/UC02_CheckIn.puml` | UC-02 Thực hiện Check-in |
| 3 | `SD/UC03_CheckOut.puml` | UC-03 Thực hiện Check-out |
| 4 | `SD/UC04_ViewHistory.puml` | UC-04 Xem lịch sử chấm công cá nhân |
| 5 | `SD/UC05_Notification.puml` | UC-05 Nhận thông báo trạng thái chấm công |
| 6 | `SD/UC06_ManageGeofence.puml` | UC-06 Quản lý Geofence 3D |
| 7 | `SD/UC07_View3DMap.puml` | UC-07 Xem bản đồ GIS 3D real-time |
| 8 | `SD/UC08_ManageShift.puml` | UC-08 Quản lý ca làm việc |
| 9 | `SD/UC09_Report.puml` | UC-09 Xem và xuất báo cáo chấm công |
| 10 | `SD/UC10_ManageException.puml` | UC-10 Quản lý ngoại lệ chấm công |
| 11 | `SD/UC11_FraudDetection.puml` | UC-11 Phát hiện gian lận |
| 12 | `SD/UC12_BuddyPunch.puml` | UC-12 Phát hiện chấm công hộ |
| 13 | `SD/UC13_ManageDevice.puml` | UC-13 Quản lý thiết bị tin cậy |
| 14 | `SD/UC14_AuditLog.puml` | UC-14 Tra cứu Audit Log |
| 15 | `SD/UC15_ManageEmployee.puml` | UC-15 Quản lý nhân viên và phòng ban |
| 16 | `SD/UC16_Dashboard.puml` | UC-16 Xem Dashboard tổng quan |
| 17 | `SD/UC17_ManageBuilding.puml` | UC-17 Quản lý tòa nhà và tầng |

## 1. UC-01 - Đăng Nhập Hệ Thống

File sơ đồ: `SD/UC01_Login.puml`

Người dùng đăng nhập vào hệ thống bằng tài khoản đã được cấp:

- Người dùng nhập username và password trên Mobile App hoặc Web Dashboard.
- Client gửi request `POST /auth/login` đến API Server.
- API Server truy vấn Database để tìm Account theo username và chỉ lấy tài khoản còn hoạt động.
- Database trả về thông tin account gồm password_hash và role nếu tìm thấy.
- Nếu tài khoản không tồn tại hoặc bị khóa, API Server trả lỗi 401 và client hiển thị thông báo lỗi.
- Nếu mật khẩu sai, API Server trả lỗi 401 và cho phép người dùng nhập lại.
- Nếu đăng nhập thành công, API Server cập nhật `last_login_at`, ghi AuditLog hành động LOGIN và trả JWT token kèm role.
- Client nhận token và điều hướng người dùng đến màn hình chính phù hợp với vai trò.

## 2. UC-02 - Thực Hiện Check-in

File sơ đồ: `SD/UC02_CheckIn.puml`

Nhân viên thực hiện check-in bằng Mobile App:

- Nhân viên nhấn nút Check-in trên ứng dụng.
- Mobile App thu tọa độ GPS gồm latitude, longitude, altitude và gps_accuracy.
- Ứng dụng chụp selfie và thu tín hiệu liveness để phục vụ kiểm tra gương mặt.
- Mobile App gửi request `POST /attendance/check-in` đến API Server, kèm employee_id, device_fingerprint, GPS, face_image và liveness_signals.
- API Server truy vấn Database để lấy Employee, Device và Shift tương ứng.
- API Server gọi Fraud Detection để kiểm tra mock location, GPS spoofing, thiết bị, gương mặt và liveness.
- Fraud Detection trả về FraudResult gồm confidence_score và các flags.
- API Server truy vấn danh sách geofence hoặc GeofenceRule đang hoạt động phù hợp với altitude.
- API Server kiểm tra gps_accuracy, điều kiện geofence và fraud_score.
- Nếu GPS accuracy kém, hệ thống ghi AuditLog `CHECK_IN_FAILED_GPS` và trả kết quả failed_gps_accuracy.
- Nếu phát hiện gian lận, hệ thống tạo AttendanceRecord rejected với lý do `fraud_detected`, ghi AuditLog và trả kết quả rejected.
- Nếu ngoài geofence, hệ thống tạo AttendanceRecord rejected với lý do `outside_geofence`, ghi AuditLog và trả kết quả rejected.
- Nếu hợp lệ, hệ thống tính `is_late`, tạo AttendanceRecord approved, ghi AuditLog `CHECK_IN_APPROVED` và trả kết quả approved.
- Mobile App hiển thị thông báo trạng thái cho nhân viên, chi tiết phần thông báo được mô tả ở UC-05.

## 3. UC-03 - Thực Hiện Check-out

File sơ đồ: `SD/UC03_CheckOut.puml`

Nhân viên thực hiện check-out khi kết thúc ca làm việc:

- Nhân viên nhấn nút Check-out trên Mobile App.
- Ứng dụng thu GPS 3D, gps_accuracy, ảnh selfie và tín hiệu liveness.
- Mobile App gửi request `POST /attendance/check-out` đến API Server.
- API Server truy vấn AttendanceRecord cuối cùng của nhân viên trong ngày với type check_in.
- Nếu chưa có bản ghi check-in trong ngày, API Server trả kết quả `failed_no_checkin`.
- Nếu đã có check-in, API Server gọi Fraud Detection để kiểm tra gian lận.
- Fraud Detection trả về confidence_score và flags.
- API Server truy vấn geofence hoặc GeofenceRule và Shift tương ứng.
- API Server kiểm tra điều kiện geofence, fraud_score và tính `is_early_leave` dựa trên shift.end_time.
- Nếu phát hiện gian lận, hệ thống tạo AttendanceRecord check_out rejected, ghi AuditLog và trả kết quả rejected.
- Nếu ngoài geofence, hệ thống tạo AttendanceRecord check_out rejected với lý do `outside_geofence`.
- Nếu check-out trước giờ kết thúc ca nhưng vị trí hợp lệ, hệ thống tạo AttendanceRecord approved và đánh dấu `is_early_leave=TRUE`.
- Nếu hợp lệ, hệ thống tạo AttendanceRecord approved với `is_early_leave=FALSE`.
- Mobile App hiển thị trạng thái check-out cho nhân viên.

## 4. UC-04 - Xem Lịch Sử Chấm Công Cá Nhân

File sơ đồ: `SD/UC04_ViewHistory.puml`

Nhân viên xem lại lịch sử chấm công của bản thân:

- Nhân viên chọn tab Lịch sử chấm công trên Mobile App.
- Nhân viên chọn khoảng thời gian cần xem theo ngày, tuần hoặc tháng.
- Mobile App gửi request `GET /attendance/history` kèm employee_id, from và to.
- API Server truy vấn AttendanceRecord theo employee_id và khoảng thời gian, sắp xếp mới nhất trước.
- Nếu không có dữ liệu, API Server trả danh sách rỗng và ứng dụng hiển thị thông báo không có dữ liệu.
- Nếu có dữ liệu, API Server tính tổng giờ làm bằng cách ghép cặp check_in/check_out theo ngày.
- Mobile App hiển thị danh sách gồm ngày, giờ vào/ra, trạng thái, tầng làm việc và tổng giờ làm.

## 5. UC-05 - Nhận Thông Báo Trạng Thái Chấm Công

File sơ đồ: `SD/UC05_Notification.puml`

UC-05 mô tả phần phản hồi trực tiếp sau khi nhân viên thực hiện check-in hoặc check-out:

- Mobile App gửi request check-in hoặc check-out đến API Server.
- API Server xử lý nghiệp vụ theo UC-02 hoặc UC-03.
- Nếu chấm công thành công, API Server trả status approved, thông điệp thành công, vị trí/tầng, timestamp và thời gian phản hồi.
- Mobile App hiển thị thông báo chấm công thành công cho nhân viên.
- Nếu ngoài geofence, API Server trả status rejected với reason `outside_geofence`.
- Mobile App hiển thị thông báo ngoài vùng cho phép.
- Nếu phát hiện gian lận, API Server trả status rejected với reason tương ứng như mock_location hoặc fraud_detected.
- Mobile App hiển thị thông báo chấm công bị từ chối do vị trí hoặc tín hiệu không hợp lệ.
- Nếu request timeout hoặc lỗi mạng, Mobile App tự hiển thị thông báo lỗi kết nối và cho phép thử lại.
- Mục tiêu phản hồi của thông báo là dưới 5 giây trong điều kiện hệ thống hoạt động bình thường.

## 6. UC-06 - Quản Lý Geofence 3D

File sơ đồ: `SD/UC06_ManageGeofence.puml`

HR/Admin tạo hoặc vô hiệu hóa vùng geofence 3D:

- HR/Admin mở trang Quản lý Geofence trên Web Dashboard.
- Web Dashboard gọi API lấy danh sách Building và Floor.
- API Server truy vấn Database và trả danh sách tòa nhà, tầng.
- Web Dashboard khởi tạo ArcGIS Scene View và load layer tương ứng.
- HR/Admin chọn Building và Floor trên bản đồ 3D.
- HR/Admin nhập tọa độ trung tâm, bán kính, khoảng độ cao, tên geofence hoặc thông tin GeofenceRule.
- Web Dashboard gửi request tạo geofence đến API Server.
- API Server truy vấn các geofence đang hoạt động cùng floor_id để kiểm tra trùng lặp.
- Nếu geofence bị overlap, API Server trả 409 Conflict và Web Dashboard hiển thị cảnh báo.
- Nếu hợp lệ, API Server insert geofence, ghi AuditLog `GEOFENCE_CREATE` và trả mã geofence mới.
- Web Dashboard vẽ vùng geofence mới trên ArcGIS Scene View và thông báo thành công.
- Khi HR/Admin chọn xóa geofence, Web Dashboard gửi request DELETE đến API Server.
- API Server cập nhật `is_active=FALSE`, ghi AuditLog `GEOFENCE_DELETE` và trả 200 OK.
- Web Dashboard xóa marker hoặc vùng geofence khỏi bản đồ.

## 7. UC-07 - Xem Bản Đồ GIS 3D Real-time

File sơ đồ: `SD/UC07_View3DMap.puml`

HR/Admin xem vị trí nhân viên trên bản đồ 3D:

- HR/Admin mở tab Bản đồ 3D trên Web Dashboard.
- Web Dashboard khởi tạo ArcGIS SceneView và load arcgis_layer_id của các tòa nhà.
- ArcGIS Scene View báo trạng thái sẵn sàng.
- Web Dashboard gọi API `GET /realtime/employees-location` để lấy vị trí nhân viên đang làm việc.
- API Server truy vấn AttendanceRecord có type check_in, status approved, trong ngày hiện tại và chưa có check_out tương ứng.
- Database trả danh sách employee_id, latitude, longitude, altitude, floor và building.
- Web Dashboard gửi dữ liệu marker sang ArcGIS Scene View.
- ArcGIS hiển thị bản đồ 3D với marker của từng nhân viên.
- Khi HR/Admin lọc theo Building, Floor hoặc Department, Web Dashboard gửi lại request với điều kiện lọc.
- API Server trả danh sách nhân viên đã lọc và ArcGIS cập nhật marker trên bản đồ.
- Trong chế độ auto refresh, Web Dashboard gọi lại API mỗi 30 giây để cập nhật vị trí mới nhất.

## 8. UC-08 - Quản Lý Ca Làm Việc

File sơ đồ: `SD/UC08_ManageShift.puml`

HR/Admin quản lý thông tin ca làm việc:

- HR/Admin vào menu Quản lý Ca trên Web Dashboard.
- Web Dashboard gọi API lấy danh sách Shift hiện có.
- API Server truy vấn Database và trả danh sách ca làm việc.
- HR/Admin nhấn Tạo mới và nhập name, start_time, end_time, late_tolerance_min, early_leave_min và apply_to_weekends.
- Web Dashboard gửi request `POST /shifts` đến API Server.
- Nếu thời gian ca bị xung đột với ca khác, API Server trả 409 Conflict và giao diện hiển thị cảnh báo.
- Nếu hợp lệ, API Server insert Shift, ghi AuditLog `SHIFT_CREATE` và trả shift_id mới.
- HR/Admin chọn nhân viên để gán ca.
- Web Dashboard gửi request cập nhật ca cho nhân viên.
- API Server cập nhật ca mặc định hoặc bản ghi gán ca, ghi AuditLog `SHIFT_ASSIGN` và trả 200 OK.
- Khi chỉnh sửa ca, hệ thống cảnh báo ca đang được áp dụng có thể ảnh hưởng đến các lần check-in tiếp theo.
- Sau khi HR/Admin xác nhận, API Server update Shift và ghi AuditLog `SHIFT_UPDATE`.

## 9. UC-09 - Xem Và Xuất Báo Cáo Chấm Công

File sơ đồ: `SD/UC09_Report.puml`

HR/Admin/CEO xem báo cáo chấm công và xuất file:

- Người dùng vào mục Báo cáo trên Web Dashboard.
- Người dùng chọn bộ lọc gồm khoảng thời gian, phòng ban hoặc nhân viên.
- Web Dashboard gửi request `GET /reports/attendance` đến API Server.
- API Server truy vấn AttendanceRecord kết hợp Employee theo điều kiện lọc.
- Database trả các bản ghi chấm công thô.
- API Server tổng hợp số ngày công, tổng giờ làm, số lần trễ, số lần về sớm, số lần vắng mặt và số bản ghi bị từ chối.
- Nếu không có dữ liệu, Web Dashboard hiển thị thông báo không có dữ liệu.
- Nếu có dữ liệu, Web Dashboard hiển thị summary và bảng bản ghi chi tiết.
- Khi người dùng nhấn Xuất Excel hoặc Xuất PDF, Web Dashboard gửi request export kèm format.
- API Server truy vấn lại dữ liệu theo cùng bộ lọc và tạo file Excel/PDF.
- API Server trả file stream để trình duyệt tải file về máy người dùng.

## 10. UC-10 - Quản Lý Ngoại Lệ Chấm Công

File sơ đồ: `SD/UC10_ManageException.puml`

HR/Admin xem và xử lý ngoại lệ chấm công:

- HR/Admin vào mục Ngoại lệ trên Web Dashboard.
- Web Dashboard gọi API lấy các AttendanceRecord có status rejected, is_late TRUE hoặc is_early_leave TRUE.
- API Server truy vấn Database, sắp xếp theo thời gian mới nhất và trả danh sách ngoại lệ.
- Web Dashboard hiển thị các bản ghi bất thường cho HR/Admin.
- HR/Admin chọn một bản ghi để xem chi tiết.
- Web Dashboard gọi API lấy AttendanceRecord kèm FraudDetection.
- API Server trả chi tiết gồm lý do từ chối, tọa độ, kết quả FraudDetection và các cờ gian lận.
- Nếu HR/Admin phê duyệt thủ công, Web Dashboard gửi request approve.
- API Server cập nhật AttendanceRecord thành approved, xóa rejection_reason nếu cần và ghi AuditLog `MANUAL_APPROVE`.
- Nếu HR/Admin chọn giữ nguyên từ chối, hệ thống không thay đổi trạng thái bản ghi.

## 11. UC-11 - Phát Hiện Gian Lận Và Xác Minh Gương Mặt

File sơ đồ: `SD/UC11_FraudDetection.puml`

UC-11 được kích hoạt tự động trong luồng check-in/check-out:

- API Server gọi Fraud Service với employee_id, device_fingerprint, GPS, gps_accuracy, ảnh gương mặt, liveness_signals và raw_signals.
- Fraud Service đọc cờ mock_location từ hệ điều hành thiết bị.
- Fraud Service truy vấn 3 vị trí chấm công gần nhất của nhân viên để phân tích tốc độ di chuyển.
- Nếu tốc độ bất thường, gps_accuracy không hợp lệ hoặc altitude bất thường, hệ thống đánh dấu gps_spoofing_detected.
- Fraud Service truy vấn Device theo device_fingerprint và employee_id để kiểm tra thiết bị lạ.
- Nếu thiết bị không tồn tại hoặc chưa được tin cậy, hệ thống đánh dấu unknown_device.
- Fraud Service lấy face_template của nhân viên từ Database.
- Fraud Service gọi Face Verification Service để so khớp face_image với face_template và kiểm tra liveness.
- Face Verification Service trả face_match_score, liveness_score, face_matched và liveness_passed.
- Fraud Service xác định face_mismatch_detected và liveness_failed.
- Fraud Service tính confidence_score bắt đầu từ 100 và trừ điểm theo từng dấu hiệu gian lận.
- Fraud Service trả FraudResult cho API Server.
- API Server lưu FraudDetection vào Database với flags, confidence_score, raw_signals và thời điểm kiểm tra.
- Nếu liveness_failed hoặc confidence_score thấp, API Server đánh dấu yêu cầu chấm công bị từ chối.
- Nếu confidence_score ở vùng nghi ngờ, hệ thống vẫn có thể ghi nhận nhưng tạo AuditLog để HR xem xét.
- Nếu confidence_score đủ tin cậy, quyết định cuối cùng phụ thuộc vào kết quả kiểm tra geofence.

## 12. UC-12 - Phát Hiện Chấm Công Hộ

File sơ đồ: `SD/UC12_BuddyPunch.puml`

UC-12 kiểm tra khả năng chấm công hộ và chạy song song với các kiểm tra gian lận khác:

- API Server gọi Fraud Service với device_fingerprint, employee_id, tọa độ và timestamp.
- Fraud Service truy vấn các employee_id đã dùng cùng thiết bị trong 1 giờ gần nhất.
- Nếu thiết bị đã được dùng cho employee khác trong khoảng thời gian ngắn, hệ thống đánh dấu buddy_punch_suspected với reason `device_shared`.
- Nếu thiết bị chỉ dùng cho một employee, hệ thống chưa đánh dấu nghi ngờ ở bước này.
- Fraud Service truy vấn vị trí chấm công gần nhất của employee hiện tại.
- Fraud Service tính khoảng cách và thời gian giữa hai lần chấm công.
- Nếu tốc độ di chuyển vượt ngưỡng thực tế, hệ thống đánh dấu buddy_punch_suspected với reason `impossible_travel`.
- Fraud Service trả kết quả buddy_punch_suspected cho API Server.
- Nếu có nghi ngờ, API Server cập nhật FraudDetection và ghi AuditLog `BUDDY_PUNCH_ALERT`.
- Hệ thống không tự động reject trong mọi trường hợp buddy punching, mà ghi nhận để HR xem xét ở UC-10.

## 13. UC-13 - Quản Lý Thiết Bị Tin Cậy

File sơ đồ: `SD/UC13_ManageDevice.puml`

Admin quản lý danh sách thiết bị đã đăng ký:

- Admin vào mục Quản lý Thiết bị trên Web Dashboard.
- Web Dashboard gọi API lấy danh sách thiết bị, có thể lọc theo employee_id.
- API Server truy vấn Device kết hợp Employee và trả danh sách thiết bị.
- Web Dashboard hiển thị thông tin thiết bị gồm nhân viên, platform, model, is_trusted và registered_at.
- Khi Admin đánh dấu thiết bị tin cậy, Web Dashboard gửi request cập nhật `is_trusted=true`.
- API Server update Device, ghi AuditLog `DEVICE_TRUST` và trả 200 OK.
- Web Dashboard thông báo thiết bị đã được tin cậy.
- Khi Admin thu hồi tin cậy, Web Dashboard gửi request cập nhật `is_trusted=false`.
- API Server update Device, ghi AuditLog `DEVICE_UNTRUST` và trả 200 OK.
- Từ lần check-in tiếp theo, thiết bị bị thu hồi tin cậy sẽ kích hoạt cờ unknown_device trong FraudDetection.

## 14. UC-14 - Tra Cứu Audit Log

File sơ đồ: `SD/UC14_AuditLog.puml`

Admin tra cứu nhật ký hệ thống:

- Admin vào mục Audit Log trên Web Dashboard.
- Web Dashboard hiển thị form lọc theo actor, action_type, khoảng thời gian và target_entity.
- Admin nhập điều kiện lọc và nhấn tìm kiếm.
- Web Dashboard gửi request `GET /audit-logs` đến API Server.
- API Server truy vấn AuditLog theo điều kiện lọc, sắp xếp giảm dần theo created_at và giới hạn 100 bản ghi.
- Nếu không có kết quả, Web Dashboard hiển thị thông báo không có kết quả phù hợp.
- Nếu có kết quả, Web Dashboard hiển thị bảng log gồm account, action_type, target_entity, target_id, ip_address và created_at.
- Admin nhấp vào một log entry để xem chi tiết.
- Web Dashboard gọi API lấy log theo log_id.
- API Server trả payload JSON đầy đủ.
- Web Dashboard hiển thị chi tiết log ở chế độ chỉ đọc.
- AuditLog không có API UPDATE hoặc DELETE để đảm bảo tính truy vết.

## 15. UC-15 - Quản Lý Nhân Viên Và Phòng Ban

File sơ đồ: `SD/UC15_ManageEmployee.puml`

Admin/HR quản lý nhân viên và phòng ban:

- Admin/HR vào mục Quản lý Nhân viên và chọn Thêm mới.
- Web Dashboard nhận các thông tin full_name, department_id, position, email, phone và hire_date.
- Web Dashboard gửi request `POST /employees` đến API Server.
- API Server kiểm tra email có bị trùng trong Database hay không.
- Nếu email trùng, API Server trả 409 Conflict và Web Dashboard hiển thị lỗi.
- Nếu email hợp lệ, API Server insert Employee với status active.
- API Server tạo Account liên kết với Employee, dùng email làm username và mật khẩu tạm đã băm.
- API Server ghi AuditLog `EMPLOYEE_CREATE` và trả employee_id, account_id.
- Khi cập nhật thông tin, Admin/HR chọn nhân viên, sửa dữ liệu và lưu.
- API Server update Employee, ghi AuditLog `EMPLOYEE_UPDATE` và trả 200 OK.
- Khi vô hiệu hóa nhân viên, Web Dashboard gửi request deactivate.
- API Server cập nhật Employee thành inactive, khóa Account tương ứng và ghi AuditLog `EMPLOYEE_DEACTIVATE`.
- Với phòng ban, Admin/HR gửi request tạo hoặc sửa Department.
- API Server insert/update Department, ghi AuditLog và trả trạng thái thành công.

## 16. UC-16 - Xem Dashboard Tổng Quan

File sơ đồ: `SD/UC16_Dashboard.puml`

CEO/HR/Admin xem dashboard tổng quan:

- Người dùng đăng nhập thành công và truy cập trang Dashboard.
- Web Dashboard gọi API `GET /dashboard/summary`.
- API Server truy vấn tổng số nhân viên active từ bảng Employee.
- API Server đếm số nhân viên đã check-in trong ngày từ AttendanceRecord.
- API Server tính số lượt đi trễ dựa trên `is_late` trong AttendanceRecord.
- API Server đếm số cảnh báo gian lận trong ngày bằng cách join FraudDetection với AttendanceRecord.
- API Server truy vấn vị trí nhân viên đang check-in và chưa check-out để phục vụ mini-map.
- Database trả dữ liệu KPI và danh sách vị trí nhân viên.
- API Server trả summary gồm total_employees, checked_in_today, on_time_rate, fraud_alerts_today và active_locations.
- Web Dashboard hiển thị KPI cards, mini-map vị trí nhân viên và biểu đồ tỷ lệ đúng giờ.
- Trong chế độ auto refresh, Web Dashboard gọi lại API mỗi 60 giây và cập nhật dashboard.

## 17. UC-17 - Quản Lý Tòa Nhà Và Tầng

File sơ đồ: `SD/UC17_ManageBuilding.puml`

Admin quản lý dữ liệu tòa nhà và tầng:

- Admin vào mục Quản lý Tòa nhà và chọn Thêm tòa nhà.
- Admin nhập name, address, center_lat, center_lng, total_floors và arcgis_layer_id.
- Web Dashboard gửi request `POST /buildings` đến API Server.
- API Server gọi ArcGIS Scene View để validate arcgis_layer_id.
- Nếu layer không hợp lệ, API Server trả 400 Bad Request và Web Dashboard hiển thị cảnh báo tích hợp ArcGIS.
- Nếu layer hợp lệ, API Server insert Building, ghi AuditLog `BUILDING_CREATE` và trả building_id.
- Web Dashboard hiển thị tòa nhà trên bản đồ 3D.
- Admin chọn Building và thêm tầng.
- Admin nhập floor_number, floor_name, altitude_min và altitude_max.
- Web Dashboard gửi request tạo Floor cho building_id tương ứng.
- API Server insert Floor, ghi AuditLog `FLOOR_CREATE` và trả floor_id.
- Sau khi tạo Floor, Admin có thể cấu hình geofence cho tầng đó ở UC-06.
- Khi Admin xem danh sách, Web Dashboard gọi API lấy Building kèm Floors.
- API Server truy vấn Database và trả danh sách tòa nhà/tầng cho Dashboard hiển thị.
