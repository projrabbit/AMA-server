# Mô Tả Kiến Trúc Dự Án

## 1. Tổng quan kiến trúc

Hệ thống chấm công thông minh được thiết kế theo mô hình client-server, gồm hai nhóm giao diện chính là Mobile App cho nhân viên và Web Dashboard cho HR/Admin/CEO. Các giao diện gửi yêu cầu đến API Server được xây dựng bằng FastAPI để xử lý nghiệp vụ chấm công, quản trị dữ liệu, báo cáo và giám sát vị trí.

Backend của hệ thống được thống nhất trên Python/FastAPI. Ngoài API Server chính, các thành phần hỗ trợ như Fraud Detection Service, Face Verification Service, Notification Service và Report Service có thể được tổ chức thành module FastAPI trong cùng backend hoặc tách thành các service FastAPI riêng khi cần mở rộng.

## 2. Các lớp trong hệ thống

### 2.1 Lớp giao diện người dùng

Mobile App phục vụ nhân viên với các chức năng đăng nhập, chấm công vào/ra, xác minh vị trí và khuôn mặt, nhận thông báo trạng thái, xem lịch sử chấm công và xem thông tin thiết bị.

Web Dashboard phục vụ HR/Admin/CEO với các chức năng xem tổng quan, theo dõi bản đồ 3D, quản lý vùng chấm công, quản lý tòa nhà/tầng, quản lý nhân viên/phòng ban/ca làm/thiết bị, xử lý ngoại lệ, xuất báo cáo và tra cứu nhật ký hệ thống.

### 2.2 Lớp API và nghiệp vụ

API Server là thành phần trung tâm tiếp nhận yêu cầu từ Mobile App và Web Dashboard. Thành phần này được xây dựng bằng FastAPI, chịu trách nhiệm xác thực người dùng, phân quyền theo vai trò, xử lý nghiệp vụ chấm công, kiểm tra ca làm việc, đối chiếu vùng chấm công, ghi nhận lịch sử và tạo dữ liệu báo cáo.

Các nhóm API chính gồm đăng nhập, chấm công, lịch sử chấm công, dashboard tổng quan, bản đồ 3D, geofence, ca làm việc, báo cáo, ngoại lệ, thiết bị tin cậy, audit log và quản lý nhân viên/phòng ban.

### 2.3 Lớp dịch vụ xử lý chuyên biệt

Fraud Detection Service kiểm tra các dấu hiệu bất thường khi chấm công như mock location, GPS spoofing, thiết bị lạ, vị trí không đủ chính xác hoặc nghi ngờ chấm công hộ.

Face Verification Service xử lý ảnh selfie, so khớp khuôn mặt nhân viên và kiểm tra liveness để giảm rủi ro chấm công thay.

GIS Integration kết nối với ArcGIS Platform để hiển thị bản đồ 3D, tòa nhà, tầng, marker nhân viên và vùng chấm công theo độ cao.

Notification Service gửi phản hồi tức thời sau khi chấm công và lưu thông báo để nhân viên xem lại trong ứng dụng.

Report Service tổng hợp dữ liệu chấm công theo nhân viên, phòng ban và khoảng thời gian, đồng thời hỗ trợ xuất file Excel/PDF.

### 2.4 Lớp dữ liệu

Cơ sở dữ liệu được lưu tập trung trên Supabase PostgreSQL và chia logic thành hai nhóm chính. Nhóm dữ liệu nghiệp vụ lưu thông tin nhân viên, tài khoản, phòng ban, thiết bị, ca làm, bản ghi chấm công, phát hiện gian lận và audit log. Nhóm dữ liệu GIS/3D lưu thông tin tòa nhà, tầng, cell space, lớp bản đồ, trạng thái vị trí, quy tắc geofence và metadata của mô hình 3D.

Supabase PostgreSQL được dùng làm hệ quản trị cơ sở dữ liệu chính cho cả dữ liệu nghiệp vụ và dữ liệu GIS/3D. Với dữ liệu vị trí và không gian, hệ thống có thể dùng PostGIS trên PostgreSQL để hỗ trợ truy vấn tọa độ, bán kính, vùng và khoảng cách. ArcGIS đóng vai trò hiển thị, tương tác bản đồ 3D và đồng bộ layer theo dữ liệu lưu trong Supabase.

## 3. Luồng xử lý chính

### 3.1 Luồng chấm công vào/ra

Nhân viên mở Mobile App và nhấn chấm công vào hoặc chấm công ra. Ứng dụng thu thập vị trí GPS 3D, độ chính xác GPS, thông tin thiết bị và ảnh selfie. Dữ liệu được gửi đến API Server để kiểm tra tài khoản, nhân viên, thiết bị và ca làm việc.

API Server gọi Fraud Detection Service và Face Verification Service để đánh giá độ tin cậy của yêu cầu. Sau đó hệ thống đối chiếu vị trí với geofence theo tòa nhà, tầng và độ cao. Nếu hợp lệ, hệ thống tạo bản ghi chấm công được duyệt. Nếu không hợp lệ, hệ thống tạo bản ghi bị từ chối hoặc đánh dấu cần xem xét, đồng thời ghi audit log và trả thông báo về Mobile App.

### 3.2 Luồng giám sát Dashboard

HR/Admin/CEO truy cập Web Dashboard để xem KPI tổng quan, tỷ lệ đúng giờ, số nhân viên đã chấm công, cảnh báo bất thường và danh sách nhân viên đang làm việc. Dashboard gọi API để lấy dữ liệu tổng hợp và tự cập nhật theo chu kỳ.

Với màn hình bản đồ 3D, Web Dashboard lấy danh sách vị trí nhân viên đang làm việc và hiển thị marker trên ArcGIS Scene View theo tòa nhà, tầng và phòng ban.

### 3.3 Luồng quản trị dữ liệu

Admin/HR quản lý nhân viên, phòng ban, ca làm việc, thiết bị tin cậy, tòa nhà, tầng và vùng chấm công trên Web Dashboard. Mọi thao tác tạo, cập nhật, vô hiệu hóa hoặc phê duyệt đều được gửi đến API Server và ghi lại trong audit log để đảm bảo truy vết.

### 3.4 Luồng báo cáo và xử lý ngoại lệ

HR/Admin/CEO chọn khoảng thời gian, phòng ban hoặc nhân viên để xem báo cáo chấm công. Hệ thống tổng hợp số ngày công, tổng giờ làm, số lần đi trễ, về sớm, vắng mặt và các bản ghi bị từ chối.

Các lượt chấm công bất thường được đưa vào màn hình ngoại lệ để HR/Admin xem chi tiết. Người quản trị có thể phê duyệt thủ công hoặc giữ trạng thái từ chối. Kết quả xử lý được lưu lại trong audit log.

## 4. Mô hình triển khai đề xuất

Hệ thống có thể triển khai theo mô hình nhiều container để dễ phát triển và mở rộng. Web Dashboard được phục vụ qua web server. Mobile App giao tiếp với FastAPI Backend qua HTTPS. FastAPI Backend kết nối với Supabase PostgreSQL/PostGIS để đọc ghi cả dữ liệu nghiệp vụ và dữ liệu GIS/3D, đồng thời kết nối MinIO và các service phụ trợ.

Các thành phần triển khai chính gồm Web Dashboard, FastAPI Backend, Fraud Detection Service, Face Verification Service, Supabase PostgreSQL/PostGIS, MinIO, Redis cache nếu cần, ArcGIS Platform và Reverse Proxy.

## 5. Yêu cầu phi chức năng hỗ trợ kiến trúc

Hệ thống cần đảm bảo xác thực và phân quyền theo vai trò, bảo mật mật khẩu bằng cơ chế băm, truyền dữ liệu qua HTTPS, bảo vệ ảnh selfie và dữ liệu vị trí, ghi audit log đầy đủ, phản hồi chấm công nhanh và hỗ trợ mở rộng khi số lượng nhân viên tăng.
