# Full API Documentation — AMA Smart Attendance System

**Project**: Smart Attendance System with 3D GIS, GPS, Face Verification, and Fraud Detection

**Base URL**: `/api/v1`

**Backend**: Python FastAPI

**Database**: Supabase PostgreSQL / PostGIS

**Authentication**: JWT Bearer token

**Default content type**: `application/json` unless specified

**File upload endpoints**: `multipart/form-data`

---

## Table of Contents

1. [API Conventions](#1-api-conventions)
2. [Module 1: Authentication](#2-module-1-authentication)
3. [Module 2: Attendance](#3-module-2-attendance)
4. [Module 3: Geofence](#4-module-3-geofence)
5. [Module 4: Fraud Detection](#5-module-4-fraud-detection)
6. [Module 5: Face Verification](#6-module-5-face-verification)
7. [Module 6: Notification](#7-module-6-notification)
8. [Module 7: Report](#8-module-7-report)
9. [Module 8: Audit Log](#9-module-8-audit-log)
10. [Module 9: Admin Management](#10-module-9-admin-management)
11. [Endpoint Summary Table](#11-endpoint-summary-table)
12. [Gap Analysis vs MVP Docs](#12-gap-analysis-vs-mvp-docs)

---

## 1. API Conventions

### 1.1 Authorization Header

All endpoints require this header unless explicitly marked `Public`:

```http
Authorization: Bearer <access_token>
```

### 1.2 Roles

| Role       | Description                        |
|------------|------------------------------------|
| `employee` | Mobile employee, can check in/out  |
| `hr`       | HR operator, manages attendance    |
| `manager`  | CEO / leadership, read-only viewer |
| `admin`    | System administrator               |

### 1.3 Standard Success Response

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

`meta` is optional, used for pagination or processing metrics.

### 1.4 Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### 1.5 HTTP Status Codes

| Status | Meaning                                                       |
|--------|---------------------------------------------------------------|
| `200`  | Request completed successfully                                |
| `201`  | Resource created                                              |
| `400`  | Invalid business input                                        |
| `401`  | Missing or invalid token                                      |
| `403`  | Authenticated but not authorized                              |
| `404`  | Resource not found                                            |
| `409`  | Conflict (duplicate, overlapping, invalid state)              |
| `422`  | Schema validation error (missing required fields, wrong type) |
| `500`  | Unexpected server error                                       |

### 1.6 Pagination

Query parameters for paginated list endpoints:

| Parameter | Type    | Default | Description         |
|-----------|---------|---------|---------------------|
| `page`    | integer | `1`     | Page number         |
| `limit`   | integer | `20`    | Items per page      |

Pagination meta block:

```json
{
  "page": 1,
  "limit": 20,
  "total": 125,
  "total_pages": 7
}
```

### 1.7 Date and Time Format

ISO 8601 throughout the entire API.

| Type     | Example                    |
|----------|----------------------------|
| Date     | `2026-05-20`               |
| Datetime | `2026-05-20T08:00:00+07:00`|
| Time     | `08:00:00`                 |

### 1.8 Core Enums

| Enum                | Values                                                                                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `employee_status`   | `active`, `inactive`, `on_leave`, `terminated`                                                                                                            |
| `account_role`      | `employee`, `hr`, `manager`, `admin`                                                                                                                      |
| `device_platform`   | `android`, `ios`, `web`, `other`                                                                                                                          |
| `attendance_type`   | `checkin`, `checkout`                                                                                                                                     |
| `attendance_status` | `pending`, `approved`, `rejected`, `flagged`                                                                                                              |
| `rejection_reason`  | `failed_gps_accuracy`, `fraud_detected`, `outside_geofence`, `failed_no_checkin`, `mock_location`, `gps_spoofing`, `unknown_device`, `face_mismatch`, `liveness_failed` |
| `export_format`     | `excel`, `pdf`                                                                                                                                            |
| `notification_type` | `checkin_approved`, `checkin_rejected`, `checkout_approved`, `checkout_rejected`, `device_trusted`, `exception_flagged`                                   |

---

## 2. Module 1: Authentication

### 2.1 Login

```http
POST /auth/login
```

**Authorization**: Public

**Description**: Authenticate with username and password. Returns JWT access token and refresh token. Works for all roles (employee, hr, manager, admin).

**Request body**:

```json
{
  "username": "employee01@example.com",
  "password": "password123"
}
```

| Field      | Type   | Required | Description              |
|------------|--------|----------|--------------------------|
| `username` | string | Yes      | Email used as username   |
| `password` | string | Yes      | Plain text password      |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "account": {
      "account_id": 1,
      "username": "employee01@example.com",
      "role": "employee",
      "last_login_at": "2026-05-20T08:00:00+07:00"
    },
    "employee": {
      "employee_id": 10,
      "full_name": "Nguyen Van A",
      "email": "employee01@example.com",
      "department_id": 2,
      "status": "active"
    }
  }
}
```

**Error handling**:

| Status | Code                  | Condition                                          |
|--------|-----------------------|----------------------------------------------------|
| `401`  | `INVALID_CREDENTIALS` | Username does not exist or password is wrong       |
| `401`  | `ACCOUNT_LOCKED`      | Account exists but `is_active = false`             |
| `422`  | `VALIDATION_ERROR`    | Missing `username` or `password`                   |

**Audit log**:

| Action  | Target    |
|---------|-----------|
| `login` | `ACCOUNT` |

---

### 2.2 Refresh Token

```http
POST /auth/refresh
```

**Authorization**: Public (refresh token in body)

**Description**: Issue a new access token using a valid refresh token. Allows clients to stay authenticated without re-entering credentials.

**Request body**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

| Field           | Type   | Required | Description              |
|-----------------|--------|----------|--------------------------|
| `refresh_token` | string | Yes      | Previously issued refresh token |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Error handling**:

| Status | Code                    | Condition                              |
|--------|-------------------------|----------------------------------------|
| `401`  | `INVALID_REFRESH_TOKEN` | Token is invalid, expired, or revoked  |
| `401`  | `ACCOUNT_LOCKED`        | Account was deactivated since issue    |

---

### 2.3 Current User

```http
GET /auth/me
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Return the authenticated user's account and linked employee profile.

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "account": {
      "account_id": 1,
      "username": "employee01@example.com",
      "role": "employee",
      "is_active": true
    },
    "employee": {
      "employee_id": 10,
      "department_id": 2,
      "full_name": "Nguyen Van A",
      "email": "employee01@example.com",
      "phone": "0900000000",
      "position": "Developer",
      "status": "active"
    }
  }
}
```

**Error handling**:

| Status | Code          | Condition                    |
|--------|---------------|------------------------------|
| `401`  | `UNAUTHORIZED`| Token missing or invalid     |

---

### 2.4 Logout

```http
POST /auth/logout
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Revoke the current access token and refresh token. The client should discard both tokens.

**Request body**: _(empty)_

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

**Audit log**:

| Action   | Target    |
|----------|-----------|
| `logout` | `ACCOUNT` |

---

### 2.5 Change Password

```http
PUT /auth/change-password
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Change the authenticated user's own password. Requires the current password to confirm identity.

**Request body**:

```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword@456",
  "confirm_password": "NewPassword@456"
}
```

| Field              | Type   | Required | Description                           |
|--------------------|--------|----------|---------------------------------------|
| `current_password` | string | Yes      | Current password for verification     |
| `new_password`     | string | Yes      | New password (min 8 chars, mixed case)|
| `confirm_password` | string | Yes      | Must match `new_password`             |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "message": "Password changed successfully"
  }
}
```

**Error handling**:

| Status | Code                      | Condition                                   |
|--------|---------------------------|---------------------------------------------|
| `400`  | `WRONG_CURRENT_PASSWORD`  | `current_password` is incorrect             |
| `400`  | `PASSWORD_MISMATCH`       | `new_password` and `confirm_password` differ|
| `400`  | `WEAK_PASSWORD`           | New password does not meet policy           |

**Audit log**:

| Action   | Target    |
|----------|-----------|
| `update` | `ACCOUNT` |

---

## 3. Module 2: Attendance

### 3.1 Check In

```http
POST /attendance/check-in
```

**Authorization**: `employee`

**Content type**: `multipart/form-data`

**Description**: Create an attendance check-in record. Validates device trust, GPS accuracy, 3D geofence (building, floor, altitude), face match, liveness detection, and fraud signals. A record is always written (approved or rejected) unless required identity data is missing.

**Form fields**:

| Field              | Type    | Required | Description                                            |
|--------------------|---------|----------|--------------------------------------------------------|
| `employee_id`      | integer | No       | Defaults to token employee; must match token if provided |
| `device_fingerprint`| string | Yes      | Unique mobile device fingerprint                       |
| `platform`         | string  | Yes      | `android`, `ios`, `web`, `other`                       |
| `model`            | string  | No       | Device model name                                      |
| `latitude`         | decimal | Yes      | GPS latitude, between -90 and 90                       |
| `longitude`        | decimal | Yes      | GPS longitude, between -180 and 180                    |
| `altitude`         | decimal | Yes      | GPS altitude in meters for floor/geofence matching     |
| `gps_accuracy`     | decimal | Yes      | Accuracy in meters (lower is better)                   |
| `captured_at`      | datetime| No       | Client-side capture timestamp                          |
| `is_mock_location` | boolean | No       | Mobile OS mock location flag (default: false)          |
| `liveness_signals` | string  | Yes      | JSON string of liveness challenge results              |
| `raw_signals`      | string  | No       | JSON string of raw device/sensor signals               |
| `face_image`       | file    | Yes      | Selfie image (JPEG or PNG, max 5 MB)                   |

`liveness_signals` JSON structure:

```json
{
  "blink_detected": true,
  "head_pose_changed": true,
  "challenge_passed": true
}
```

`raw_signals` JSON structure:

```json
{
  "provider": "gps",
  "speed_mps": 0.3,
  "bearing": 45.0
}
```

**Success response — Approved** `201 Created`:

```json
{
  "success": true,
  "data": {
    "record_id": 1001,
    "employee_id": 10,
    "type": "checkin",
    "status": "approved",
    "rejection_reason": null,
    "message": "Check-in approved",
    "timestamp": "2026-05-20T08:02:10+07:00",
    "is_late": false,
    "is_early_leave": false,
    "shift": {
      "shift_id": 3,
      "name": "Morning Shift",
      "start_time": "08:00:00",
      "end_time": "17:00:00"
    },
    "location": {
      "latitude": 10.772123,
      "longitude": 106.657890,
      "altitude": 12.5,
      "gps_accuracy": 5.2,
      "building_id": 1,
      "building_name": "Main Office",
      "floor_id": 2,
      "floor_name": "Floor 2",
      "geofence_rule_id": 7
    },
    "fraud_result": {
      "fraud_id": 501,
      "mock_location_detected": false,
      "gps_spoofing_detected": false,
      "buddy_punch_suspected": false,
      "unknown_device": false,
      "face_mismatch_detected": false,
      "liveness_failed": false,
      "confidence_score": 96.5
    }
  },
  "meta": {
    "response_time_ms": 1250
  }
}
```

**Success response — Rejected** `201 Created`:

```json
{
  "success": true,
  "data": {
    "record_id": 1002,
    "employee_id": 10,
    "type": "checkin",
    "status": "rejected",
    "rejection_reason": "outside_geofence",
    "message": "Check-in rejected: location is outside allowed geofence",
    "timestamp": "2026-05-20T08:05:00+07:00",
    "is_late": false,
    "is_early_leave": false,
    "location": {
      "latitude": 10.700000,
      "longitude": 106.600000,
      "altitude": 10.0,
      "gps_accuracy": 4.8,
      "building_id": null,
      "floor_id": null,
      "geofence_rule_id": null
    },
    "fraud_result": {
      "fraud_id": 502,
      "mock_location_detected": false,
      "gps_spoofing_detected": false,
      "buddy_punch_suspected": false,
      "unknown_device": false,
      "face_mismatch_detected": false,
      "liveness_failed": false,
      "confidence_score": 92.0
    }
  }
}
```

**Error handling** (request-level errors, no record written):

| Status | Code                  | Condition                                                 |
|--------|-----------------------|-----------------------------------------------------------|
| `400`  | `GPS_ACCURACY_TOO_LOW`| GPS accuracy exceeds the configured threshold             |
| `403`  | `EMPLOYEE_MISMATCH`   | Provided `employee_id` does not match the token employee  |
| `409`  | `ALREADY_CHECKED_IN`  | Employee already has an approved check-in without checkout|
| `422`  | `VALIDATION_ERROR`    | Missing GPS fields, face image, or device fingerprint     |

**Audit log**:

| Action    | Target              |
|-----------|---------------------|
| `checkin` | `ATTENDANCE_RECORD` |
| `reject`  | `ATTENDANCE_RECORD` |

---

### 3.2 Check Out

```http
POST /attendance/check-out
```

**Authorization**: `employee`

**Content type**: `multipart/form-data`

**Description**: Create an attendance check-out record. Finds the most recent approved check-in for today, validates the same conditions as check-in, then pairs them to compute `worked_minutes`.

**Form fields**: Same as `POST /attendance/check-in`.

**Success response — Approved** `201 Created`:

```json
{
  "success": true,
  "data": {
    "record_id": 1010,
    "employee_id": 10,
    "type": "checkout",
    "status": "approved",
    "rejection_reason": null,
    "message": "Check-out approved",
    "timestamp": "2026-05-20T17:01:30+07:00",
    "is_late": false,
    "is_early_leave": false,
    "matched_checkin_record_id": 1001,
    "worked_minutes": 539,
    "shift": {
      "shift_id": 3,
      "name": "Morning Shift",
      "start_time": "08:00:00",
      "end_time": "17:00:00"
    },
    "location": {
      "latitude": 10.772123,
      "longitude": 106.657890,
      "altitude": 12.4,
      "gps_accuracy": 5.0,
      "building_id": 1,
      "floor_id": 2,
      "geofence_rule_id": 7
    },
    "fraud_result": {
      "fraud_id": 510,
      "mock_location_detected": false,
      "gps_spoofing_detected": false,
      "buddy_punch_suspected": false,
      "unknown_device": false,
      "face_mismatch_detected": false,
      "liveness_failed": false,
      "confidence_score": 95.0
    }
  }
}
```

**Error handling**:

| Status | Code                  | Condition                                                      |
|--------|-----------------------|----------------------------------------------------------------|
| `409`  | `FAILED_NO_CHECKIN`   | No approved check-in exists for today or current shift         |
| `400`  | `GPS_ACCURACY_TOO_LOW`| GPS accuracy exceeds threshold                                 |
| `403`  | `EMPLOYEE_MISMATCH`   | Provided `employee_id` does not match token employee           |
| `422`  | `VALIDATION_ERROR`    | Missing GPS fields, face image, or device fingerprint          |

---

### 3.3 Today Attendance Status

```http
GET /attendance/today-status
```

**Authorization**: `employee`

**Description**: Return the current employee's check-in / check-out state for today. Used by the mobile home screen to decide which action buttons to display.

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "date": "2026-05-20",
    "employee_id": 10,
    "can_check_in": false,
    "can_check_out": true,
    "current_shift": {
      "shift_id": 3,
      "name": "Morning Shift",
      "start_time": "08:00:00",
      "end_time": "17:00:00"
    },
    "latest_checkin": {
      "record_id": 1001,
      "timestamp": "2026-05-20T08:02:10+07:00",
      "status": "approved"
    },
    "latest_checkout": null
  }
}
```

---

### 3.4 Attendance History

```http
GET /attendance/history
```

**Authorization**: `employee`, `hr`, `admin`

**Description**: Return a paginated attendance history with per-day detail and aggregated summary. Employees can only view their own history. HR and Admin can view any employee.

**Query parameters**:

| Parameter     | Type    | Required | Description                                                        |
|---------------|---------|----------|--------------------------------------------------------------------|
| `employee_id` | integer | No       | Target employee; for `employee` role defaults to and locked to self|
| `from`        | date    | Yes      | Start date inclusive                                               |
| `to`          | date    | Yes      | End date inclusive                                                 |
| `page`        | integer | No       | Page number (default 1)                                            |
| `limit`       | integer | No       | Items per page (default 20)                                        |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee": {
      "employee_id": 10,
      "full_name": "Nguyen Van A"
    },
    "range": {
      "from": "2026-05-01",
      "to": "2026-05-20"
    },
    "summary": {
      "work_days": 14,
      "total_work_minutes": 6720,
      "late_count": 1,
      "early_leave_count": 0,
      "rejected_count": 2
    },
    "days": [
      {
        "date": "2026-05-20",
        "checkin": {
          "record_id": 1001,
          "timestamp": "2026-05-20T08:02:10+07:00",
          "status": "approved",
          "is_late": false
        },
        "checkout": {
          "record_id": 1010,
          "timestamp": "2026-05-20T17:01:30+07:00",
          "status": "approved",
          "is_early_leave": false
        },
        "building_name": "Main Office",
        "floor_name": "Floor 2",
        "worked_minutes": 539,
        "status": "completed"
      }
    ]
  },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 14,
    "total_pages": 1
  }
}
```

**Error handling**:

| Status | Code               | Condition                                            |
|--------|--------------------|------------------------------------------------------|
| `403`  | `FORBIDDEN`        | Employee tries to view another employee's history    |
| `404`  | `EMPLOYEE_NOT_FOUND`| Requested `employee_id` does not exist              |
| `422`  | `VALIDATION_ERROR` | `from` or `to` missing or invalid date format        |

---

### 3.5 Attendance Exceptions

```http
GET /attendance/exceptions
```

**Authorization**: `hr`, `admin`

**Description**: List abnormal attendance records: rejected, flagged, late, or early-leave. Used by HR to review violations and decide on manual overrides.

**Query parameters**:

| Parameter       | Type    | Required | Description                                                         |
|-----------------|---------|----------|---------------------------------------------------------------------|
| `from`          | date    | No       | Start date                                                          |
| `to`            | date    | No       | End date                                                            |
| `status`        | string  | No       | `rejected`, `flagged`, `approved`                                   |
| `department_id` | integer | No       | Filter by department                                                |
| `employee_id`   | integer | No       | Filter by employee                                                  |
| `reason`        | string  | No       | Filter by rejection reason enum                                     |
| `page`          | integer | No       | Page number                                                         |
| `limit`         | integer | No       | Items per page                                                      |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "record_id": 1002,
      "employee": {
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering"
      },
      "type": "checkin",
      "timestamp": "2026-05-20T08:05:00+07:00",
      "status": "rejected",
      "rejection_reason": "outside_geofence",
      "is_late": false,
      "is_early_leave": false,
      "fraud_flags": {
        "mock_location_detected": false,
        "gps_spoofing_detected": false,
        "buddy_punch_suspected": false,
        "unknown_device": false,
        "face_mismatch_detected": false,
        "liveness_failed": false
      }
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 3.6 Attendance Record Detail

```http
GET /attendance/{record_id}
```

**Authorization**: `hr`, `admin`

**Description**: Return the full detail of a single attendance record including device info, shift, location, and fraud detection results.

**Path parameters**:

| Parameter   | Type    | Description             |
|-------------|---------|-------------------------|
| `record_id` | integer | Attendance record ID    |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "record_id": 1002,
    "employee": {
      "employee_id": 10,
      "full_name": "Nguyen Van A",
      "department_id": 2,
      "department_name": "Engineering"
    },
    "device": {
      "device_id": 12,
      "device_fingerprint": "abc-device-fingerprint",
      "platform": "android",
      "model": "Pixel 8",
      "is_trusted": true
    },
    "shift": {
      "shift_id": 3,
      "name": "Morning Shift",
      "start_time": "08:00:00",
      "end_time": "17:00:00"
    },
    "geofence_rule_id": null,
    "type": "checkin",
    "timestamp": "2026-05-20T08:05:00+07:00",
    "latitude": 10.700000,
    "longitude": 106.600000,
    "altitude": 10.0,
    "gps_accuracy": 4.8,
    "status": "rejected",
    "rejection_reason": "outside_geofence",
    "is_late": false,
    "is_early_leave": false,
    "fraud_detection": {
      "fraud_id": 502,
      "mock_location_detected": false,
      "gps_spoofing_detected": false,
      "buddy_punch_suspected": false,
      "unknown_device": false,
      "face_mismatch_detected": false,
      "liveness_failed": false,
      "reason": null,
      "confidence_score": 92.0,
      "checked_at": "2026-05-20T08:05:01+07:00"
    }
  }
}
```

**Error handling**:

| Status | Code             | Condition                      |
|--------|------------------|--------------------------------|
| `404`  | `RECORD_NOT_FOUND` | Record ID does not exist      |

---

### 3.7 Manually Approve Attendance Record

```http
PUT /attendance/{record_id}/approve
```

**Authorization**: `hr`, `admin`

**Description**: Override a rejected or flagged attendance record and set it to approved. Typically used after HR verifies the situation through other means.

**Path parameters**:

| Parameter   | Type    | Description             |
|-------------|---------|-------------------------|
| `record_id` | integer | Attendance record ID    |

**Request body**:

```json
{
  "note": "Approved after HR verified employee was physically present."
}
```

| Field  | Type   | Required | Description                         |
|--------|--------|----------|-------------------------------------|
| `note` | string | No       | Reason for manual approval          |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "record_id": 1002,
    "status": "approved",
    "rejection_reason": null,
    "approved_by_account_id": 2,
    "approved_at": "2026-05-20T09:00:00+07:00"
  }
}
```

**Error handling**:

| Status | Code                  | Condition                                          |
|--------|-----------------------|----------------------------------------------------|
| `404`  | `RECORD_NOT_FOUND`    | Record ID does not exist                           |
| `409`  | `ALREADY_APPROVED`    | Record is already in `approved` status             |

**Audit log**:

| Action    | Target              |
|-----------|---------------------|
| `approve` | `ATTENDANCE_RECORD` |

---

## 4. Module 3: Geofence

### 4.1 List Buildings

```http
GET /buildings
```

**Authorization**: `hr`, `admin`

**Description**: Return all registered buildings with optional floor list. Used for the 3D map configuration and geofence setup.

**Query parameters**:

| Parameter        | Type    | Required | Description                              |
|------------------|---------|----------|------------------------------------------|
| `include_floors` | boolean | No       | If `true`, include floors in each building|
| `q`              | string  | No       | Search by building name or address       |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "building_id": 1,
      "name": "Main Office",
      "address": "Linh Trung, Thu Duc, Ho Chi Minh City",
      "center_lat": 10.772123,
      "center_lng": 106.657890,
      "total_floors": 5,
      "arcgis_layer_id": "arcgis-layer-001",
      "floors": [
        {
          "floor_id": 2,
          "floor_number": 2,
          "floor_name": "Floor 2",
          "altitude_min": 10.0,
          "altitude_max": 15.0
        }
      ]
    }
  ]
}
```

---

### 4.2 Create Building

```http
POST /buildings
```

**Authorization**: `admin`

**Description**: Register a new building with its geographic center and ArcGIS layer reference for 3D map rendering.

**Request body**:

```json
{
  "name": "Main Office",
  "address": "Linh Trung, Thu Duc, Ho Chi Minh City",
  "center_lat": 10.772123,
  "center_lng": 106.657890,
  "total_floors": 5,
  "arcgis_layer_id": "arcgis-layer-001"
}
```

| Field           | Type    | Required | Description                            |
|-----------------|---------|----------|----------------------------------------|
| `name`          | string  | Yes      | Building name (must be unique)         |
| `address`       | string  | Yes      | Physical address                       |
| `center_lat`    | decimal | Yes      | Geographic center latitude             |
| `center_lng`    | decimal | Yes      | Geographic center longitude            |
| `total_floors`  | integer | Yes      | Number of floors                       |
| `arcgis_layer_id`| string | Yes      | ArcGIS layer ID for 3D rendering       |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "building_id": 1,
    "name": "Main Office",
    "arcgis_layer_valid": true
  }
}
```

**Error handling**:

| Status | Code                    | Condition                              |
|--------|-------------------------|----------------------------------------|
| `400`  | `INVALID_ARCGIS_LAYER`  | ArcGIS layer ID could not be validated |
| `409`  | `BUILDING_NAME_EXISTS`  | Building name already exists           |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `create` | `BUILDING` |

---

### 4.3 Update Building

```http
PUT /buildings/{building_id}
```

**Authorization**: `admin`

**Description**: Update building metadata. ArcGIS layer will be re-validated on update.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `building_id` | integer | Building ID   |

**Request body**:

```json
{
  "name": "Main Office",
  "address": "Updated address",
  "center_lat": 10.772123,
  "center_lng": 106.657890,
  "total_floors": 5,
  "arcgis_layer_id": "arcgis-layer-001"
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "building_id": 1,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                   | Condition                              |
|--------|------------------------|----------------------------------------|
| `404`  | `BUILDING_NOT_FOUND`   | Building ID does not exist             |
| `400`  | `INVALID_ARCGIS_LAYER` | ArcGIS layer ID could not be validated |

---

### 4.4 List Building Floors

```http
GET /buildings/{building_id}/floors
```

**Authorization**: `hr`, `admin`

**Description**: Return all floors for a specific building with their altitude ranges for 3D geofence configuration.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `building_id` | integer | Building ID   |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "floor_id": 2,
      "building_id": 1,
      "floor_number": 2,
      "floor_name": "Floor 2",
      "altitude_min": 10.0,
      "altitude_max": 15.0
    }
  ]
}
```

**Error handling**:

| Status | Code                 | Condition                  |
|--------|----------------------|----------------------------|
| `404`  | `BUILDING_NOT_FOUND` | Building ID does not exist |

---

### 4.5 Create Floor

```http
POST /buildings/{building_id}/floors
```

**Authorization**: `admin`

**Description**: Add a floor to a building with altitude range used for 3D geofence matching.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `building_id` | integer | Building ID   |

**Request body**:

```json
{
  "floor_number": 2,
  "floor_name": "Floor 2",
  "altitude_min": 10.0,
  "altitude_max": 15.0
}
```

| Field          | Type    | Required | Description                                  |
|----------------|---------|----------|----------------------------------------------|
| `floor_number` | integer | Yes      | Floor number (must be unique per building)   |
| `floor_name`   | string  | Yes      | Display name                                 |
| `altitude_min` | decimal | Yes      | Minimum GPS altitude for this floor (meters) |
| `altitude_max` | decimal | Yes      | Maximum GPS altitude for this floor (meters) |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "floor_id": 2,
    "building_id": 1,
    "floor_name": "Floor 2"
  }
}
```

**Error handling**:

| Status | Code                      | Condition                                         |
|--------|---------------------------|---------------------------------------------------|
| `404`  | `BUILDING_NOT_FOUND`      | Building ID does not exist                        |
| `400`  | `INVALID_ALTITUDE_RANGE`  | `altitude_min >= altitude_max`                    |
| `409`  | `FLOOR_NUMBER_EXISTS`     | Floor number already used in this building        |

**Audit log**:

| Action   | Target  |
|----------|---------|
| `create` | `FLOOR` |

---

### 4.6 Update Floor

```http
PUT /floors/{floor_id}
```

**Authorization**: `admin`

**Description**: Update a floor's altitude range or display name. Affects all active geofences on this floor.

**Path parameters**:

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `floor_id` | integer | Floor ID    |

**Request body**:

```json
{
  "floor_number": 2,
  "floor_name": "Floor 2",
  "altitude_min": 10.0,
  "altitude_max": 15.0
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "floor_id": 2,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                     | Condition                      |
|--------|--------------------------|--------------------------------|
| `404`  | `FLOOR_NOT_FOUND`        | Floor ID does not exist        |
| `400`  | `INVALID_ALTITUDE_RANGE` | `altitude_min >= altitude_max` |

---

### 4.7 List Geofences

```http
GET /geofences
```

**Authorization**: `hr`, `admin`

**Description**: Return all geofence rules with filtering. Used for the geofence management UI.

**Query parameters**:

| Parameter     | Type    | Required | Description              |
|---------------|---------|----------|--------------------------|
| `building_id` | integer | No       | Filter by building       |
| `floor_id`    | integer | No       | Filter by floor          |
| `is_active`   | boolean | No       | Filter by active status  |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "geofence_id": 7,
      "geofence_rule_id": 7,
      "name": "Floor 2 Working Area",
      "building_id": 1,
      "building_name": "Main Office",
      "floor_id": 2,
      "floor_name": "Floor 2",
      "center_lat": 10.772123,
      "center_lng": 106.657890,
      "radius_meters": 50.0,
      "altitude_min": 10.0,
      "altitude_max": 15.0,
      "allow_checkin": true,
      "allow_checkout": true,
      "is_active": true,
      "created_by_account_id": 2
    }
  ]
}
```

---

### 4.8 Create Geofence

```http
POST /geofences
```

**Authorization**: `hr`, `admin`

**Description**: Define a new geofence rule on a specific floor. The radius is validated for overlaps with existing active geofences on the same floor.

**Request body**:

```json
{
  "floor_id": 2,
  "name": "Floor 2 Working Area",
  "center_lat": 10.772123,
  "center_lng": 106.657890,
  "radius_meters": 50.0,
  "altitude_min": 10.0,
  "altitude_max": 15.0,
  "allow_checkin": true,
  "allow_checkout": true
}
```

| Field           | Type    | Required | Description                                           |
|-----------------|---------|----------|-------------------------------------------------------|
| `floor_id`      | integer | Yes      | Floor this geofence belongs to                        |
| `name`          | string  | Yes      | Geofence display name                                 |
| `center_lat`    | decimal | Yes      | Center latitude of the geofence circle                |
| `center_lng`    | decimal | Yes      | Center longitude of the geofence circle               |
| `radius_meters` | decimal | Yes      | Radius of the geofence circle in meters               |
| `altitude_min`  | decimal | Yes      | Minimum altitude for acceptance (inherits from floor) |
| `altitude_max`  | decimal | Yes      | Maximum altitude for acceptance (inherits from floor) |
| `allow_checkin` | boolean | Yes      | Whether check-in is allowed in this zone              |
| `allow_checkout`| boolean | Yes      | Whether check-out is allowed in this zone             |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "geofence_id": 7,
    "geofence_rule_id": 7,
    "is_active": true
  }
}
```

**Error handling**:

| Status | Code                     | Condition                                              |
|--------|--------------------------|--------------------------------------------------------|
| `404`  | `FLOOR_NOT_FOUND`        | Floor ID does not exist                                |
| `409`  | `GEOFENCE_OVERLAP`       | New geofence overlaps an active geofence on same floor |
| `400`  | `INVALID_ALTITUDE_RANGE` | `altitude_min >= altitude_max`                         |

**Audit log**:

| Action   | Target          |
|----------|-----------------|
| `create` | `GEOFENCE_RULE` |

---

### 4.9 Update Geofence

```http
PUT /geofences/{geofence_id}
```

**Authorization**: `hr`, `admin`

**Description**: Update a geofence's coordinates, radius, or rules. Overlap check is re-run on update excluding the geofence being updated.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `geofence_id` | integer | Geofence ID   |

**Request body**:

```json
{
  "name": "Floor 2 Working Area",
  "center_lat": 10.772123,
  "center_lng": 106.657890,
  "radius_meters": 55.0,
  "altitude_min": 10.0,
  "altitude_max": 15.0,
  "allow_checkin": true,
  "allow_checkout": true,
  "is_active": true
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "geofence_id": 7,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                     | Condition                                |
|--------|--------------------------|------------------------------------------|
| `404`  | `GEOFENCE_NOT_FOUND`     | Geofence ID does not exist               |
| `409`  | `GEOFENCE_OVERLAP`       | Updated geofence overlaps another one    |
| `400`  | `INVALID_ALTITUDE_RANGE` | `altitude_min >= altitude_max`           |

---

### 4.10 Disable Geofence

```http
DELETE /geofences/{geofence_id}
```

**Authorization**: `hr`, `admin`

**Description**: Soft-delete a geofence by setting `is_active = false`. The record is kept for historical reference. Existing attendance records linked to this geofence are not affected.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `geofence_id` | integer | Geofence ID   |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "geofence_id": 7,
    "is_active": false
  }
}
```

**Error handling**:

| Status | Code                  | Condition                                  |
|--------|-----------------------|--------------------------------------------|
| `404`  | `GEOFENCE_NOT_FOUND`  | Geofence ID does not exist                 |
| `409`  | `ALREADY_DISABLED`    | Geofence is already inactive               |

**Audit log**:

| Action   | Target          |
|----------|-----------------|
| `delete` | `GEOFENCE_RULE` |

---

## 5. Module 4: Fraud Detection

### 5.1 Evaluate Fraud (Internal)

```http
POST /internal/fraud/evaluate
```

**Authorization**: Internal service only (no public JWT)

**Description**: Analyze a set of attendance signals and return a fraud verdict with a confidence score. Called internally by the attendance service during check-in / check-out processing. Not exposed publicly.

**Request body**:

```json
{
  "employee_id": 10,
  "device_fingerprint": "abc-device-fingerprint",
  "latitude": 10.772123,
  "longitude": 106.657890,
  "altitude": 12.5,
  "gps_accuracy": 5.2,
  "timestamp": "2026-05-20T08:02:10+07:00",
  "is_mock_location": false,
  "face_image_object_key": "selfies/2026/05/20/1001.jpg",
  "liveness_signals": {
    "blink_detected": true,
    "head_pose_changed": true,
    "challenge_passed": true
  },
  "raw_signals": {
    "provider": "gps",
    "speed_mps": 0.5
  }
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "mock_location_detected": false,
    "gps_spoofing_detected": false,
    "buddy_punch_suspected": false,
    "unknown_device": false,
    "face_mismatch_detected": false,
    "liveness_failed": false,
    "confidence_score": 96.5,
    "reason": null,
    "flags": []
  }
}
```

**Fraud flags description**:

| Flag                     | Detection method                                           |
|--------------------------|------------------------------------------------------------|
| `mock_location_detected` | Mobile OS mock location flag is true                       |
| `gps_spoofing_detected`  | Speed/accuracy anomaly, signal jitter analysis             |
| `buddy_punch_suspected`  | Device previously used by another employee in same window  |
| `unknown_device`         | Device fingerprint not registered or not trusted           |
| `face_mismatch_detected` | Selfie does not match stored face reference                |
| `liveness_failed`        | Liveness challenge not passed                              |

---

### 5.2 List Fraud Records

```http
GET /fraud/records
```

**Authorization**: `hr`, `admin`

**Description**: Return a paginated list of fraud detection results linked to attendance records. Used to review fraud patterns and investigate suspicious check-ins.

**Query parameters**:

| Parameter              | Type    | Required | Description                                |
|------------------------|---------|----------|--------------------------------------------|
| `employee_id`          | integer | No       | Filter by employee                         |
| `from`                 | date    | No       | Start date                                 |
| `to`                   | date    | No       | End date                                   |
| `mock_location`        | boolean | No       | Filter records with mock location detected |
| `gps_spoofing`         | boolean | No       | Filter records with GPS spoofing detected  |
| `buddy_punch`          | boolean | No       | Filter records with buddy punch suspected  |
| `unknown_device`       | boolean | No       | Filter records with unknown device         |
| `face_mismatch`        | boolean | No       | Filter records with face mismatch          |
| `min_confidence_score` | decimal | No       | Minimum confidence score (0–100)           |
| `max_confidence_score` | decimal | No       | Maximum confidence score (0–100)           |
| `page`                 | integer | No       | Page number                                |
| `limit`                | integer | No       | Items per page                             |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "fraud_id": 502,
      "record_id": 1002,
      "employee": {
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering"
      },
      "attendance_type": "checkin",
      "attendance_timestamp": "2026-05-20T08:05:00+07:00",
      "mock_location_detected": true,
      "gps_spoofing_detected": false,
      "buddy_punch_suspected": false,
      "unknown_device": false,
      "face_mismatch_detected": false,
      "liveness_failed": false,
      "confidence_score": 32.0,
      "reason": "mock_location",
      "checked_at": "2026-05-20T08:05:01+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 5.3 Fraud Record Detail

```http
GET /fraud/records/{fraud_id}
```

**Authorization**: `hr`, `admin`

**Description**: Return the full fraud detection result for a single attendance record.

**Path parameters**:

| Parameter  | Type    | Description      |
|------------|---------|------------------|
| `fraud_id` | integer | Fraud record ID  |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "fraud_id": 502,
    "record_id": 1002,
    "employee": {
      "employee_id": 10,
      "full_name": "Nguyen Van A",
      "department_name": "Engineering"
    },
    "attendance": {
      "type": "checkin",
      "timestamp": "2026-05-20T08:05:00+07:00",
      "status": "rejected",
      "rejection_reason": "mock_location",
      "latitude": 10.700000,
      "longitude": 106.600000,
      "altitude": 10.0,
      "gps_accuracy": 4.8
    },
    "device": {
      "device_id": 12,
      "device_fingerprint": "abc-device-fingerprint",
      "platform": "android",
      "model": "Pixel 8",
      "is_trusted": true
    },
    "mock_location_detected": true,
    "gps_spoofing_detected": false,
    "buddy_punch_suspected": false,
    "unknown_device": false,
    "face_mismatch_detected": false,
    "liveness_failed": false,
    "confidence_score": 32.0,
    "reason": "mock_location",
    "checked_at": "2026-05-20T08:05:01+07:00"
  }
}
```

**Error handling**:

| Status | Code                | Condition                    |
|--------|---------------------|------------------------------|
| `404`  | `FRAUD_NOT_FOUND`   | Fraud record ID does not exist|

---

## 6. Module 5: Face Verification

### 6.1 Register Employee Face

```http
POST /employees/{employee_id}/face
```

**Authorization**: `hr`, `admin`

**Content type**: `multipart/form-data`

**Description**: Upload and store a reference face image for an employee. This image is used for future face matching during check-in / check-out. Replaces any existing face reference.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Form fields**:

| Field        | Type | Required | Description                                     |
|--------------|------|----------|-------------------------------------------------|
| `face_image` | file | Yes      | Clear frontal face image (JPEG or PNG, max 5 MB)|

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "face_registered": true,
    "face_object_key": "faces/employee_10/reference_2026-05-20.jpg",
    "registered_at": "2026-05-20T09:00:00+07:00"
  }
}
```

**Error handling**:

| Status | Code                    | Condition                                       |
|--------|-------------------------|-------------------------------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND`    | Employee ID does not exist                      |
| `400`  | `NO_FACE_DETECTED`      | No face was detected in the uploaded image      |
| `400`  | `MULTIPLE_FACES`        | More than one face detected in the image        |
| `400`  | `IMAGE_TOO_SMALL`       | Image resolution is too low for reliable match  |
| `422`  | `VALIDATION_ERROR`      | Missing `face_image`                            |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `update` | `EMPLOYEE` |

---

### 6.2 Get Employee Face Status

```http
GET /employees/{employee_id}/face
```

**Authorization**: `hr`, `admin`

**Description**: Return the current face registration status and metadata for an employee. Does not return the image.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "face_registered": true,
    "face_object_key": "faces/employee_10/reference_2026-05-20.jpg",
    "registered_at": "2026-05-20T09:00:00+07:00"
  }
}
```

If no face registered:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "face_registered": false,
    "face_object_key": null,
    "registered_at": null
  }
}
```

**Error handling**:

| Status | Code                 | Condition                   |
|--------|----------------------|-----------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND` | Employee ID does not exist  |

---

### 6.3 Delete Employee Face Reference

```http
DELETE /employees/{employee_id}/face
```

**Authorization**: `admin`

**Description**: Remove the stored face reference for an employee. The employee will not be able to check in until a new face is registered.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "face_removed": true
  }
}
```

**Error handling**:

| Status | Code                   | Condition                         |
|--------|------------------------|-----------------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND`   | Employee ID does not exist        |
| `404`  | `FACE_NOT_REGISTERED`  | Employee has no face on record    |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `update` | `EMPLOYEE` |

---

### 6.4 Verify Face (Internal)

```http
POST /internal/face/verify
```

**Authorization**: Internal service only

**Content type**: `multipart/form-data`

**Description**: Compare a submitted selfie against the stored reference face for an employee and run liveness detection. Called internally by the attendance service.

**Form fields**:

| Field             | Type    | Required | Description                         |
|-------------------|---------|----------|-------------------------------------|
| `employee_id`     | integer | Yes      | Employee whose reference to match   |
| `face_image`      | file    | Yes      | Selfie captured at attendance time  |
| `liveness_signals`| string  | Yes      | JSON string of liveness challenge inputs|

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "face_match_score": 0.94,
    "liveness_score": 0.91,
    "face_matched": true,
    "liveness_passed": true
  }
}
```

---

## 7. Module 6: Notification

### 7.1 List My Notifications

```http
GET /notifications
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Return notifications for the currently authenticated user. Supports filtering by read status. Notifications are generated by system events such as check-in approval, rejection, or device trust updates.

**Query parameters**:

| Parameter | Type    | Required | Description                          |
|-----------|---------|----------|--------------------------------------|
| `is_read` | boolean | No       | Filter by read status                |
| `type`    | string  | No       | Filter by `notification_type` enum   |
| `page`    | integer | No       | Page number                          |
| `limit`   | integer | No       | Items per page                       |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "notification_id": 301,
      "type": "checkin_approved",
      "title": "Check-in Approved",
      "body": "Your check-in at Main Office, Floor 2 was approved at 08:02.",
      "is_read": false,
      "created_at": "2026-05-20T08:02:15+07:00",
      "meta": {
        "record_id": 1001,
        "building_name": "Main Office",
        "floor_name": "Floor 2"
      }
    },
    {
      "notification_id": 302,
      "type": "checkin_rejected",
      "title": "Check-in Rejected",
      "body": "Your check-in was rejected: location is outside allowed geofence.",
      "is_read": true,
      "created_at": "2026-05-20T08:05:05+07:00",
      "meta": {
        "record_id": 1002,
        "rejection_reason": "outside_geofence"
      }
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1,
    "unread_count": 1
  }
}
```

---

### 7.2 Mark Notification as Read

```http
PUT /notifications/{notification_id}/read
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Mark a single notification as read. Only the owner of the notification can mark it.

**Path parameters**:

| Parameter         | Type    | Description         |
|-------------------|---------|---------------------|
| `notification_id` | integer | Notification ID     |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "notification_id": 301,
    "is_read": true
  }
}
```

**Error handling**:

| Status | Code                       | Condition                                      |
|--------|----------------------------|------------------------------------------------|
| `404`  | `NOTIFICATION_NOT_FOUND`   | Notification ID does not exist                 |
| `403`  | `FORBIDDEN`                | Notification belongs to a different account    |

---

### 7.3 Mark All Notifications as Read

```http
PUT /notifications/read-all
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Mark all unread notifications for the authenticated user as read.

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "marked_count": 5
  }
}
```

---

### 7.4 Get Notification Preferences

```http
GET /notifications/preferences
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Return the authenticated user's notification preference settings (push, in-app, or both).

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "account_id": 1,
    "push_enabled": true,
    "in_app_enabled": true,
    "notify_checkin_approved": true,
    "notify_checkin_rejected": true,
    "notify_checkout_approved": true,
    "notify_checkout_rejected": true,
    "notify_device_trusted": true,
    "notify_exception_flagged": true
  }
}
```

---

### 7.5 Update Notification Preferences

```http
PUT /notifications/preferences
```

**Authorization**: `employee`, `hr`, `manager`, `admin`

**Description**: Update push and in-app notification preferences for the authenticated user.

**Request body**:

```json
{
  "push_enabled": true,
  "in_app_enabled": true,
  "notify_checkin_approved": true,
  "notify_checkin_rejected": true,
  "notify_checkout_approved": false,
  "notify_checkout_rejected": true,
  "notify_device_trusted": true,
  "notify_exception_flagged": false
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "updated": true
  }
}
```

---

### 7.6 Send Notification (Internal)

```http
POST /internal/notifications/send
```

**Authorization**: Internal service only

**Description**: Dispatch a notification to one or more accounts. Called internally by the attendance service after record creation.

**Request body**:

```json
{
  "account_ids": [1],
  "type": "checkin_approved",
  "title": "Check-in Approved",
  "body": "Your check-in at Main Office, Floor 2 was approved.",
  "meta": {
    "record_id": 1001
  }
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "sent_count": 1,
    "failed_count": 0
  }
}
```

---

## 8. Module 7: Report

### 8.1 Dashboard Summary

```http
GET /dashboard/summary
```

**Authorization**: `manager`, `hr`, `admin`

**Description**: Return KPI summary for the dashboard. Includes attendance counts, fraud alert count, and active employee locations. Designed for 60-second polling. `manager` role is read-only.

**Query parameters**:

| Parameter | Type | Required | Description                     |
|-----------|------|----------|---------------------------------|
| `date`    | date | No       | Target date, defaults to today  |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "date": "2026-05-20",
    "total_employees": 120,
    "checked_in_today": 96,
    "on_time_count": 88,
    "late_count": 8,
    "early_leave_count": 2,
    "absent_count": 24,
    "fraud_alerts_today": 3,
    "on_time_rate": 91.67,
    "active_locations": [
      {
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering",
        "latitude": 10.772123,
        "longitude": 106.657890,
        "altitude": 12.5,
        "building_id": 1,
        "building_name": "Main Office",
        "floor_id": 2,
        "floor_name": "Floor 2",
        "last_checkin_at": "2026-05-20T08:02:10+07:00"
      }
    ]
  },
  "meta": {
    "refresh_interval_seconds": 60
  }
}
```

---

### 8.2 Realtime Employee Locations

```http
GET /realtime/employees-location
```

**Authorization**: `hr`, `admin`

**Description**: Return employees with an approved check-in today who have not yet checked out. Used for the real-time 3D map display. Designed for 30-second polling.

**Query parameters**:

| Parameter       | Type    | Required | Description              |
|-----------------|---------|----------|--------------------------|
| `building_id`   | integer | No       | Filter by building       |
| `floor_id`      | integer | No       | Filter by floor          |
| `department_id` | integer | No       | Filter by department     |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "employee_id": 10,
      "full_name": "Nguyen Van A",
      "department_id": 2,
      "department_name": "Engineering",
      "record_id": 1001,
      "latitude": 10.772123,
      "longitude": 106.657890,
      "altitude": 12.5,
      "gps_accuracy": 5.2,
      "building_id": 1,
      "building_name": "Main Office",
      "floor_id": 2,
      "floor_name": "Floor 2",
      "arcgis_layer_id": "arcgis-layer-001",
      "checked_in_at": "2026-05-20T08:02:10+07:00"
    }
  ],
  "meta": {
    "refresh_interval_seconds": 30
  }
}
```

---

### 8.3 Attendance Report

```http
GET /reports/attendance
```

**Authorization**: `manager`, `hr`, `admin`

**Description**: Return a full attendance report for a date range with per-employee summary and day-level detail. `manager` role is read-only and cannot export.

**Query parameters**:

| Parameter       | Type    | Required | Description               |
|-----------------|---------|----------|---------------------------|
| `from`          | date    | Yes      | Start date inclusive      |
| `to`            | date    | Yes      | End date inclusive        |
| `department_id` | integer | No       | Department filter         |
| `employee_id`   | integer | No       | Employee filter           |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "range": {
      "from": "2026-05-01",
      "to": "2026-05-20"
    },
    "summary": {
      "employee_count": 120,
      "total_work_days": 1680,
      "total_work_minutes": 806400,
      "late_count": 35,
      "early_leave_count": 12,
      "absent_count": 90,
      "rejected_count": 18
    },
    "employees": [
      {
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering",
        "work_days": 14,
        "total_work_minutes": 6720,
        "late_count": 1,
        "early_leave_count": 0,
        "absent_count": 0,
        "rejected_count": 2
      }
    ],
    "details": [
      {
        "date": "2026-05-20",
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering",
        "checkin_at": "2026-05-20T08:02:10+07:00",
        "checkout_at": "2026-05-20T17:01:30+07:00",
        "worked_minutes": 539,
        "is_late": false,
        "is_early_leave": false,
        "status": "completed"
      }
    ]
  }
}
```

**Error handling**:

| Status | Code               | Condition                            |
|--------|--------------------|--------------------------------------|
| `422`  | `VALIDATION_ERROR` | `from` or `to` missing or invalid    |

---

### 8.4 Export Attendance Report

```http
GET /reports/attendance/export
```

**Authorization**: `hr`, `admin`

**Description**: Export the attendance report as an Excel or PDF file. The response is a binary file download. `manager` role is not allowed to export.

**Query parameters**:

| Parameter       | Type    | Required | Description                                |
|-----------------|---------|----------|--------------------------------------------|
| `format`        | string  | Yes      | `excel` or `pdf`                           |
| `from`          | date    | Yes      | Start date inclusive                       |
| `to`            | date    | Yes      | End date inclusive                         |
| `department_id` | integer | No       | Department filter                          |
| `employee_id`   | integer | No       | Employee filter                            |

**Success response** `200 OK`:

Binary file with appropriate headers:

| Format  | Content-Type                                                                | Filename example                               |
|---------|-----------------------------------------------------------------------------|------------------------------------------------|
| `excel` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`         | `attendance_report_2026-05-01_2026-05-20.xlsx` |
| `pdf`   | `application/pdf`                                                           | `attendance_report_2026-05-01_2026-05-20.pdf`  |

**Error handling**:

| Status | Code                   | Condition                                  |
|--------|------------------------|--------------------------------------------|
| `400`  | `INVALID_EXPORT_FORMAT`| Format is not `excel` or `pdf`             |
| `404`  | `NO_REPORT_DATA`       | No attendance data found for the filters   |
| `422`  | `VALIDATION_ERROR`     | `from`, `to`, or `format` missing          |

---

## 9. Module 8: Audit Log

### 9.1 Search Audit Logs

```http
GET /audit-logs
```

**Authorization**: `admin`

**Description**: Return a paginated, filterable list of system audit logs. Audit logs are immutable — no update or delete is available through the API.

**Query parameters**:

| Parameter     | Type     | Required | Description                                                                                              |
|---------------|----------|----------|----------------------------------------------------------------------------------------------------------|
| `actor`       | integer  | No       | Filter by account ID of the actor                                                                        |
| `action_type` | string   | No       | `login`, `logout`, `create`, `update`, `delete`, `checkin`, `checkout`, `approve`, `reject`              |
| `from`        | datetime | No       | Start datetime (ISO 8601)                                                                                |
| `to`          | datetime | No       | End datetime (ISO 8601)                                                                                  |
| `entity`      | string   | No       | Target entity: `ACCOUNT`, `EMPLOYEE`, `ATTENDANCE_RECORD`, `DEVICE`, `SHIFT`, `BUILDING`, `FLOOR`, `GEOFENCE_RULE` |
| `page`        | integer  | No       | Page number                                                                                              |
| `limit`       | integer  | No       | Items per page (max 100)                                                                                 |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "log_id": 9001,
      "account": {
        "account_id": 2,
        "username": "admin@example.com",
        "role": "admin"
      },
      "action_type": "create",
      "target_entity": "GEOFENCE_RULE",
      "target_id": 7,
      "ip_address": "192.168.1.10",
      "created_at": "2026-05-20T09:00:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 100,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 9.2 Audit Log Detail

```http
GET /audit-logs/{log_id}
```

**Authorization**: `admin`

**Description**: Return the full detail of a single audit log entry including the before/after payload snapshot of the affected entity.

**Path parameters**:

| Parameter | Type    | Description     |
|-----------|---------|-----------------|
| `log_id`  | integer | Audit log ID    |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "log_id": 9001,
    "account": {
      "account_id": 2,
      "username": "admin@example.com",
      "role": "admin"
    },
    "action_type": "create",
    "target_entity": "GEOFENCE_RULE",
    "target_id": 7,
    "payload": {
      "before": null,
      "after": {
        "geofence_rule_id": 7,
        "floor_id": 2,
        "radius_meters": 50.0,
        "is_active": true
      }
    },
    "ip_address": "192.168.1.10",
    "created_at": "2026-05-20T09:00:00+07:00"
  }
}
```

**Error handling**:

| Status | Code             | Condition                   |
|--------|------------------|-----------------------------|
| `404`  | `LOG_NOT_FOUND`  | Audit log ID does not exist |

---

## 10. Module 9: Admin Management

### 10.1 List Employees

```http
GET /employees
```

**Authorization**: `hr`, `admin`

**Description**: Return a paginated list of employees with account and department info. Supports search by name, email, or phone.

**Query parameters**:

| Parameter       | Type    | Required | Description                                    |
|-----------------|---------|----------|------------------------------------------------|
| `department_id` | integer | No       | Filter by department                           |
| `status`        | string  | No       | `active`, `inactive`, `on_leave`, `terminated` |
| `q`             | string  | No       | Search by full name, email, or phone           |
| `page`          | integer | No       | Page number                                    |
| `limit`         | integer | No       | Items per page                                 |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "employee_id": 10,
      "department_id": 2,
      "department_name": "Engineering",
      "full_name": "Nguyen Van A",
      "email": "employee01@example.com",
      "phone": "0900000000",
      "position": "Developer",
      "hire_date": "2025-01-15",
      "status": "active",
      "account": {
        "account_id": 1,
        "username": "employee01@example.com",
        "role": "employee",
        "is_active": true
      }
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 10.2 Create Employee

```http
POST /employees
```

**Authorization**: `hr`, `admin`

**Description**: Create a new employee profile and linked account. The account is immediately active with the provided temporary password.

**Request body**:

```json
{
  "full_name": "Nguyen Van A",
  "department_id": 2,
  "position": "Developer",
  "email": "employee01@example.com",
  "phone": "0900000000",
  "hire_date": "2025-01-15",
  "role": "employee",
  "temporary_password": "Temp@123456"
}
```

| Field                | Type    | Required | Description                              |
|----------------------|---------|----------|------------------------------------------|
| `full_name`          | string  | Yes      | Employee's full name                     |
| `department_id`      | integer | Yes      | Department to assign                     |
| `position`           | string  | Yes      | Job title/position                       |
| `email`              | string  | Yes      | Must be unique, used as account username |
| `phone`              | string  | Yes      | Must be unique                           |
| `hire_date`          | date    | Yes      | Employee's start date                    |
| `role`               | string  | Yes      | `employee`, `hr`, `manager`, `admin`     |
| `temporary_password` | string  | Yes      | Initial login password (min 8 chars)     |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "account_id": 1,
    "username": "employee01@example.com",
    "status": "active"
  }
}
```

**Error handling**:

| Status | Code                    | Condition                                    |
|--------|-------------------------|----------------------------------------------|
| `409`  | `EMAIL_ALREADY_EXISTS`  | Email is already used by another account     |
| `409`  | `PHONE_ALREADY_EXISTS`  | Phone number is already registered           |
| `404`  | `DEPARTMENT_NOT_FOUND`  | Department ID does not exist                 |
| `422`  | `VALIDATION_ERROR`      | Required field missing or invalid format     |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `create` | `EMPLOYEE` |

---

### 10.3 Employee Detail

```http
GET /employees/{employee_id}
```

**Authorization**: `hr`, `admin`

**Description**: Return the full employee profile including account, current device, and assigned shift.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "department_id": 2,
    "department_name": "Engineering",
    "full_name": "Nguyen Van A",
    "email": "employee01@example.com",
    "phone": "0900000000",
    "position": "Developer",
    "hire_date": "2025-01-15",
    "status": "active",
    "face_registered": true,
    "account": {
      "account_id": 1,
      "username": "employee01@example.com",
      "role": "employee",
      "last_login_at": "2026-05-20T08:00:00+07:00",
      "is_active": true
    },
    "device": {
      "device_id": 12,
      "platform": "android",
      "model": "Pixel 8",
      "is_trusted": true
    },
    "shift": {
      "shift_id": 3,
      "name": "Morning Shift"
    }
  }
}
```

**Error handling**:

| Status | Code                 | Condition                  |
|--------|----------------------|----------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND` | Employee ID does not exist |

---

### 10.4 Update Employee

```http
PUT /employees/{employee_id}
```

**Authorization**: `hr`, `admin`

**Description**: Update employee profile fields. Email and phone uniqueness is re-validated on update.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Request body**:

```json
{
  "full_name": "Nguyen Van A",
  "department_id": 2,
  "position": "Senior Developer",
  "email": "employee01@example.com",
  "phone": "0900000000",
  "hire_date": "2025-01-15",
  "status": "active"
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                   | Condition                               |
|--------|------------------------|-----------------------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND`   | Employee ID does not exist              |
| `409`  | `EMAIL_ALREADY_EXISTS` | Email already used by another account   |
| `409`  | `PHONE_ALREADY_EXISTS` | Phone already used by another employee  |
| `404`  | `DEPARTMENT_NOT_FOUND` | Department ID does not exist            |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `update` | `EMPLOYEE` |

---

### 10.5 Deactivate Employee

```http
PUT /employees/{employee_id}/deactivate
```

**Authorization**: `hr`, `admin`

**Description**: Mark an employee as inactive and lock their account. The employee will no longer be able to log in or check in. The employee record and all attendance history are preserved.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Request body**:

```json
{
  "reason": "Employee resigned"
}
```

| Field    | Type   | Required | Description              |
|----------|--------|----------|--------------------------|
| `reason` | string | No       | Reason for deactivation  |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "status": "inactive",
    "account_locked": true
  }
}
```

**Error handling**:

| Status | Code                   | Condition                         |
|--------|------------------------|-----------------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND`   | Employee ID does not exist        |
| `409`  | `ALREADY_INACTIVE`     | Employee is already inactive      |

**Audit log**:

| Action   | Target     |
|----------|------------|
| `update` | `EMPLOYEE` |
| `update` | `ACCOUNT`  |

---

### 10.6 List Departments

```http
GET /departments
```

**Authorization**: `hr`, `admin`

**Description**: Return all departments with manager info.

**Query parameters**:

| Parameter | Type    | Required | Description              |
|-----------|---------|----------|--------------------------|
| `q`       | string  | No       | Search by department name|
| `page`    | integer | No       | Page number              |
| `limit`   | integer | No       | Items per page           |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "department_id": 2,
      "name": "Engineering",
      "description": "Software engineering team",
      "manager_id": 10,
      "manager_name": "Nguyen Van A",
      "employee_count": 12,
      "created_at": "2026-05-01T09:00:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 10.7 Create Department

```http
POST /departments
```

**Authorization**: `hr`, `admin`

**Description**: Create a new department and optionally assign a manager.

**Request body**:

```json
{
  "name": "Engineering",
  "description": "Software engineering team",
  "manager_id": 10
}
```

| Field        | Type    | Required | Description                            |
|--------------|---------|----------|----------------------------------------|
| `name`       | string  | Yes      | Department name (must be unique)       |
| `description`| string  | No       | Department description                 |
| `manager_id` | integer | No       | Employee ID to assign as manager       |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "department_id": 2,
    "name": "Engineering"
  }
}
```

**Error handling**:

| Status | Code                      | Condition                              |
|--------|---------------------------|----------------------------------------|
| `409`  | `DEPARTMENT_NAME_EXISTS`  | Department name already exists         |
| `404`  | `MANAGER_NOT_FOUND`       | `manager_id` employee does not exist   |

---

### 10.8 Update Department

```http
PUT /departments/{department_id}
```

**Authorization**: `hr`, `admin`

**Description**: Update department name, description, or manager assignment.

**Path parameters**:

| Parameter       | Type    | Description     |
|-----------------|---------|-----------------|
| `department_id` | integer | Department ID   |

**Request body**:

```json
{
  "name": "Engineering",
  "description": "Updated description",
  "manager_id": 10
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "department_id": 2,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                     | Condition                             |
|--------|--------------------------|---------------------------------------|
| `404`  | `DEPARTMENT_NOT_FOUND`   | Department ID does not exist          |
| `409`  | `DEPARTMENT_NAME_EXISTS` | Name already used by another dept     |

**Audit log**:

| Action   | Target       |
|----------|--------------|
| `update` | `DEPARTMENT` |

---

### 10.9 List Shifts

```http
GET /shifts
```

**Authorization**: `hr`, `admin`

**Description**: Return all shifts with optional filter by employee.

**Query parameters**:

| Parameter     | Type    | Required | Description             |
|---------------|---------|----------|-------------------------|
| `employee_id` | integer | No       | Filter by employee      |
| `page`        | integer | No       | Page number             |
| `limit`       | integer | No       | Items per page          |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "shift_id": 3,
      "employee_id": 10,
      "employee_name": "Nguyen Van A",
      "name": "Morning Shift",
      "start_time": "08:00:00",
      "end_time": "17:00:00",
      "late_tolerance_min": 10,
      "early_leave_min": 10,
      "apply_to_weekends": false
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 10.10 Create Shift

```http
POST /shifts
```

**Authorization**: `hr`, `admin`

**Description**: Create a new shift definition and assign it to an employee. Checks for time conflicts with the employee's existing shifts.

**Request body**:

```json
{
  "employee_id": 10,
  "name": "Morning Shift",
  "start_time": "08:00:00",
  "end_time": "17:00:00",
  "late_tolerance_min": 10,
  "early_leave_min": 10,
  "apply_to_weekends": false
}
```

| Field                | Type    | Required | Description                                              |
|----------------------|---------|----------|----------------------------------------------------------|
| `employee_id`        | integer | Yes      | Employee to assign this shift to                         |
| `name`               | string  | Yes      | Shift display name                                       |
| `start_time`         | time    | Yes      | Shift start time (HH:MM:SS)                              |
| `end_time`           | time    | Yes      | Shift end time (HH:MM:SS)                                |
| `late_tolerance_min` | integer | No       | Minutes after start before marking as late (default: 0) |
| `early_leave_min`    | integer | No       | Minutes before end before marking as early leave         |
| `apply_to_weekends`  | boolean | No       | Whether the shift applies on weekends (default: false)   |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "shift_id": 3,
    "name": "Morning Shift"
  }
}
```

**Error handling**:

| Status | Code                   | Condition                                    |
|--------|------------------------|----------------------------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND`   | Employee ID does not exist                   |
| `409`  | `SHIFT_TIME_CONFLICT`  | Shift time overlaps with existing shift      |

**Audit log**:

| Action   | Target  |
|----------|---------|
| `create` | `SHIFT` |

---

### 10.11 Update Shift

```http
PUT /shifts/{shift_id}
```

**Authorization**: `hr`, `admin`

**Description**: Update an existing shift's time parameters. Conflict check is re-run on update.

**Path parameters**:

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `shift_id` | integer | Shift ID    |

**Request body**:

```json
{
  "name": "Morning Shift",
  "start_time": "08:00:00",
  "end_time": "17:30:00",
  "late_tolerance_min": 10,
  "early_leave_min": 10,
  "apply_to_weekends": false
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "shift_id": 3,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code                  | Condition                              |
|--------|-----------------------|----------------------------------------|
| `404`  | `SHIFT_NOT_FOUND`     | Shift ID does not exist                |
| `409`  | `SHIFT_TIME_CONFLICT` | Updated times conflict with another shift|

**Audit log**:

| Action   | Target  |
|----------|---------|
| `update` | `SHIFT` |

---

### 10.12 Assign Shift to Employee

```http
PUT /employees/{employee_id}/shift
```

**Authorization**: `hr`, `admin`

**Description**: Reassign an employee to a different existing shift.

**Path parameters**:

| Parameter     | Type    | Description   |
|---------------|---------|---------------|
| `employee_id` | integer | Employee ID   |

**Request body**:

```json
{
  "shift_id": 3
}
```

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "employee_id": 10,
    "shift_id": 3,
    "assigned": true
  }
}
```

**Error handling**:

| Status | Code                 | Condition                   |
|--------|----------------------|-----------------------------|
| `404`  | `EMPLOYEE_NOT_FOUND` | Employee ID does not exist  |
| `404`  | `SHIFT_NOT_FOUND`    | Shift ID does not exist     |

**Audit log**:

| Action   | Target  |
|----------|---------|
| `update` | `SHIFT` |

---

### 10.13 Register Device

```http
POST /devices/register
```

**Authorization**: `employee`

**Description**: Register the current employee's mobile device. A new device is created with `is_trusted = false` and must be approved by an admin before check-in is allowed.

**Request body**:

```json
{
  "device_fingerprint": "abc-device-fingerprint",
  "platform": "android",
  "model": "Pixel 8",
  "os_version": "Android 15",
  "app_version": "1.0.0"
}
```

| Field                | Type   | Required | Description                        |
|----------------------|--------|----------|------------------------------------|
| `device_fingerprint` | string | Yes      | Unique hardware device identifier  |
| `platform`           | string | Yes      | `android`, `ios`, `web`, `other`   |
| `model`              | string | No       | Device model name                  |
| `os_version`         | string | No       | Operating system version           |
| `app_version`        | string | No       | Mobile app version                 |

**Success response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "device_id": 12,
    "employee_id": 10,
    "platform": "android",
    "model": "Pixel 8",
    "is_trusted": false,
    "registered_at": "2026-05-20T07:30:00+07:00"
  }
}
```

---

### 10.14 Current Employee Device

```http
GET /devices/me
```

**Authorization**: `employee`

**Description**: Return the registered device for the authenticated employee.

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "device_id": 12,
    "device_fingerprint": "abc-device-fingerprint",
    "platform": "android",
    "model": "Pixel 8",
    "registered_at": "2026-05-20T07:30:00+07:00",
    "is_trusted": true
  }
}
```

If no device registered:

```json
{
  "success": true,
  "data": null
}
```

---

### 10.15 List All Devices

```http
GET /devices
```

**Authorization**: `admin`

**Description**: Return a paginated list of all registered devices with employee info. Used for device trust management.

**Query parameters**:

| Parameter     | Type    | Required | Description                 |
|---------------|---------|----------|-----------------------------|
| `employee_id` | integer | No       | Filter by employee          |
| `is_trusted`  | boolean | No       | Filter by trust status      |
| `platform`    | string  | No       | Filter by device platform   |
| `page`        | integer | No       | Page number                 |
| `limit`       | integer | No       | Items per page              |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "device_id": 12,
      "employee": {
        "employee_id": 10,
        "full_name": "Nguyen Van A",
        "department_name": "Engineering"
      },
      "device_fingerprint": "abc-device-fingerprint",
      "platform": "android",
      "model": "Pixel 8",
      "os_version": "Android 15",
      "app_version": "1.0.0",
      "registered_at": "2026-05-20T07:30:00+07:00",
      "is_trusted": true
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### 10.16 Trust or Untrust Device

```http
PUT /devices/{device_id}/trust
```

**Authorization**: `admin`

**Description**: Approve or revoke trust for a device. Only trusted devices are allowed to perform check-in / check-out. Revoking trust takes effect on the next attendance submission.

**Path parameters**:

| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `device_id` | integer | Device ID   |

**Request body**:

```json
{
  "is_trusted": true
}
```

| Field        | Type    | Required | Description               |
|--------------|---------|----------|---------------------------|
| `is_trusted` | boolean | Yes      | `true` to trust, `false` to revoke |

**Success response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "device_id": 12,
    "is_trusted": true,
    "updated": true
  }
}
```

**Error handling**:

| Status | Code               | Condition                 |
|--------|--------------------|---------------------------|
| `404`  | `DEVICE_NOT_FOUND` | Device ID does not exist  |

**Audit log**:

| Action   | Target   |
|----------|----------|
| `update` | `DEVICE` |

---

## 11. Endpoint Summary Table

| Module              | Method   | Endpoint                                       | Authorization                    |
|---------------------|----------|------------------------------------------------|----------------------------------|
| **Authentication**  | `POST`   | `/auth/login`                                  | Public                           |
|                     | `POST`   | `/auth/refresh`                                | Public                           |
|                     | `GET`    | `/auth/me`                                     | All roles                        |
|                     | `POST`   | `/auth/logout`                                 | All roles                        |
|                     | `PUT`    | `/auth/change-password`                        | All roles                        |
| **Attendance**      | `POST`   | `/attendance/check-in`                         | `employee`                       |
|                     | `POST`   | `/attendance/check-out`                        | `employee`                       |
|                     | `GET`    | `/attendance/today-status`                     | `employee`                       |
|                     | `GET`    | `/attendance/history`                          | `employee`, `hr`, `admin`        |
|                     | `GET`    | `/attendance/exceptions`                       | `hr`, `admin`                    |
|                     | `GET`    | `/attendance/{record_id}`                      | `hr`, `admin`                    |
|                     | `PUT`    | `/attendance/{record_id}/approve`              | `hr`, `admin`                    |
| **Geofence**        | `GET`    | `/buildings`                                   | `hr`, `admin`                    |
|                     | `POST`   | `/buildings`                                   | `admin`                          |
|                     | `PUT`    | `/buildings/{building_id}`                     | `admin`                          |
|                     | `GET`    | `/buildings/{building_id}/floors`              | `hr`, `admin`                    |
|                     | `POST`   | `/buildings/{building_id}/floors`              | `admin`                          |
|                     | `PUT`    | `/floors/{floor_id}`                           | `admin`                          |
|                     | `GET`    | `/geofences`                                   | `hr`, `admin`                    |
|                     | `POST`   | `/geofences`                                   | `hr`, `admin`                    |
|                     | `PUT`    | `/geofences/{geofence_id}`                     | `hr`, `admin`                    |
|                     | `DELETE` | `/geofences/{geofence_id}`                     | `hr`, `admin`                    |
| **Fraud Detection** | `POST`   | `/internal/fraud/evaluate`                     | Internal only                    |
|                     | `GET`    | `/fraud/records`                               | `hr`, `admin`                    |
|                     | `GET`    | `/fraud/records/{fraud_id}`                    | `hr`, `admin`                    |
| **Face Verification**| `POST`  | `/employees/{employee_id}/face`                | `hr`, `admin`                    |
|                     | `GET`    | `/employees/{employee_id}/face`                | `hr`, `admin`                    |
|                     | `DELETE` | `/employees/{employee_id}/face`                | `admin`                          |
|                     | `POST`   | `/internal/face/verify`                        | Internal only                    |
| **Notification**    | `GET`    | `/notifications`                               | All roles                        |
|                     | `PUT`    | `/notifications/{notification_id}/read`        | All roles                        |
|                     | `PUT`    | `/notifications/read-all`                      | All roles                        |
|                     | `GET`    | `/notifications/preferences`                   | All roles                        |
|                     | `PUT`    | `/notifications/preferences`                   | All roles                        |
|                     | `POST`   | `/internal/notifications/send`                 | Internal only                    |
| **Report**          | `GET`    | `/dashboard/summary`                           | `manager`, `hr`, `admin`         |
|                     | `GET`    | `/realtime/employees-location`                 | `hr`, `admin`                    |
|                     | `GET`    | `/reports/attendance`                          | `manager`, `hr`, `admin`         |
|                     | `GET`    | `/reports/attendance/export`                   | `hr`, `admin`                    |
| **Audit Log**       | `GET`    | `/audit-logs`                                  | `admin`                          |
|                     | `GET`    | `/audit-logs/{log_id}`                         | `admin`                          |
| **Admin Management**| `GET`    | `/employees`                                   | `hr`, `admin`                    |
|                     | `POST`   | `/employees`                                   | `hr`, `admin`                    |
|                     | `GET`    | `/employees/{employee_id}`                     | `hr`, `admin`                    |
|                     | `PUT`    | `/employees/{employee_id}`                     | `hr`, `admin`                    |
|                     | `PUT`    | `/employees/{employee_id}/deactivate`          | `hr`, `admin`                    |
|                     | `PUT`    | `/employees/{employee_id}/shift`               | `hr`, `admin`                    |
|                     | `GET`    | `/departments`                                 | `hr`, `admin`                    |
|                     | `POST`   | `/departments`                                 | `hr`, `admin`                    |
|                     | `PUT`    | `/departments/{department_id}`                 | `hr`, `admin`                    |
|                     | `GET`    | `/shifts`                                      | `hr`, `admin`                    |
|                     | `POST`   | `/shifts`                                      | `hr`, `admin`                    |
|                     | `PUT`    | `/shifts/{shift_id}`                           | `hr`, `admin`                    |
|                     | `POST`   | `/devices/register`                            | `employee`                       |
|                     | `GET`    | `/devices/me`                                  | `employee`                       |
|                     | `GET`    | `/devices`                                     | `admin`                          |
|                     | `PUT`    | `/devices/{device_id}/trust`                   | `admin`                          |

**Total endpoints: 47** (35 public-facing + 3 internal + 9 previously missing)

---

## 12. Gap Analysis vs MVP Docs

The following endpoints are **present in this document but absent from `API_DOCS_MVP.md`**:

| Endpoint                                    | Reason Added                                                               |
|---------------------------------------------|----------------------------------------------------------------------------|
| `POST /auth/refresh`                        | Required for token renewal without re-login on mobile                      |
| `PUT /auth/change-password`                 | Required for account security; not covered in MVP doc                      |
| `GET /fraud/records`                        | UC-11/UC-12 reference fraud review by HR/Admin — no view API existed       |
| `GET /fraud/records/{fraud_id}`             | Detail view for fraud investigation                                         |
| `POST /employees/{employee_id}/face`        | UC-02/UC-03 require a registered face reference; no registration API existed|
| `GET /employees/{employee_id}/face`         | Status check before attempting check-in                                     |
| `DELETE /employees/{employee_id}/face`      | Admin cleanup when face reference must be reset                             |
| `GET /notifications`                        | UC-05 is entirely about employee notifications; no notification API existed |
| `PUT /notifications/{notification_id}/read` | Required for mobile unread badge management                                 |
| `PUT /notifications/read-all`               | Bulk clear for notification inbox                                           |
| `GET /notifications/preferences`            | Allow users to control which events trigger push vs in-app                  |
| `PUT /notifications/preferences`            | Required for preference management                                          |
| `POST /internal/notifications/send`         | Internal dispatch contract for the notification service                     |

**Key observations**:

1. `API_DOCS_MVP.md` has no notification module at all despite UC-05 being a defined use case.
2. Face registration had no public API — employees could never have their face set up via the web dashboard.
3. Fraud records were only visible inline in the attendance record detail, with no dedicated browsing or filtering capability.
4. Token refresh and password change are essential for a production mobile app and were missing.
