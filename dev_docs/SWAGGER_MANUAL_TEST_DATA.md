# Swagger Manual Test Data

> Base URL: `http://localhost:8000/api/v1`  
> Swagger UI: `http://localhost:8000/docs`  
> Ngày tạo: 2026-05-23

---

## Hướng dẫn sử dụng

1. **Khởi động server**: `uv run fastapi dev app/main.py`
2. **Trình tự test**: Login → copy `access_token` → Authorize (nút Authorize góc trên phải Swagger) → test các endpoint khác
3. **Format token**: `Bearer <access_token>` (Swagger tự điền prefix khi dùng nút Authorize)

---

## Tài khoản test (đã seed vào DB)

| account_id | username | password | role |
|-----------|---------|----------|------|
| 1001 | `linh.tran@example.com` | `Admin@2026` | admin |
| 1002 | `minh.nguyen@example.com` | `Employee@2026` | employee |
| 1003 | `hoa.pham@example.com` | `Hr@2026xx` | hr |
| 1004 | `quang.le@example.com` | `Manager@2026` | manager |
| 1005 | `demo.admin@amaserver.local` | `Admin@2026` | admin |

> Để reset password về mặc định: `uv run python testing/seed_dev_accounts.py`

---

## 1. Authentication (`/auth`)

### POST `/auth/login`

```json
{
  "username": "linh.tran@example.com",
  "password": "Admin@2026"
}
```

> Thử với các role khác:

| Role | username | password |
|------|----------|----------|
| admin | `linh.tran@example.com` | `Admin@2026` |
| employee | `minh.nguyen@example.com` | `Employee@2026` |
| hr | `hoa.pham@example.com` | `Hr@2026xx` |
| manager | `quang.le@example.com` | `Manager@2026` |

> Thử case lỗi:

| Case | username | password |
|------|----------|----------|
| Sai password | `linh.tran@example.com` | `wrongpassword` |
| Không tồn tại | `nobody@test.com` | `Admin@2026` |
| Thiếu field | _(bỏ trống password)_ | — |

---

### POST `/auth/refresh`

```json
{
  "refresh_token": "<refresh_token từ login>"
}
```

---

### GET `/auth/me`

> Không có body. Cần Authorization header.

---

### POST `/auth/logout`

```json
{
  "refresh_token": "<refresh_token từ login>"
}
```

> Sau logout, thử gọi lại `/auth/me` — kỳ vọng 401.

---

### PUT `/auth/change-password`

```json
{
  "current_password": "Admin@123",
  "new_password": "NewPass@456",
  "confirm_password": "NewPass@456"
}
```

> Case lỗi: `new_password` không có chữ hoa → 422; `confirm_password` không khớp → 400.

---

## 2. Employees (`/employees`)

> Yêu cầu role: `hr` hoặc `admin` (trừ GET detail).

### GET `/employees`

Query params (tất cả optional):

| Param | Value ví dụ |
|-------|------------|
| `page` | `1` |
| `limit` | `20` |

---

### POST `/employees`

```json
{
  "full_name": "Nguyễn Văn An",
  "department_id": 1,
  "position": "Software Engineer",
  "email": "nguyenvanan@company.com",
  "phone": "0901234567",
  "hire_date": "2025-01-15",
  "role": "employee",
  "temporary_password": "TempPass@2025"
}
```

> `role` enum: `employee` | `hr` | `manager` | `admin`

---

### GET `/employees/{employee_id}`

> Path param: `employee_id = 1`

---

### PUT `/employees/{employee_id}`

```json
{
  "full_name": "Nguyễn Văn An Updated",
  "position": "Senior Software Engineer",
  "phone": "0909999999"
}
```

> Tất cả fields đều optional — gửi chỉ field cần cập nhật.

---

### PUT `/employees/{employee_id}/deactivate`

```json
{
  "reason": "Nghỉ việc tự nguyện"
}
```

---

### PUT `/employees/{employee_id}/assign-shift`

```json
{
  "shift_id": 1
}
```

---

### GET `/employees/{employee_id}/face/status`

> Path param: `employee_id = 1`  
> Role: `admin` hoặc `hr` — không cho `employee`.

---

### DELETE `/employees/{employee_id}/face`

> Path param: `employee_id = 1`  
> Role: `admin` chỉ.

---

## 3. Departments (`/departments`)

### GET `/departments`

> Không có body/query bắt buộc. Role: `hr`, `manager`, `admin`.

---

### POST `/departments`

```json
{
  "name": "Engineering",
  "description": "Phòng kỹ thuật phần mềm",
  "manager_id": null
}
```

> `manager_id` optional — nếu có, phải là `employee_id` hợp lệ.

---

### PUT `/departments/{department_id}`

```json
{
  "name": "Engineering & R&D",
  "description": "Phòng kỹ thuật và nghiên cứu phát triển"
}
```

---

## 4. Shifts (`/shifts`)

### GET `/shifts`

> Không có body/query bắt buộc.

---

### POST `/shifts`

```json
{
  "employee_id": 1,
  "name": "Ca sáng",
  "start_time": "08:00:00",
  "end_time": "17:00:00",
  "late_tolerance_min": 15,
  "early_leave_min": 10,
  "apply_to_weekends": false
}
```

---

### PUT `/shifts/{shift_id}`

```json
{
  "name": "Ca sáng (cập nhật)",
  "late_tolerance_min": 10
}
```

---

## 5. Devices (`/devices`)

### POST `/devices/register`

> Role: `admin` hoặc `manager` — không cho `hr`.

```json
{
  "device_fingerprint": "fp_android_abcdef123456",
  "platform": "android",
  "model": "Samsung Galaxy S24",
  "os_version": "Android 14",
  "app_version": "1.0.0"
}
```

> `platform` enum: `android` | `ios` | `web` | `other`

---

### GET `/devices/my`

> Không cần body. Role: `admin` hoặc `manager`.

---

### GET `/devices`

> Không cần body. Role: `admin` chỉ.

---

### PUT `/devices/{device_id}/trust`

```json
{
  "is_trusted": true
}
```

> Để untrust: `"is_trusted": false`

---

## 6. Attendance (`/attendance`)

> ⚠️ Check-in và Check-out dùng **multipart/form-data**, KHÔNG phải JSON.  
> Trên Swagger: chọn "multipart/form-data" và điền từng field.

### POST `/attendance/check-in` — multipart/form-data

| Field | Value | Required |
|-------|-------|----------|
| `device_fingerprint` | `fp_android_abcdef123456` | ✅ |
| `platform` | `android` | ✅ |
| `latitude` | `10.8704078` | ✅ |
| `longitude` | `106.80290665` | ✅ |
| `altitude` | `2.5` | ✅ |
| `gps_accuracy` | `8.0` | ✅ |
| `liveness_signals` | `{"blink_detected":true,"head_pose_changed":true,"challenge_passed":false}` | ✅ |
| `face_image` | _(upload file ảnh .jpg)_ | ✅ |
| `employee_id` | `1` | optional |
| `model` | `Samsung Galaxy S24` | optional |
| `is_mock_location` | `false` | optional |
| `raw_signals` | `{"provider":"gps","speed_mps":0.2,"bearing":90.0}` | optional |

> **Tọa độ UIT Building A**: `lat=10.8704078`, `lng=106.80290665` (trong geofence)  
> **Tọa độ ngoài geofence**: `lat=10.8750000`, `lng=106.8100000`

---

### POST `/attendance/check-out` — multipart/form-data

> Giống check-in, dùng cùng fields. Cần đã có record check-in hợp lệ trước đó.

| Field | Value |
|-------|-------|
| `device_fingerprint` | `fp_android_abcdef123456` |
| `platform` | `android` |
| `latitude` | `10.8704078` |
| `longitude` | `106.80290665` |
| `altitude` | `2.5` |
| `gps_accuracy` | `8.0` |
| `liveness_signals` | `{"blink_detected":true,"head_pose_changed":false,"challenge_passed":false}` |
| `face_image` | _(upload file ảnh .jpg)_ |

---

### GET `/attendance/today-status`

> Không cần body. Role: `employee` hoặc `manager` — không cho `hr`.

---

### GET `/attendance/history`

Query params:

| Param | Value | Required |
|-------|-------|----------|
| `from` | `2026-05-01` | ✅ |
| `to` | `2026-05-23` | ✅ |
| `employee_id` | `1` | optional (HR/Admin mới dùng) |
| `page` | `1` | optional |
| `limit` | `20` | optional |

---

### GET `/attendance/exceptions`

> Role: `hr` hoặc `admin`.

Query params (tất cả optional):

| Param | Value ví dụ |
|-------|------------|
| `from` | `2026-05-01` |
| `to` | `2026-05-23` |
| `status` | `rejected` hoặc `pending` |
| `department_id` | `1` |
| `employee_id` | `1` |
| `page` | `1` |
| `limit` | `20` |

---

### GET `/attendance/{record_id}`

> Path param: `record_id = 1`. Role: `hr` hoặc `admin`.

---

### PUT `/attendance/{record_id}/approve`

```json
{
  "note": "Xác nhận chấm công hợp lệ sau khi kiểm tra thực tế"
}
```

> `note` là optional — có thể gửi `{}`.

---

## 7. Face Verification (`/employees/{employee_id}/face`, `/internal/face`)

### POST `/employees/{employee_id}/face/register` — multipart/form-data

> Role: `admin` hoặc `manager`. Path param: `employee_id = 1`.

| Field | Value |
|-------|-------|
| `face_image` | _(upload file ảnh khuôn mặt .jpg rõ nét, 1 người)_ |

---

### POST `/internal/face/verify` — multipart/form-data

| Field | Value |
|-------|-------|
| `employee_id` | `1` |
| `selfie_image` | _(upload file ảnh selfie .jpg)_ |

---

## 8. Geofence — Buildings (`/buildings`)

### GET `/buildings`

Query params (optional):

| Param | Value |
|-------|-------|
| `include_floors` | `true` |

---

### POST `/buildings`

```json
{
  "name": "Tòa nhà A - UIT",
  "address": "Tòa nhà A, Trường Đại học Công nghệ Thông tin - ĐHQG-HCM, Khu phố 6, Phường Linh Trung, TP. Thủ Đức, TP. HCM",
  "center_lat": 10.8704078,
  "center_lng": 106.80290665,
  "total_floors": 2,
  "arcgis_layer_id": "uit_building_a_layer_001"
}
```

---

### PUT `/buildings/{building_id}`

```json
{
  "name": "Tòa nhà A - UIT (cập nhật)",
  "total_floors": 3
}
```

---

## 9. Geofence — Floors (`/buildings/{building_id}/floors`, `/floors`)

### GET `/buildings/{building_id}/floors`

> Path param: `building_id = 1`

---

### POST `/buildings/{building_id}/floors`

```json
{
  "floor_number": 1,
  "floor_name": "Tầng 1 - Sảnh và Phòng Lab",
  "altitude_min": 0.0,
  "altitude_max": 4.0
}
```

> Tầng 2:

```json
{
  "floor_number": 2,
  "floor_name": "Tầng 2 - Phòng Hội Thảo",
  "altitude_min": 4.0,
  "altitude_max": 8.0
}
```

---

### PUT `/floors/{floor_id}`

```json
{
  "floor_name": "Tầng 1 - Sảnh Chính và Lab Máy Tính",
  "altitude_max": 4.5
}
```

---

## 10. Geofence — Zones (`/geofences`)

### GET `/geofences`

> Không cần body. Role: `hr`, `manager`, `admin`.

---

### POST `/geofences`

> Sảnh chính tầng 1 (dùng data UIT Building A):

```json
{
  "floor_id": 1,
  "name": "A1 - Sảnh Chính",
  "center_lat": 10.87012,
  "center_lng": 106.80288,
  "radius_meters": 30.0,
  "altitude_min": 0.0,
  "altitude_max": 4.0,
  "allow_checkin": true,
  "allow_checkout": true
}
```

> Phòng Lab máy tính:

```json
{
  "floor_id": 1,
  "name": "A1 - Phòng Lab Máy Tính",
  "center_lat": 10.87032,
  "center_lng": 106.80306,
  "radius_meters": 20.0,
  "altitude_min": 0.0,
  "altitude_max": 4.0,
  "allow_checkin": true,
  "allow_checkout": false
}
```

---

### PUT `/geofences/{geofence_id}`

```json
{
  "name": "A1 - Sảnh Chính (mở rộng)",
  "radius_meters": 40.0,
  "is_active": true
}
```

---

### PUT `/geofences/{geofence_id}/disable`

> Không cần body. Path param: `geofence_id = 1`.

---

## 11. Fraud Detection (`/fraud`, `/internal/fraud`)

### POST `/internal/fraud/evaluate`

> Case bình thường — không có fraud:

```json
{
  "employee_id": 1,
  "device_fingerprint": "fp_android_abcdef123456",
  "latitude": 10.8704078,
  "longitude": 106.80290665,
  "altitude": 2.5,
  "gps_accuracy": 8.0,
  "timestamp": "2026-05-23T08:00:00",
  "is_mock_location": false,
  "liveness_signals": {
    "blink_detected": true,
    "head_pose_changed": true,
    "challenge_passed": false
  }
}
```

> Case mock location:

```json
{
  "employee_id": 1,
  "device_fingerprint": "fp_android_abcdef123456",
  "latitude": 10.8704078,
  "longitude": 106.80290665,
  "altitude": 2.5,
  "gps_accuracy": 8.0,
  "timestamp": "2026-05-23T08:00:00",
  "is_mock_location": true,
  "liveness_signals": {
    "blink_detected": false,
    "head_pose_changed": false,
    "challenge_passed": false
  }
}
```

> Case GPS spoofing (speed quá cao):

```json
{
  "employee_id": 1,
  "device_fingerprint": "fp_android_abcdef123456",
  "latitude": 10.8704078,
  "longitude": 106.80290665,
  "altitude": 2.5,
  "gps_accuracy": 8.0,
  "timestamp": "2026-05-23T08:00:00",
  "is_mock_location": false,
  "liveness_signals": {
    "blink_detected": true,
    "head_pose_changed": false,
    "challenge_passed": false
  },
  "raw_signals": {
    "provider": "gps",
    "speed_mps": 50.0,
    "bearing": 180.0
  }
}
```

---

### GET `/fraud/records`

Query params (tất cả optional):

| Param | Value ví dụ |
|-------|------------|
| `from` | `2026-05-01` |
| `to` | `2026-05-23` |
| `employee_id` | `1` |
| `mock_location` | `true` |
| `gps_spoofing` | `false` |
| `min_confidence_score` | `0` |
| `max_confidence_score` | `60` |
| `page` | `1` |
| `limit` | `20` |

---

### GET `/fraud/records/{fraud_id}`

> Path param: `fraud_id = 1`

---

## 12. Notifications (`/notifications`, `/internal/notifications`)

### GET `/notifications`

Query params (tất cả optional):

| Param | Value |
|-------|-------|
| `is_read` | `false` |
| `type` | `checkin_approved` |
| `page` | `1` |
| `limit` | `20` |

> `type` enum: `checkin_approved` | `checkin_rejected` | `checkout_approved` | `checkout_rejected` | `device_trusted` | `exception_flagged`

---

### PUT `/notifications/{notification_id}/read`

> Không cần body. Path param: `notification_id = 1`.

---

### PUT `/notifications/read-all`

> Không cần body. Đánh dấu toàn bộ notification của account hiện tại.

---

### GET `/notifications/preferences`

> Không cần body.

---

### PUT `/notifications/preferences`

```json
{
  "push_enabled": true,
  "in_app_enabled": true,
  "notify_checkin_approved": true,
  "notify_checkin_rejected": true,
  "notify_checkout_approved": true,
  "notify_checkout_rejected": true,
  "notify_device_trusted": false,
  "notify_exception_flagged": true
}
```

---

### POST `/internal/notifications/send`

```json
{
  "account_ids": [1, 2, 3],
  "type": "checkin_approved",
  "title": "Chấm công đã được duyệt",
  "body": "Lần check-in lúc 08:05 ngày 23/05/2026 đã được phê duyệt.",
  "meta": {
    "record_id": 42,
    "timestamp": "2026-05-23T08:05:00"
  }
}
```

> `type` enum: `checkin_approved` | `checkin_rejected` | `checkout_approved` | `checkout_rejected` | `device_trusted` | `exception_flagged`

---

## 13. Reports & Dashboard (`/dashboard`, `/realtime`, `/reports`)

### GET `/dashboard/summary`

Query params (optional):

| Param | Value |
|-------|-------|
| `date` | `2026-05-23` |

> Nếu không truyền `date`, server dùng ngày hôm nay (GMT+7).  
> Role: `manager`, `hr`, `admin`.

---

### GET `/realtime/employees-location`

Query params (tất cả optional):

| Param | Value ví dụ |
|-------|------------|
| `building_id` | `1` |
| `floor_id` | `1` |
| `department_id` | `1` |

> Role: `hr` hoặc `admin`.

---

### GET `/reports/attendance`

Query params:

| Param | Value | Required |
|-------|-------|----------|
| `from` | `2026-05-01` | ✅ |
| `to` | `2026-05-23` | ✅ |
| `department_id` | `1` | optional |
| `employee_id` | `1` | optional |

> Role: `manager`, `hr`, `admin`.

---

### GET `/reports/attendance/export`

Query params:

| Param | Value | Required |
|-------|-------|----------|
| `format` | `excel` hoặc `pdf` | ✅ |
| `from` | `2026-05-01` | ✅ |
| `to` | `2026-05-23` | ✅ |
| `department_id` | `1` | optional |
| `employee_id` | `1` | optional |

> Swagger sẽ tải file xuống trực tiếp. Role: `hr` hoặc `admin` (không cho `manager`).

---

## 14. Audit Logs (`/audit-logs`)

### GET `/audit-logs`

Query params (tất cả optional):

| Param | Value ví dụ |
|-------|------------|
| `account_id` | `1` |
| `action_type` | `login` |
| `offset` | `0` |
| `limit` | `20` |

> `action_type` enum: `login` | `logout` | `checkin` | `checkout` | `approve` | `reject`  
> Role: `hr`, `manager`, `admin`.

---

### GET `/audit-logs/{log_id}`

> Path param: `log_id = 1`. Role: `hr`, `manager`, `admin`.

---

## Phụ lục — Role Permission Matrix

| Endpoint | employee | hr | manager | admin |
|----------|----------|----|---------|-------|
| Login / Me / Logout | ✅ | ✅ | ✅ | ✅ |
| Change Password | ✅ | ✅ | ✅ | ✅ |
| GET employees | ❌ | ✅ | ✅ | ✅ |
| POST/PUT/DELETE employees | ❌ | ✅ | ❌ | ✅ |
| GET/POST departments | ❌ | ✅ | ✅ | ✅ |
| PUT departments | ❌ | ❌ | ❌ | ✅ |
| GET/POST/PUT shifts | ❌ | ✅ | ✅ | ✅ |
| Register/Trust device | ❌ | ❌ | ✅ | ✅ |
| GET devices | ❌ | ❌ | ❌ | ✅ |
| Check-in / Check-out | ✅ | ❌ | ✅ | ✅ |
| Attendance history (own) | ✅ | ❌ | ✅ | ✅ |
| Attendance history (any) | ❌ | ✅ | ✅ | ✅ |
| Attendance exceptions | ❌ | ✅ | ✅ | ✅ |
| Approve attendance | ❌ | ✅ | ✅ | ✅ |
| Face register/delete | ❌ | ❌ | ✅ | ✅ |
| Face status | ❌ | ✅ | ✅ | ✅ |
| Buildings/Floors/Geofences (GET) | ❌ | ✅ | ✅ | ✅ |
| Buildings/Floors/Geofences (write) | ❌ | ❌ | ❌ | ✅ |
| Fraud records | ❌ | ✅ | ❌ | ✅ |
| Dashboard/Reports | ❌ | ✅ | ✅ | ✅ |
| Export report | ❌ | ✅ | ❌ | ✅ |
| Audit logs | ❌ | ✅ | ✅ | ✅ |
| Notifications (own) | ✅ | ✅ | ✅ | ✅ |
