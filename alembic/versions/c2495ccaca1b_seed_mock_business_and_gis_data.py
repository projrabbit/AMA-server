"""seed mock business and gis data

Revision ID: c2495ccaca1b
Revises: 5072b8ca88f8
Create Date: 2026-05-20 10:21:31.120831

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c2495ccaca1b'
down_revision: Union[str, Sequence[str], None] = '5072b8ca88f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql("""
        INSERT INTO gis.building (
            building_id,
            name,
            address,
            center_lat,
            center_lng,
            total_floors,
            arcgis_layer_id
        ) VALUES (
            1001,
            'AMA Two-Floor Office',
            '1 ArcGIS Demo Street, Ho Chi Minh City',
            10.77687500,
            106.70081500,
            2,
            'ama-hq-building'
        ) ON CONFLICT (building_id) DO UPDATE SET
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            center_lat = EXCLUDED.center_lat,
            center_lng = EXCLUDED.center_lng,
            total_floors = EXCLUDED.total_floors,
            arcgis_layer_id = EXCLUDED.arcgis_layer_id;

        INSERT INTO gis.floor (
            floor_id,
            building_id,
            floor_number,
            floor_name,
            altitude_min,
            altitude_max
        ) VALUES
            (1001, 1001, 1, 'Floor 1 - Operations', 0.00, 4.00),
            (1002, 1001, 2, 'Floor 2 - Management', 4.00, 8.00)
        ON CONFLICT (floor_id) DO UPDATE SET
            building_id = EXCLUDED.building_id,
            floor_number = EXCLUDED.floor_number,
            floor_name = EXCLUDED.floor_name,
            altitude_min = EXCLUDED.altitude_min,
            altitude_max = EXCLUDED.altitude_max;

        INSERT INTO gis.cell_space (
            cell_space_id,
            floor_id,
            building_id,
            name,
            address,
            center_lat,
            center_lng,
            total_floors,
            arcgis_layer_id
        ) VALUES
            (1001, 1001, 1001, 'Main Lobby', 'Floor 1 / South West', 10.77678500, 106.70065000, 2, 'ama-hq-f1-lobby'),
            (1002, 1001, 1001, 'Engineering Hub', 'Floor 1 / North West', 10.77699000, 106.70071000, 2, 'ama-hq-f1-engineering'),
            (1003, 1001, 1001, 'Meeting Room A', 'Floor 1 / North East', 10.77697000, 106.70100500, 2, 'ama-hq-f1-meeting-a'),
            (1004, 1001, 1001, 'Check-in Cafe', 'Floor 1 / South East', 10.77676500, 106.70094500, 2, 'ama-hq-f1-checkin-cafe'),
            (1005, 1002, 1001, 'HR Office', 'Floor 2 / South West', 10.77678500, 106.70065000, 2, 'ama-hq-f2-hr'),
            (1006, 1002, 1001, 'Admin Office', 'Floor 2 / South East', 10.77678500, 106.70094500, 2, 'ama-hq-f2-admin'),
            (1007, 1002, 1001, 'Conference Hall', 'Floor 2 / North West', 10.77699000, 106.70071000, 2, 'ama-hq-f2-conference'),
            (1008, 1002, 1001, 'Quiet Workspace', 'Floor 2 / North East', 10.77699000, 106.70100500, 2, 'ama-hq-f2-quiet-workspace')
        ON CONFLICT (cell_space_id) DO UPDATE SET
            floor_id = EXCLUDED.floor_id,
            building_id = EXCLUDED.building_id,
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            center_lat = EXCLUDED.center_lat,
            center_lng = EXCLUDED.center_lng,
            total_floors = EXCLUDED.total_floors,
            arcgis_layer_id = EXCLUDED.arcgis_layer_id;

        INSERT INTO gis.cell_space_boundary (
            boundary_id,
            cell_space_id,
            boundary_type,
            boundary_geometry_type,
            description
        ) VALUES
            (1001, 1001, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.70052,10.77667],[106.70078,10.77667],[106.70078,10.77690],[106.70052,10.77690],[106.70052,10.77667]]]}$json$),
            (1002, 1002, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.70052,10.77690],[106.70090,10.77690],[106.70090,10.77708],[106.70052,10.77708],[106.70052,10.77690]]]}$json$),
            (1003, 1003, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.70090,10.77686],[106.70111,10.77686],[106.70111,10.77708],[106.70090,10.77708],[106.70090,10.77686]]]}$json$),
            (1004, 1004, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.70078,10.77667],[106.70111,10.77667],[106.70111,10.77686],[106.70078,10.77686],[106.70078,10.77667]]]}$json$),
            (1005, 1005, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.70052,10.77667],[106.70078,10.77667],[106.70078,10.77690],[106.70052,10.77690],[106.70052,10.77667]]]}$json$),
            (1006, 1006, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.70078,10.77667],[106.70111,10.77667],[106.70111,10.77690],[106.70078,10.77690],[106.70078,10.77667]]]}$json$),
            (1007, 1007, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.70052,10.77690],[106.70090,10.77690],[106.70090,10.77708],[106.70052,10.77708],[106.70052,10.77690]]]}$json$),
            (1008, 1008, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.70090,10.77690],[106.70111,10.77690],[106.70111,10.77708],[106.70090,10.77708],[106.70090,10.77690]]]}$json$)
        ON CONFLICT (boundary_id) DO UPDATE SET
            cell_space_id = EXCLUDED.cell_space_id,
            boundary_type = EXCLUDED.boundary_type,
            boundary_geometry_type = EXCLUDED.boundary_geometry_type,
            description = EXCLUDED.description;

        INSERT INTO gis.geofence_rule (
            geofence_rule_id,
            cell_space_id,
            allowed_radius_m,
            altitude_min,
            altitude_max,
            allow_checkin,
            allow_checkout,
            is_active,
            created_by_account_id
        ) VALUES
            (1001, 1001, 18.00, 0.00, 4.00, true, true, true, 1001),
            (1002, 1002, 20.00, 0.00, 4.00, true, true, true, 1001),
            (1003, 1003, 12.00, 0.00, 4.00, true, true, true, 1001),
            (1004, 1004, 15.00, 0.00, 4.00, true, true, true, 1001),
            (1005, 1005, 12.00, 4.00, 8.00, true, true, true, 1001),
            (1006, 1006, 12.00, 4.00, 8.00, true, true, true, 1001),
            (1007, 1007, 18.00, 4.00, 8.00, true, true, true, 1001),
            (1008, 1008, 15.00, 4.00, 8.00, true, true, true, 1001)
        ON CONFLICT (geofence_rule_id) DO UPDATE SET
            cell_space_id = EXCLUDED.cell_space_id,
            allowed_radius_m = EXCLUDED.allowed_radius_m,
            altitude_min = EXCLUDED.altitude_min,
            altitude_max = EXCLUDED.altitude_max,
            allow_checkin = EXCLUDED.allow_checkin,
            allow_checkout = EXCLUDED.allow_checkout,
            is_active = EXCLUDED.is_active,
            created_by_account_id = EXCLUDED.created_by_account_id;

        INSERT INTO gis.gis_layer (
            layer_id,
            cell_space_id,
            arcgis_layer_id,
            layer_type,
            layer_url,
            is_visible
        ) VALUES
            (1001, 1001, 'ama-hq-f1-lobby-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1001', true),
            (1002, 1002, 'ama-hq-f1-engineering-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1002', true),
            (1003, 1003, 'ama-hq-f1-meeting-a-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1003', true),
            (1004, 1004, 'ama-hq-f1-checkin-cafe-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1004', true),
            (1005, 1005, 'ama-hq-f2-hr-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1005', true),
            (1006, 1006, 'ama-hq-f2-admin-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1006', true),
            (1007, 1007, 'ama-hq-f2-conference-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1007', true),
            (1008, 1008, 'ama-hq-f2-quiet-workspace-layer', 'indoor-room', 'testing/ama_hq_gis_data.json#cell-space-1008', true)
        ON CONFLICT (layer_id) DO UPDATE SET
            cell_space_id = EXCLUDED.cell_space_id,
            arcgis_layer_id = EXCLUDED.arcgis_layer_id,
            layer_type = EXCLUDED.layer_type,
            layer_url = EXCLUDED.layer_url,
            is_visible = EXCLUDED.is_visible;

        INSERT INTO gis.state (
            state_id,
            cell_space_id,
            latitude,
            longitude,
            altitude,
            state_type
        ) VALUES
            (1001, 1001, 10.77678500, 106.70065000, 0.50, 'entrance'),
            (1002, 1004, 10.77676500, 106.70094500, 0.50, 'checkin-kiosk'),
            (1003, 1002, 10.77699000, 106.70071000, 0.50, 'work-zone'),
            (1004, 1007, 10.77699000, 106.70071000, 4.50, 'conference'),
            (1005, 1005, 10.77678500, 106.70065000, 4.50, 'hr-desk'),
            (1006, 1006, 10.77678500, 106.70094500, 4.50, 'admin-desk'),
            (1007, 1008, 10.77699000, 106.70100500, 4.50, 'quiet-zone')
        ON CONFLICT (state_id) DO UPDATE SET
            cell_space_id = EXCLUDED.cell_space_id,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            altitude = EXCLUDED.altitude,
            state_type = EXCLUDED.state_type;

        INSERT INTO gis.transition (
            transition_id,
            from_state_id,
            to_state_id,
            transition_type,
            distance_m
        ) VALUES
            (1001, 1001, 1002, 'hallway', 32.00),
            (1002, 1002, 1003, 'hallway', 28.00),
            (1003, 1003, 1004, 'stairs', 18.00),
            (1004, 1004, 1005, 'hallway', 24.00),
            (1005, 1005, 1006, 'hallway', 30.00),
            (1006, 1006, 1007, 'hallway', 22.00)
        ON CONFLICT (transition_id) DO UPDATE SET
            from_state_id = EXCLUDED.from_state_id,
            to_state_id = EXCLUDED.to_state_id,
            transition_type = EXCLUDED.transition_type,
            distance_m = EXCLUDED.distance_m;
    """)

    op.get_bind().exec_driver_sql("""
        INSERT INTO business.department (
            department_id,
            name,
            description,
            created_at,
            manager_id
        ) VALUES
            (1001, 'Engineering', 'Builds attendance, GIS, and mobile services.', TIMESTAMPTZ '2026-05-20 08:00:00+07', NULL),
            (1002, 'Human Resources', 'Handles employee records and attendance approvals.', TIMESTAMPTZ '2026-05-20 08:00:00+07', NULL),
            (1003, 'Operations', 'Manages office operations and device enrollment.', TIMESTAMPTZ '2026-05-20 08:00:00+07', NULL)
        ON CONFLICT (department_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            created_at = EXCLUDED.created_at;

        INSERT INTO business.employee (
            employee_id,
            department_id,
            full_name,
            email,
            phone,
            position,
            hire_date,
            status
        ) VALUES
            (1001, 1001, 'Linh Tran', 'linh.tran@example.com', '+84901000001', 'Engineering Manager', DATE '2024-01-15', 'active'),
            (1002, 1001, 'Minh Nguyen', 'minh.nguyen@example.com', '+84901000002', 'Mobile Engineer', DATE '2024-03-01', 'active'),
            (1003, 1002, 'Hoa Pham', 'hoa.pham@example.com', '+84901000003', 'HR Specialist', DATE '2023-11-20', 'active'),
            (1004, 1003, 'Quang Le', 'quang.le@example.com', '+84901000004', 'Operations Coordinator', DATE '2024-04-10', 'active')
        ON CONFLICT (employee_id) DO UPDATE SET
            department_id = EXCLUDED.department_id,
            full_name = EXCLUDED.full_name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            position = EXCLUDED.position,
            hire_date = EXCLUDED.hire_date,
            status = EXCLUDED.status;

        UPDATE business.department
        SET manager_id = CASE department_id
            WHEN 1001 THEN 1001
            WHEN 1002 THEN 1003
            WHEN 1003 THEN 1004
        END
        WHERE department_id IN (1001, 1002, 1003);

        INSERT INTO business.account (
            account_id,
            employee_id,
            username,
            password_hash,
            role,
            last_login_at,
            is_active
        ) VALUES
            (1001, 1001, 'linh.tran@example.com', 'mock-password-hash-admin', 'admin', TIMESTAMPTZ '2026-05-20 08:05:00+07', true),
            (1002, 1002, 'minh.nguyen@example.com', 'mock-password-hash-employee', 'employee', TIMESTAMPTZ '2026-05-20 08:34:00+07', true),
            (1003, 1003, 'hoa.pham@example.com', 'mock-password-hash-hr', 'hr', TIMESTAMPTZ '2026-05-20 09:15:00+07', true),
            (1004, 1004, 'quang.le@example.com', 'mock-password-hash-manager', 'manager', TIMESTAMPTZ '2026-05-20 08:22:00+07', true)
        ON CONFLICT (account_id) DO UPDATE SET
            employee_id = EXCLUDED.employee_id,
            username = EXCLUDED.username,
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            last_login_at = EXCLUDED.last_login_at,
            is_active = EXCLUDED.is_active;

        INSERT INTO business.device (
            device_id,
            employee_id,
            device_fingerprint,
            platform,
            model,
            register_at,
            is_trusted
        ) VALUES
            (1001, 1001, 'ama-demo-device-linh', 'ios', 'iPhone 15', TIMESTAMPTZ '2026-05-18 09:00:00+07', true),
            (1002, 1002, 'ama-demo-device-minh', 'android', 'Pixel 8', TIMESTAMPTZ '2026-05-18 09:30:00+07', true),
            (1003, 1003, 'ama-demo-device-hoa', 'ios', 'iPhone 14', TIMESTAMPTZ '2026-05-18 10:00:00+07', true),
            (1004, 1004, 'ama-demo-device-quang', 'android', 'Galaxy S24', TIMESTAMPTZ '2026-05-18 10:30:00+07', false)
        ON CONFLICT (device_id) DO UPDATE SET
            employee_id = EXCLUDED.employee_id,
            device_fingerprint = EXCLUDED.device_fingerprint,
            platform = EXCLUDED.platform,
            model = EXCLUDED.model,
            register_at = EXCLUDED.register_at,
            is_trusted = EXCLUDED.is_trusted;

        INSERT INTO business.shift (
            shift_id,
            employee_id,
            name,
            start_time,
            end_time,
            late_tolerance_min,
            early_leave_min,
            apply_to_weekends
        ) VALUES
            (1001, 1001, 'Office Day Shift', TIME '08:30:00', TIME '17:30:00', 10, 10, false),
            (1002, 1002, 'Office Day Shift', TIME '08:30:00', TIME '17:30:00', 10, 10, false),
            (1003, 1003, 'HR Day Shift', TIME '09:00:00', TIME '18:00:00', 15, 10, false),
            (1004, 1004, 'Operations Early Shift', TIME '08:00:00', TIME '17:00:00', 10, 10, false)
        ON CONFLICT (shift_id) DO UPDATE SET
            employee_id = EXCLUDED.employee_id,
            name = EXCLUDED.name,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            late_tolerance_min = EXCLUDED.late_tolerance_min,
            early_leave_min = EXCLUDED.early_leave_min,
            apply_to_weekends = EXCLUDED.apply_to_weekends;

        INSERT INTO business.attendance_record (
            record_id,
            employee_id,
            device_id,
            shift_id,
            geofence_rule_id,
            type,
            timestamp,
            latitude,
            longitude,
            altitude,
            gps_accuracy,
            status,
            rejection_reason,
            is_late,
            is_early_leave
        ) VALUES
            (1001, 1002, 1002, 1002, 1002, 'checkin', TIMESTAMPTZ '2026-05-20 08:35:00+07', 10.776990, 106.700710, 0.80, 4.20, 'approved', NULL, false, false),
            (1002, 1002, 1002, 1002, 1002, 'checkout', TIMESTAMPTZ '2026-05-20 17:31:00+07', 10.776995, 106.700715, 0.90, 5.10, 'approved', NULL, false, false),
            (1003, 1003, 1003, 1003, 1005, 'checkin', TIMESTAMPTZ '2026-05-20 09:07:00+07', 10.776785, 106.700650, 4.60, 3.80, 'pending', NULL, false, false),
            (1004, 1004, 1004, 1004, 1004, 'checkin', TIMESTAMPTZ '2026-05-20 08:22:00+07', 10.776765, 106.700945, 0.70, 16.40, 'flagged', 'gps_spoofing', false, false),
            (1005, 1001, 1001, 1001, 1007, 'checkin', TIMESTAMPTZ '2026-05-20 08:28:00+07', 10.776990, 106.700710, 4.50, 3.50, 'approved', NULL, false, false)
        ON CONFLICT (record_id) DO UPDATE SET
            employee_id = EXCLUDED.employee_id,
            device_id = EXCLUDED.device_id,
            shift_id = EXCLUDED.shift_id,
            geofence_rule_id = EXCLUDED.geofence_rule_id,
            type = EXCLUDED.type,
            timestamp = EXCLUDED.timestamp,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            altitude = EXCLUDED.altitude,
            gps_accuracy = EXCLUDED.gps_accuracy,
            status = EXCLUDED.status,
            rejection_reason = EXCLUDED.rejection_reason,
            is_late = EXCLUDED.is_late,
            is_early_leave = EXCLUDED.is_early_leave;

        INSERT INTO business.fraud_detection (
            fraud_id,
            record_id,
            mock_location_detected,
            gps_spoofing_detected,
            buddy_punch_suspected,
            reason,
            checked_at
        ) VALUES
            (1001, 1004, false, true, false, 'GPS jump pattern and high reported accuracy variance near check-in cafe.', TIMESTAMPTZ '2026-05-20 08:23:00+07')
        ON CONFLICT (fraud_id) DO UPDATE SET
            record_id = EXCLUDED.record_id,
            mock_location_detected = EXCLUDED.mock_location_detected,
            gps_spoofing_detected = EXCLUDED.gps_spoofing_detected,
            buddy_punch_suspected = EXCLUDED.buddy_punch_suspected,
            reason = EXCLUDED.reason,
            checked_at = EXCLUDED.checked_at;

        INSERT INTO business.audit_log (
            log_id,
            account_id,
            action_type,
            target_entity,
            target_id,
            payload,
            created_at
        ) VALUES
            (1001, 1001, 'create', 'EMPLOYEE', 1002, $json${"source":"seed","employee_id":1002,"department":"Engineering"}$json$::json, TIMESTAMPTZ '2026-05-20 08:01:00+07'),
            (1002, 1002, 'checkin', 'ATTENDANCE_RECORD', 1001, $json${"source":"mobile","geofence_rule_id":1002,"cell_space":"Engineering Hub"}$json$::json, TIMESTAMPTZ '2026-05-20 08:35:00+07'),
            (1003, 1003, 'approve', 'ATTENDANCE_RECORD', 1001, $json${"source":"hr-dashboard","status":"approved"}$json$::json, TIMESTAMPTZ '2026-05-20 09:20:00+07'),
            (1004, 1004, 'checkin', 'ATTENDANCE_RECORD', 1004, $json${"source":"mobile","status":"flagged","reason":"gps_spoofing"}$json$::json, TIMESTAMPTZ '2026-05-20 08:22:00+07')
        ON CONFLICT (log_id) DO UPDATE SET
            account_id = EXCLUDED.account_id,
            action_type = EXCLUDED.action_type,
            target_entity = EXCLUDED.target_entity,
            target_id = EXCLUDED.target_id,
            payload = EXCLUDED.payload,
            created_at = EXCLUDED.created_at;
    """)

    op.get_bind().exec_driver_sql("""
        SELECT setval(pg_get_serial_sequence('gis.building', 'building_id'), GREATEST((SELECT COALESCE(MAX(building_id), 1) FROM gis.building), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.floor', 'floor_id'), GREATEST((SELECT COALESCE(MAX(floor_id), 1) FROM gis.floor), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.cell_space', 'cell_space_id'), GREATEST((SELECT COALESCE(MAX(cell_space_id), 1) FROM gis.cell_space), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.cell_space_boundary', 'boundary_id'), GREATEST((SELECT COALESCE(MAX(boundary_id), 1) FROM gis.cell_space_boundary), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.geofence_rule', 'geofence_rule_id'), GREATEST((SELECT COALESCE(MAX(geofence_rule_id), 1) FROM gis.geofence_rule), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.gis_layer', 'layer_id'), GREATEST((SELECT COALESCE(MAX(layer_id), 1) FROM gis.gis_layer), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.state', 'state_id'), GREATEST((SELECT COALESCE(MAX(state_id), 1) FROM gis.state), 1), true);
        SELECT setval(pg_get_serial_sequence('gis.transition', 'transition_id'), GREATEST((SELECT COALESCE(MAX(transition_id), 1) FROM gis.transition), 1), true);

        SELECT setval(pg_get_serial_sequence('business.department', 'department_id'), GREATEST((SELECT COALESCE(MAX(department_id), 1) FROM business.department), 1), true);
        SELECT setval(pg_get_serial_sequence('business.employee', 'employee_id'), GREATEST((SELECT COALESCE(MAX(employee_id), 1) FROM business.employee), 1), true);
        SELECT setval(pg_get_serial_sequence('business.account', 'account_id'), GREATEST((SELECT COALESCE(MAX(account_id), 1) FROM business.account), 1), true);
        SELECT setval(pg_get_serial_sequence('business.device', 'device_id'), GREATEST((SELECT COALESCE(MAX(device_id), 1) FROM business.device), 1), true);
        SELECT setval(pg_get_serial_sequence('business.shift', 'shift_id'), GREATEST((SELECT COALESCE(MAX(shift_id), 1) FROM business.shift), 1), true);
        SELECT setval(pg_get_serial_sequence('business.attendance_record', 'record_id'), GREATEST((SELECT COALESCE(MAX(record_id), 1) FROM business.attendance_record), 1), true);
        SELECT setval(pg_get_serial_sequence('business.fraud_detection', 'fraud_id'), GREATEST((SELECT COALESCE(MAX(fraud_id), 1) FROM business.fraud_detection), 1), true);
        SELECT setval(pg_get_serial_sequence('business.audit_log', 'log_id'), GREATEST((SELECT COALESCE(MAX(log_id), 1) FROM business.audit_log), 1), true);
    """)


def downgrade() -> None:
    op.get_bind().exec_driver_sql("""
        DELETE FROM business.audit_log WHERE log_id IN (1001, 1002, 1003, 1004);
        DELETE FROM business.fraud_detection WHERE fraud_id IN (1001);
        DELETE FROM business.attendance_record WHERE record_id IN (1001, 1002, 1003, 1004, 1005);
        DELETE FROM business.shift WHERE shift_id IN (1001, 1002, 1003, 1004);
        DELETE FROM business.device WHERE device_id IN (1001, 1002, 1003, 1004);
        DELETE FROM business.account WHERE account_id IN (1001, 1002, 1003, 1004);
        UPDATE business.department SET manager_id = NULL WHERE department_id IN (1001, 1002, 1003);
        DELETE FROM business.employee WHERE employee_id IN (1001, 1002, 1003, 1004);
        DELETE FROM business.department WHERE department_id IN (1001, 1002, 1003);

        DELETE FROM gis.transition WHERE transition_id IN (1001, 1002, 1003, 1004, 1005, 1006);
        DELETE FROM gis.state WHERE state_id IN (1001, 1002, 1003, 1004, 1005, 1006, 1007);
        DELETE FROM gis.gis_layer WHERE layer_id IN (1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008);
        DELETE FROM gis.geofence_rule WHERE geofence_rule_id IN (1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008);
        DELETE FROM gis.cell_space_boundary WHERE boundary_id IN (1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008);
        DELETE FROM gis.cell_space WHERE cell_space_id IN (1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008);
        DELETE FROM gis.floor WHERE floor_id IN (1001, 1002);
        DELETE FROM gis.building WHERE building_id IN (1001);
    """)
