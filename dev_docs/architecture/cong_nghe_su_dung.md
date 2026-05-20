# 3.1 Công Nghệ Sử Dụng

Hệ thống chấm công thông minh sử dụng các công nghệ phục vụ cho ba nhóm chính: giao diện người dùng, xử lý nghiệp vụ phía máy chủ và lưu trữ dữ liệu. Ngoài ra, hệ thống còn sử dụng công nghệ GIS 3D, GPS, xác minh khuôn mặt và phát hiện gian lận để đáp ứng yêu cầu chấm công theo vị trí thực tế.

## 3.1.1 Công nghệ giao diện

| Thành phần | Công nghệ sử dụng | Mục đích sử dụng |
| --- | --- | --- |
| Web Dashboard | React, TypeScript, Vite | Xây dựng giao diện quản trị cho HR/Admin/CEO, hỗ trợ dashboard, bảng dữ liệu, biểu đồ và quản lý hệ thống. |
| Mobile App | React Native, TypeScript | Xây dựng ứng dụng di động cho nhân viên trên Android/iOS, hỗ trợ đăng nhập, chấm công, xem lịch sử và nhận thông báo. |
| Giao diện bản đồ 3D | ArcGIS Maps SDK for JavaScript | Hiển thị bản đồ 3D, tòa nhà, tầng, marker nhân viên và vùng chấm công trên Web Dashboard. |
| Biểu đồ báo cáo | Chart.js hoặc Recharts | Hiển thị KPI, tỷ lệ đúng giờ, số lượt trễ/về sớm và các thống kê chấm công. |
| Mockup giao diện | HTML5, CSS3 | Dựng wireframe/mockup cho các màn hình Web Dashboard và Mobile App. |

React và React Native được lựa chọn để thống nhất cách xây dựng giao diện bằng TypeScript, giúp nhóm phát triển tái sử dụng tư duy component và quản lý trạng thái dễ hơn. Web Dashboard ưu tiên khả năng hiển thị dữ liệu lớn, còn Mobile App ưu tiên thao tác nhanh khi chấm công.

## 3.1.2 Công nghệ phía máy chủ

| Thành phần | Công nghệ sử dụng | Mục đích sử dụng |
| --- | --- | --- |
| API Server | Python, FastAPI, Pydantic | Xây dựng API xử lý đăng nhập, chấm công, quản trị dữ liệu, báo cáo và audit log. |
| Xác thực và phân quyền | JWT, bcrypt hoặc Argon2 | Cấp token đăng nhập, phân quyền theo vai trò và băm mật khẩu người dùng. |
| Kiểm tra gian lận | Python, FastAPI | Xử lý các kiểm tra mock location, GPS spoofing, thiết bị lạ và nghi ngờ chấm công hộ trong cùng backend hoặc service riêng. |
| Xác minh khuôn mặt | OpenCV, MediaPipe hoặc Face Recognition | So khớp ảnh selfie, kiểm tra khuôn mặt và hỗ trợ kiểm tra liveness. |
| Xuất báo cáo | openpyxl, pandas, ReportLab | Tạo file báo cáo chấm công dạng Excel hoặc PDF. |
| Tác vụ nền | Redis, Celery hoặc RQ | Xử lý các tác vụ không cần phản hồi ngay như gửi thông báo, tạo file báo cáo hoặc đồng bộ dữ liệu. |
| Tài liệu API | OpenAPI/Swagger UI của FastAPI | Cung cấp tài liệu API tự động để kiểm thử và tích hợp frontend/mobile. |

FastAPI được lựa chọn cho toàn bộ backend vì có hiệu năng tốt, cú pháp rõ ràng, hỗ trợ kiểu dữ liệu với Pydantic, tự sinh tài liệu OpenAPI và phù hợp để xây dựng API theo module. Việc thống nhất backend bằng Python/FastAPI giúp các phần nghiệp vụ, xử lý ảnh, phát hiện gian lận và xuất báo cáo dùng chung một hệ sinh thái công nghệ, giảm chi phí tích hợp giữa nhiều nền tảng khác nhau.

## 3.1.3 Công nghệ cơ sở dữ liệu và lưu trữ

| Thành phần | Công nghệ sử dụng | Mục đích sử dụng |
| --- | --- | --- |
| Cơ sở dữ liệu chính | PostgreSQL trên Supabase | Lưu cả dữ liệu nghiệp vụ và dữ liệu GIS/3D như nhân viên, tài khoản, thiết bị, ca làm, chấm công, tòa nhà, tầng, geofence, lớp bản đồ và audit log. |
| Dữ liệu không gian | PostGIS trên PostgreSQL | Hỗ trợ truy vấn tọa độ, khoảng cách, vùng địa lý, bán kính, độ cao và dữ liệu geofence. |
| Thiết kế dữ liệu | DBML | Mô tả cấu trúc bảng, quan hệ và ràng buộc trước khi triển khai database. |
| Lưu ảnh và file | MinIO hoặc Amazon S3 | Lưu ảnh selfie, file báo cáo và các tài liệu xuất ra từ hệ thống. |
| Cache | Redis | Tăng tốc truy vấn dữ liệu thường dùng và hỗ trợ hàng đợi tác vụ nền. |

PostgreSQL trên Supabase được lựa chọn vì ổn định, phổ biến, dễ quản trị và phù hợp để lưu tập trung cả dữ liệu nghiệp vụ lẫn dữ liệu GIS/3D. PostGIS bổ sung khả năng xử lý dữ liệu không gian, cần thiết cho kiểm tra vùng chấm công theo tọa độ, bán kính, độ cao và tầng.

## 3.1.4 Công nghệ GIS, GPS và thiết bị

| Thành phần | Công nghệ sử dụng | Mục đích sử dụng |
| --- | --- | --- |
| Bản đồ GIS 3D | ArcGIS Platform, ArcGIS Scene View | Hiển thị và tương tác với mô hình tòa nhà 3D, tầng và marker nhân viên theo thời gian gần thực; dữ liệu mô hình và metadata được lưu trong Supabase PostgreSQL. |
| Định vị di động | GPS, altitude, gps_accuracy | Thu thập vị trí chấm công gồm kinh độ, vĩ độ, độ cao và độ chính xác. |
| Vùng chấm công | Geofence 3D | Kiểm tra nhân viên có nằm trong khu vực, tầng và phạm vi độ cao được phép hay không. |
| Thiết bị tin cậy | Device fingerprint | Nhận diện thiết bị nhân viên dùng để chấm công và phát hiện thiết bị lạ. |
| Camera di động | Mobile Camera API | Chụp selfie để xác minh người thực hiện chấm công. |

Việc kết hợp GPS, độ cao và geofence 3D giúp hệ thống phân biệt các tầng trong cùng một tòa nhà, hạn chế sai lệch khi nhiều tầng có cùng tọa độ mặt đất.

## 3.1.5 Công nghệ bảo mật và vận hành

| Thành phần | Công nghệ sử dụng | Mục đích sử dụng |
| --- | --- | --- |
| Giao tiếp bảo mật | HTTPS/TLS | Bảo vệ dữ liệu đăng nhập, vị trí và ảnh selfie trong quá trình truyền. |
| Reverse Proxy | Nginx | Điều phối request đến Web Dashboard, API Server và các service nội bộ. |
| Container hóa | Docker, Docker Compose | Đóng gói và chạy các thành phần như API Server, database, Redis và service xử lý gian lận. |
| Quản lý cấu hình | Environment Variables | Tách cấu hình môi trường, khóa bí mật, chuỗi kết nối database và thông tin ArcGIS. |
| Nhật ký hệ thống | Audit Log, Application Log | Theo dõi thao tác người dùng, lỗi hệ thống và các sự kiện quan trọng. |
| Quản lý mã nguồn | Git, GitHub | Lưu trữ mã nguồn, quản lý phiên bản và phối hợp làm việc nhóm. |

Các công nghệ bảo mật và vận hành giúp hệ thống dễ triển khai, dễ kiểm soát lỗi và đảm bảo dữ liệu nhạy cảm như vị trí, thông tin thiết bị và ảnh selfie được bảo vệ tốt hơn.

## 3.1.6 Lý do lựa chọn bộ công nghệ

Bộ công nghệ trên phù hợp với hệ thống chấm công thông minh vì đáp ứng được các yêu cầu chính: xây dựng giao diện web và mobile, xử lý nghiệp vụ theo thời gian gần thực, lưu trữ dữ liệu quan hệ, kiểm tra vị trí theo GIS 3D, xác minh thiết bị/khuôn mặt và tạo báo cáo cho người quản lý.

React, React Native và TypeScript giúp giảm sai sót khi phát triển giao diện. Python/FastAPI phù hợp để xây dựng backend API, xử lý nghiệp vụ, xử lý ảnh, phát hiện gian lận và tạo báo cáo trong cùng một nền tảng. Supabase PostgreSQL/PostGIS đảm bảo khả năng lưu trữ tập trung dữ liệu nghiệp vụ, dữ liệu GIS/3D và truy vấn vị trí. ArcGIS Platform đáp ứng yêu cầu hiển thị bản đồ 3D và tương tác với tòa nhà/tầng.
