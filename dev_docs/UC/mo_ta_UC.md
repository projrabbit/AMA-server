# Mô Tả Use Case - Hệ Thống Chấm Công Thông Minh

Tài liệu này mô tả các trường hợp sử dụng chính của hệ thống chấm công tự động sử dụng GIS 3D và GPS. Cách trình bày gồm tác nhân, mô tả, điều kiện trước, điều kiện sau và luồng sự kiện giữa tác nhân với hệ thống.

## Danh Sách Tác Nhân

| STT | Tác nhân | Ý nghĩa |
| --- | --- | --- |
| 1 | Nhân viên | Người dùng sử dụng Mobile App để đăng nhập, check-in, check-out, nhận thông báo và xem lịch sử chấm công cá nhân. |
| 2 | HR / Admin | Người quản trị vận hành hệ thống, quản lý nhân viên, ca làm việc, thiết bị, geofence, ngoại lệ, audit log và báo cáo. |
| 3 | CEO / Ban lãnh đạo | Người xem dashboard tổng quan và báo cáo chấm công phục vụ theo dõi tình hình nhân sự. |
| 4 | Hệ thống tự động | Thành phần xử lý tự động, gồm kiểm tra gian lận, đối chiếu vị trí, ghi nhận kết quả và tạo audit log. |

## Danh Sách Use Case

| STT | Mã UC | Use Case | Tác nhân |
| --- | --- | --- | --- |
| 1 | UC-01 | Đăng nhập hệ thống | Nhân viên / HR / Admin / CEO |
| 2 | UC-02 | Thực hiện Check-in | Nhân viên |
| 3 | UC-03 | Thực hiện Check-out | Nhân viên |
| 4 | UC-04 | Xem lịch sử chấm công cá nhân | Nhân viên |
| 5 | UC-05 | Nhận thông báo trạng thái chấm công | Nhân viên |
| 6 | UC-06 | Quản lý Geofence 3D | HR / Admin |
| 7 | UC-07 | Xem bản đồ GIS 3D real-time | HR / Admin |
| 8 | UC-08 | Quản lý ca làm việc | HR / Admin |
| 9 | UC-09 | Xem và xuất báo cáo chấm công | HR / Admin / CEO |
| 10 | UC-10 | Quản lý ngoại lệ chấm công | HR / Admin |
| 11 | UC-11 | Phát hiện Mock Location / GPS Spoofing | Hệ thống tự động |
| 12 | UC-12 | Phát hiện chấm công hộ | Hệ thống tự động |
| 13 | UC-13 | Quản lý thiết bị tin cậy | Admin |
| 14 | UC-14 | Tra cứu Audit Log | Admin |
| 15 | UC-15 | Quản lý nhân viên và phòng ban | HR / Admin |
| 16 | UC-16 | Xem Dashboard tổng quan | CEO / HR / Admin |
| 17 | UC-17 | Quản lý tòa nhà và tầng | Admin |

## UC-01 - Đăng Nhập Hệ Thống

- Tác nhân: Nhân viên, HR, Admin, CEO.
- Mô tả: Người dùng nhập tài khoản và mật khẩu để truy cập vào Mobile App hoặc Web Dashboard.
- Điều kiện trước: Người dùng đã có tài khoản trong hệ thống và tài khoản chưa bị khóa.
- Điều kiện sau: Nếu đăng nhập thành công, hệ thống cấp token đăng nhập và điều hướng người dùng đến màn hình phù hợp với vai trò.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Người dùng mở màn hình đăng nhập. | Hệ thống hiển thị form nhập username và password. |
| Người dùng nhập username, password và nhấn đăng nhập. | Hệ thống gửi thông tin đăng nhập đến API Server để xác thực. |
| Người dùng chờ kết quả xác thực. | Hệ thống truy vấn bảng Account, kiểm tra tài khoản có tồn tại và còn hoạt động hay không. |
| Không có hành động bổ sung. | Nếu tài khoản không tồn tại hoặc bị khóa, hệ thống trả thông báo lỗi. |
| Không có hành động bổ sung. | Nếu mật khẩu sai, hệ thống báo sai mật khẩu và cho phép nhập lại. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống cập nhật `last_login_at`, ghi AuditLog và trả JWT token kèm role. |
| Người dùng nhận kết quả đăng nhập. | Ứng dụng điều hướng người dùng đến màn hình chính tương ứng với quyền của tài khoản. |

## UC-02 - Thực Hiện Check-in

- Tác nhân: Nhân viên.
- Mô tả: Nhân viên thực hiện chấm công vào ca làm việc bằng Mobile App. Hệ thống thu GPS 3D, kiểm tra thiết bị, đối chiếu geofence và chạy kiểm tra gian lận.
- Điều kiện trước: Nhân viên đã đăng nhập, thiết bị có GPS và đã đăng ký trong hệ thống.
- Điều kiện sau: Hệ thống tạo bản ghi AttendanceRecord với trạng thái approved hoặc rejected, đồng thời ghi AuditLog.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Nhân viên nhấn nút Check-in trên Mobile App. | Ứng dụng thu tọa độ GPS gồm latitude, longitude, altitude và độ chính xác GPS. |
| Nhân viên chụp selfie theo yêu cầu của ứng dụng. | Ứng dụng thu hình ảnh gương mặt và tín hiệu liveness để gửi kèm yêu cầu. |
| Ứng dụng gửi yêu cầu check-in. | API Server kiểm tra Employee, Device và ca làm việc đang áp dụng. |
| Không có hành động bổ sung. | Hệ thống gọi Fraud Detection để kiểm tra mock location, GPS spoofing, thiết bị lạ, gương mặt và liveness. |
| Không có hành động bổ sung. | Hệ thống lấy danh sách geofence hoặc GeofenceRule đang hoạt động phù hợp với độ cao hiện tại. |
| Không có hành động bổ sung. | Nếu GPS accuracy kém, hệ thống từ chối hoặc cảnh báo theo cấu hình và ghi AuditLog. |
| Không có hành động bổ sung. | Nếu phát hiện gian lận rõ ràng, hệ thống tạo AttendanceRecord bị từ chối với lý do `fraud_detected`. |
| Không có hành động bổ sung. | Nếu ngoài vùng geofence, hệ thống tạo AttendanceRecord bị từ chối với lý do `outside_geofence`. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống tạo AttendanceRecord approved, tính `is_late` và lưu ca làm việc tương ứng. |
| Nhân viên xem phản hồi trên ứng dụng. | Ứng dụng hiển thị kết quả check-in thành công hoặc lý do bị từ chối. |

## UC-03 - Thực Hiện Check-out

- Tác nhân: Nhân viên.
- Mô tả: Nhân viên thực hiện chấm công ra khi kết thúc ca làm việc. Hệ thống kiểm tra đã có check-in trong ngày, xác minh vị trí và kiểm tra gian lận trước khi ghi nhận.
- Điều kiện trước: Nhân viên đã đăng nhập và đã có bản ghi check-in hợp lệ trong ngày hoặc trong ca tương ứng.
- Điều kiện sau: Hệ thống tạo bản ghi AttendanceRecord loại check_out và ghi AuditLog.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Nhân viên nhấn nút Check-out trên Mobile App. | Ứng dụng thu GPS 3D, độ chính xác GPS, ảnh selfie và tín hiệu liveness. |
| Ứng dụng gửi yêu cầu check-out. | API Server tìm bản ghi check-in gần nhất của nhân viên trong ngày. |
| Không có hành động bổ sung. | Nếu chưa có check-in, hệ thống trả lỗi không thể check-out. |
| Không có hành động bổ sung. | Nếu đã có check-in, hệ thống gọi Fraud Detection để kiểm tra dữ liệu vị trí, thiết bị và gương mặt. |
| Không có hành động bổ sung. | Hệ thống lấy geofence hoặc GeofenceRule và ca làm việc tương ứng. |
| Không có hành động bổ sung. | Nếu phát hiện gian lận, hệ thống tạo bản ghi check-out rejected và ghi AuditLog. |
| Không có hành động bổ sung. | Nếu ngoài geofence, hệ thống tạo bản ghi check-out rejected với lý do ngoài vùng cho phép. |
| Không có hành động bổ sung. | Nếu vị trí hợp lệ nhưng checkout trước giờ kết thúc ca, hệ thống tạo bản ghi approved và đánh dấu `is_early_leave=TRUE`. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống tạo bản ghi check-out approved. |
| Nhân viên nhận kết quả. | Ứng dụng hiển thị trạng thái check-out thành công, về sớm hoặc bị từ chối. |

## UC-04 - Xem Lịch Sử Chấm Công Cá Nhân

- Tác nhân: Nhân viên.
- Mô tả: Nhân viên tra cứu lịch sử check-in/check-out của bản thân theo ngày, tuần hoặc tháng.
- Điều kiện trước: Nhân viên đã đăng nhập.
- Điều kiện sau: Danh sách bản ghi chấm công và tổng giờ làm được hiển thị nếu có dữ liệu.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Nhân viên mở tab Lịch sử chấm công. | Ứng dụng hiển thị bộ lọc thời gian. |
| Nhân viên chọn khoảng thời gian cần xem. | Ứng dụng gửi yêu cầu truy vấn lịch sử đến API Server. |
| Không có hành động bổ sung. | API Server truy vấn AttendanceRecord theo employee_id và khoảng thời gian. |
| Không có hành động bổ sung. | Nếu không có dữ liệu, hệ thống trả danh sách rỗng. |
| Không có hành động bổ sung. | Nếu có dữ liệu, hệ thống ghép các cặp check-in/check-out theo ngày để tính tổng giờ làm. |
| Nhân viên xem kết quả. | Ứng dụng hiển thị ngày chấm công, giờ vào, giờ ra, trạng thái, tầng làm việc và tổng giờ làm. |

## UC-05 - Nhận Thông Báo Trạng Thái Chấm Công

- Tác nhân: Nhân viên.
- Mô tả: Sau khi check-in hoặc check-out, nhân viên nhận phản hồi tức thời về kết quả xử lý.
- Điều kiện trước: Nhân viên đã gửi yêu cầu check-in hoặc check-out.
- Điều kiện sau: Nhân viên biết được yêu cầu đã thành công, bị từ chối hay gặp lỗi kết nối.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Nhân viên gửi yêu cầu check-in hoặc check-out. | API Server xử lý theo luồng UC-02 hoặc UC-03. |
| Không có hành động bổ sung. | Nếu approved, hệ thống trả thông báo chấm công thành công, kèm vị trí hoặc tầng nếu xác định được. |
| Không có hành động bổ sung. | Nếu outside_geofence, hệ thống trả thông báo ngoài vùng cho phép. |
| Không có hành động bổ sung. | Nếu có dấu hiệu gian lận, hệ thống trả thông báo chấm công bị từ chối. |
| Không có hành động bổ sung. | Nếu timeout hoặc lỗi mạng, ứng dụng hiển thị lỗi kết nối và cho phép thử lại. |
| Nhân viên đọc thông báo trên màn hình. | Ứng dụng hiển thị toast hoặc thông báo trạng thái trong thời gian phản hồi mục tiêu dưới 5 giây. |

## UC-06 - Quản Lý Geofence 3D

- Tác nhân: HR / Admin.
- Mô tả: HR/Admin tạo, chỉnh sửa hoặc vô hiệu hóa vùng/quy tắc geofence 3D theo tòa nhà, tầng và khu vực làm việc.
- Điều kiện trước: HR/Admin đã đăng nhập, tòa nhà và tầng đã được cấu hình.
- Điều kiện sau: Geofence hoặc GeofenceRule được lưu, cập nhật trạng thái và hiển thị trên bản đồ 3D nếu cần.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin mở trang Quản lý Geofence. | Hệ thống tải danh sách Building và Floor. |
| HR/Admin chọn tòa nhà và tầng trên ArcGIS Scene View. | Dashboard render bản đồ 3D tương ứng với layer đã cấu hình. |
| HR/Admin nhập thông tin vùng chấm công như tọa độ, bán kính, độ cao và tên vùng. | Hệ thống gửi yêu cầu tạo geofence đến API Server. |
| Không có hành động bổ sung. | API Server kiểm tra vùng có bị trùng hoặc overlap với vùng đang hoạt động hay không. |
| Không có hành động bổ sung. | Nếu trùng lặp, hệ thống trả cảnh báo xung đột để HR/Admin chỉnh lại. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống lưu geofence hoặc GeofenceRule, ghi AuditLog và trả mã vùng vừa tạo. |
| HR/Admin quan sát bản đồ. | Web Dashboard vẽ vùng geofence mới trên bản đồ 3D. |
| HR/Admin chọn vùng geofence và yêu cầu xóa hoặc vô hiệu hóa. | Hệ thống cập nhật `is_active=FALSE`, ghi AuditLog và xóa marker khỏi bản đồ. |

## UC-07 - Xem Bản Đồ GIS 3D Real-time

- Tác nhân: HR / Admin.
- Mô tả: HR/Admin xem vị trí nhân viên đang làm việc trên bản đồ GIS 3D theo thời gian gần thực.
- Điều kiện trước: HR/Admin đã đăng nhập và hệ thống có dữ liệu nhân viên đã check-in.
- Điều kiện sau: Bản đồ 3D hiển thị marker nhân viên và cập nhật định kỳ.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin mở tab Bản đồ 3D. | Web Dashboard khởi tạo ArcGIS SceneView và load layer tòa nhà. |
| Không có hành động bổ sung. | Hệ thống gọi API lấy danh sách nhân viên đang check-in nhưng chưa check-out trong ngày. |
| Không có hành động bổ sung. | API Server truy vấn AttendanceRecord và trả danh sách tọa độ lat/lng/altitude. |
| HR/Admin xem bản đồ. | ArcGIS Scene View vẽ marker của từng nhân viên tại vị trí tương ứng. |
| HR/Admin chọn bộ lọc tòa nhà, tầng hoặc phòng ban. | Hệ thống truy vấn lại dữ liệu theo điều kiện lọc và cập nhật marker trên bản đồ. |
| Không có hành động bổ sung. | Sau mỗi 30 giây, Web Dashboard tự động gọi API để cập nhật vị trí mới nhất. |

## UC-08 - Quản Lý Ca Làm Việc

- Tác nhân: HR / Admin.
- Mô tả: HR/Admin tạo, chỉnh sửa và gán ca làm việc cho nhân viên hoặc phòng ban.
- Điều kiện trước: HR/Admin đã đăng nhập.
- Điều kiện sau: Ca làm việc được lưu và được sử dụng khi kiểm tra check-in/check-out.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin mở menu Quản lý Ca. | Hệ thống hiển thị danh sách ca làm việc hiện có. |
| HR/Admin nhấn Tạo mới và nhập tên ca, giờ bắt đầu, giờ kết thúc, số phút cho phép trễ/về sớm. | Web Dashboard gửi yêu cầu tạo ca đến API Server. |
| Không có hành động bổ sung. | API Server kiểm tra xung đột thời gian với các ca đã có. |
| Không có hành động bổ sung. | Nếu xung đột, hệ thống trả cảnh báo để HR/Admin điều chỉnh. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống lưu Shift, ghi AuditLog và trả kết quả tạo thành công. |
| HR/Admin chọn nhân viên và gán ca. | Hệ thống cập nhật ca mặc định hoặc tạo bản ghi gán ca, sau đó ghi AuditLog. |
| HR/Admin sửa thông tin ca đang áp dụng. | Hệ thống cảnh báo thay đổi có thể ảnh hưởng đến các lần chấm công tiếp theo. |

## UC-09 - Xem Và Xuất Báo Cáo Chấm Công

- Tác nhân: HR / Admin / CEO.
- Mô tả: Người dùng quản lý xem báo cáo chấm công theo khoảng thời gian và xuất file nếu cần.
- Điều kiện trước: Có dữ liệu AttendanceRecord trong hệ thống.
- Điều kiện sau: Báo cáo được hiển thị hoặc file Excel/PDF được tải về.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin/CEO vào mục Báo cáo. | Hệ thống hiển thị bộ lọc thời gian, phòng ban và nhân viên. |
| Người dùng chọn điều kiện lọc. | Web Dashboard gửi yêu cầu lấy báo cáo đến API Server. |
| Không có hành động bổ sung. | API Server truy vấn AttendanceRecord kết hợp thông tin Employee. |
| Không có hành động bổ sung. | Hệ thống tổng hợp số ngày công, tổng giờ làm, số lần trễ, về sớm, vắng mặt và bản ghi bị từ chối. |
| Không có hành động bổ sung. | Nếu không có dữ liệu, hệ thống hiển thị thông báo không có dữ liệu. |
| Người dùng xem bảng báo cáo. | Nếu có dữ liệu, hệ thống hiển thị bảng tổng hợp và chi tiết. |
| Người dùng nhấn Xuất Excel hoặc Xuất PDF. | API Server tạo file theo định dạng được chọn và trả file stream về cho trình duyệt tải xuống. |

## UC-10 - Quản Lý Ngoại Lệ Chấm Công

- Tác nhân: HR / Admin.
- Mô tả: HR/Admin xem các bản ghi bất thường như bị từ chối, đi trễ, về sớm hoặc nghi ngờ gian lận và xử lý thủ công khi cần.
- Điều kiện trước: Có bản ghi chấm công có trạng thái rejected, `is_late=TRUE` hoặc `is_early_leave=TRUE`.
- Điều kiện sau: Ngoại lệ được xem chi tiết và có thể được phê duyệt thủ công nếu phù hợp.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin mở mục Ngoại lệ. | Hệ thống truy vấn các AttendanceRecord có trạng thái bất thường. |
| HR/Admin xem danh sách ngoại lệ. | Web Dashboard hiển thị các bản ghi bị từ chối, đi trễ hoặc về sớm. |
| HR/Admin chọn một bản ghi để xem chi tiết. | Hệ thống lấy AttendanceRecord kèm FraudDetection liên quan. |
| HR/Admin xem thông tin chi tiết. | Dashboard hiển thị lý do từ chối, tọa độ, cờ gian lận và điểm tin cậy. |
| HR/Admin nhấn Phê duyệt thủ công. | Hệ thống cập nhật trạng thái bản ghi thành approved, xóa lý do từ chối nếu cần và ghi AuditLog. |
| HR/Admin chọn giữ nguyên từ chối. | Hệ thống không thay đổi trạng thái bản ghi. |

## UC-11 - Phát Hiện Mock Location / GPS Spoofing

- Tác nhân: Hệ thống tự động.
- Mô tả: Hệ thống tự động kiểm tra tính tin cậy của dữ liệu GPS, thiết bị và gương mặt khi nhân viên check-in/check-out.
- Điều kiện trước: Có yêu cầu check-in hoặc check-out gửi đến API Server.
- Điều kiện sau: FraudDetection được lưu và kết quả được trả về để quyết định approved hoặc rejected.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| API Server nhận yêu cầu chấm công. | Hệ thống gọi Fraud Service với employee_id, device_fingerprint, GPS, ảnh gương mặt và raw_signals. |
| Không có hành động từ người dùng. | Fraud Service đọc cờ mock location từ hệ điều hành thiết bị. |
| Không có hành động từ người dùng. | Fraud Service lấy các vị trí gần nhất của nhân viên để tính tốc độ di chuyển và kiểm tra GPS spoofing. |
| Không có hành động từ người dùng. | Fraud Service kiểm tra thiết bị có tồn tại và được đánh dấu tin cậy hay không. |
| Không có hành động từ người dùng. | Fraud Service lấy face template và gọi Face Verification Service để xác minh gương mặt và liveness. |
| Không có hành động từ người dùng. | Hệ thống tính confidence_score từ các cờ mock location, spoofing, thiết bị lạ, sai gương mặt và liveness fail. |
| Không có hành động từ người dùng. | FraudDetection được lưu vào database. |
| Không có hành động từ người dùng. | Nếu gian lận rõ ràng hoặc điểm tin cậy thấp, hệ thống đánh dấu yêu cầu chấm công bị từ chối. |
| Không có hành động từ người dùng. | Nếu nằm trong vùng nghi ngờ, hệ thống vẫn có thể ghi nhận nhưng tạo cảnh báo để HR xem xét. |

## UC-12 - Phát Hiện Chấm Công Hộ

- Tác nhân: Hệ thống tự động.
- Mô tả: Hệ thống kiểm tra khả năng một thiết bị hoặc vị trí bất thường được dùng để chấm công hộ.
- Điều kiện trước: Có yêu cầu check-in/check-out và có device_fingerprint.
- Điều kiện sau: Cờ `buddy_punch_suspected` được cập nhật trong FraudDetection nếu phát hiện bất thường.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| API Server nhận yêu cầu chấm công. | Hệ thống gọi Fraud Service kiểm tra buddy punching. |
| Không có hành động từ người dùng. | Fraud Service truy vấn các nhân viên đã dùng cùng device_fingerprint trong thời gian gần. |
| Không có hành động từ người dùng. | Nếu thiết bị được dùng cho nhân viên khác trong 1 giờ, hệ thống đánh dấu nghi ngờ chấm công hộ. |
| Không có hành động từ người dùng. | Fraud Service truy vấn vị trí chấm công gần nhất của nhân viên. |
| Không có hành động từ người dùng. | Hệ thống tính tốc độ di chuyển giữa hai lần chấm công. |
| Không có hành động từ người dùng. | Nếu tốc độ di chuyển không thực tế, hệ thống đánh dấu `buddy_punch_suspected=TRUE`. |
| Không có hành động từ người dùng. | Hệ thống cập nhật FraudDetection và ghi AuditLog cảnh báo. |
| Không có hành động từ người dùng. | Trường hợp này không tự động từ chối nếu chưa đủ căn cứ, HR sẽ xem xét qua UC-10. |

## UC-13 - Quản Lý Thiết Bị Tin Cậy

- Tác nhân: Admin.
- Mô tả: Admin xem danh sách thiết bị đã đăng ký và cập nhật trạng thái tin cậy của thiết bị.
- Điều kiện trước: Admin đã đăng nhập.
- Điều kiện sau: Trạng thái `is_trusted` của thiết bị được cập nhật và ghi AuditLog.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Admin mở mục Quản lý Thiết bị. | Hệ thống truy vấn danh sách Device kèm thông tin nhân viên. |
| Admin xem danh sách thiết bị. | Dashboard hiển thị thiết bị, nhân viên sở hữu, nền tảng, model, thời điểm đăng ký và trạng thái tin cậy. |
| Admin chọn thiết bị và đánh dấu tin cậy. | Hệ thống cập nhật `Device.is_trusted=TRUE`, ghi AuditLog và trả kết quả thành công. |
| Admin chọn thiết bị và thu hồi tin cậy. | Hệ thống cập nhật `Device.is_trusted=FALSE`, ghi AuditLog và trả kết quả thành công. |
| Không có hành động bổ sung. | Từ lần chấm công tiếp theo, thiết bị không tin cậy sẽ kích hoạt cờ `unknown_device` trong FraudDetection. |

## UC-14 - Tra Cứu Audit Log

- Tác nhân: Admin.
- Mô tả: Admin tra cứu nhật ký thao tác trong hệ thống theo actor, action_type, thời gian hoặc thực thể bị tác động.
- Điều kiện trước: Admin đã đăng nhập và có quyền xem AuditLog.
- Điều kiện sau: Danh sách log hoặc chi tiết log được hiển thị ở chế độ chỉ đọc.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Admin mở mục Audit Log. | Hệ thống hiển thị form lọc theo actor, action_type, khoảng thời gian và target_entity. |
| Admin nhập điều kiện lọc và nhấn tìm kiếm. | Web Dashboard gửi yêu cầu truy vấn log đến API Server. |
| Không có hành động bổ sung. | API Server truy vấn AuditLog theo điều kiện, sắp xếp mới nhất trước và giới hạn số dòng trả về. |
| Không có hành động bổ sung. | Nếu không có kết quả, hệ thống hiển thị thông báo không tìm thấy log phù hợp. |
| Admin xem bảng log. | Nếu có kết quả, dashboard hiển thị account, action_type, target_entity, target_id, ip_address và created_at. |
| Admin nhấn vào một log để xem chi tiết. | Hệ thống truy vấn payload JSON đầy đủ và hiển thị ở chế độ chỉ đọc. |

## UC-15 - Quản Lý Nhân Viên Và Phòng Ban

- Tác nhân: HR / Admin.
- Mô tả: HR/Admin tạo nhân viên mới, cập nhật thông tin nhân viên, vô hiệu hóa tài khoản và quản lý phòng ban.
- Điều kiện trước: HR/Admin đã đăng nhập.
- Điều kiện sau: Dữ liệu Employee, Account hoặc Department được cập nhật và ghi AuditLog.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| HR/Admin mở Quản lý Nhân viên và chọn Thêm mới. | Hệ thống hiển thị form nhập thông tin nhân viên. |
| HR/Admin nhập họ tên, phòng ban, chức vụ, email, số điện thoại và ngày vào làm. | Web Dashboard gửi yêu cầu tạo nhân viên đến API Server. |
| Không có hành động bổ sung. | API Server kiểm tra email có bị trùng hay không. |
| Không có hành động bổ sung. | Nếu email trùng, hệ thống trả lỗi và yêu cầu nhập email khác. |
| Không có hành động bổ sung. | Nếu email hợp lệ, hệ thống tạo Employee, tạo Account liên kết và ghi AuditLog. |
| HR/Admin chọn nhân viên và cập nhật thông tin. | Hệ thống cập nhật Employee và ghi AuditLog. |
| HR/Admin chọn vô hiệu hóa nhân viên. | Hệ thống chuyển Employee sang inactive, khóa Account tương ứng và ghi AuditLog. |
| HR/Admin tạo hoặc sửa Department. | Hệ thống insert/update Department và ghi log thao tác. |

## UC-16 - Xem Dashboard Tổng Quan

- Tác nhân: CEO / HR / Admin.
- Mô tả: Người dùng quản lý xem các KPI tổng quan về tình hình chấm công trong ngày.
- Điều kiện trước: Người dùng đã đăng nhập vào Web Dashboard.
- Điều kiện sau: Dashboard hiển thị KPI, mini-map và biểu đồ theo dữ liệu mới nhất.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Người dùng đăng nhập thành công và mở Dashboard. | Web Dashboard gọi API lấy dữ liệu tổng quan. |
| Không có hành động bổ sung. | API Server truy vấn tổng số nhân viên active. |
| Không có hành động bổ sung. | API Server đếm số nhân viên check-in trong ngày, số lượt đi trễ và số cảnh báo gian lận. |
| Không có hành động bổ sung. | API Server lấy vị trí hiện tại của nhân viên đang check-in. |
| Người dùng xem dashboard. | Dashboard hiển thị KPI cards, mini-map vị trí nhân viên và biểu đồ tỷ lệ đúng giờ. |
| Không có hành động bổ sung. | Mỗi 60 giây, dashboard tự động refresh dữ liệu mới nhất. |

## UC-17 - Quản Lý Tòa Nhà Và Tầng

- Tác nhân: Admin.
- Mô tả: Admin tạo thông tin tòa nhà, tầng và ngưỡng độ cao để làm cơ sở cấu hình geofence 3D.
- Điều kiện trước: Admin đã đăng nhập và có thông tin ArcGIS layer nếu cần hiển thị trên Scene View.
- Điều kiện sau: Building và Floor được lưu, hiển thị trên bản đồ và sẵn sàng để cấu hình geofence.

| Hành động của tác nhân | Phản ứng của hệ thống |
| --- | --- |
| Admin mở Quản lý Tòa nhà và chọn Thêm tòa nhà. | Hệ thống hiển thị form nhập name, address, center_lat, center_lng, total_floors và arcgis_layer_id. |
| Admin gửi thông tin tòa nhà. | API Server kiểm tra arcgis_layer_id với ArcGIS Scene View. |
| Không có hành động bổ sung. | Nếu layer không hợp lệ, hệ thống trả lỗi tích hợp ArcGIS. |
| Không có hành động bổ sung. | Nếu hợp lệ, hệ thống lưu Building, ghi AuditLog và hiển thị tòa nhà trên bản đồ. |
| Admin chọn Building và thêm tầng. | Hệ thống hiển thị form nhập floor_number, floor_name, altitude_min và altitude_max. |
| Admin gửi thông tin tầng. | Hệ thống lưu Floor, ghi AuditLog và trả kết quả tạo tầng thành công. |
| Admin xem danh sách tòa nhà và tầng. | Hệ thống truy vấn Building kèm Floor và hiển thị danh sách để tiếp tục cấu hình geofence. |
