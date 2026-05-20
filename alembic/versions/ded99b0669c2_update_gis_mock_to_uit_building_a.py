"""update gis mock to uit building a

Revision ID: ded99b0669c2
Revises: 7239ba51b5c2
Create Date: 2026-05-20 11:28:21.535050

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ded99b0669c2'
down_revision: Union[str, Sequence[str], None] = '7239ba51b5c2'
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
            'Tòa nhà A - Trường Đại học Công nghệ Thông tin, ĐHQG-HCM',
            'Tòa nhà A, Trường Đại học Công nghệ Thông tin - ĐHQG-HCM, Khu phố 6, Phường Linh Trung, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam',
            10.87040780,
            106.80290665,
            2,
            'uit-building-a-2f'
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
            (1001, 1001, 1, 'Floor 1 - Entrance, Check-in, and Lab Areas', 0.00, 4.00),
            (1002, 1001, 2, 'Floor 2 - Classrooms and Faculty Areas', 4.00, 8.00)
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
            (1001, 1001, 1001, 'A1 Main Entrance Lobby', 'Building A Floor 1, UIT, Linh Trung Ward, Thu Duc City', 10.87012000, 106.80288000, 2, 'uit-building-a-f1-lobby'),
            (1002, 1001, 1001, 'A1 Computer Lab', 'Building A Floor 1, UIT, Linh Trung Ward, Thu Duc City', 10.87032000, 106.80306000, 2, 'uit-building-a-f1-lab'),
            (1003, 1001, 1001, 'A1 Lecture Room', 'Building A Floor 1, UIT, Linh Trung Ward, Thu Duc City', 10.87064000, 106.80305000, 2, 'uit-building-a-f1-lecture'),
            (1004, 1001, 1001, 'A1 Attendance Check-in Zone', 'Building A Floor 1, UIT, Linh Trung Ward, Thu Duc City', 10.87034000, 106.80275000, 2, 'uit-building-a-f1-checkin'),
            (1005, 1002, 1001, 'A2 Faculty Office', 'Building A Floor 2, UIT, Linh Trung Ward, Thu Duc City', 10.87012000, 106.80288000, 2, 'uit-building-a-f2-faculty'),
            (1006, 1002, 1001, 'A2 Meeting Room', 'Building A Floor 2, UIT, Linh Trung Ward, Thu Duc City', 10.87032000, 106.80306000, 2, 'uit-building-a-f2-meeting'),
            (1007, 1002, 1001, 'A2 Lecture Room', 'Building A Floor 2, UIT, Linh Trung Ward, Thu Duc City', 10.87064000, 106.80305000, 2, 'uit-building-a-f2-lecture'),
            (1008, 1002, 1001, 'A2 Self-study Space', 'Building A Floor 2, UIT, Linh Trung Ward, Thu Duc City', 10.87034000, 106.80275000, 2, 'uit-building-a-f2-study')
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
            (1001, 1001, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.80278,10.87003],[106.80300,10.87003],[106.80310,10.87013],[106.80302,10.87022],[106.80280,10.87019],[106.80270,10.87012],[106.80278,10.87003]]]}$json$),
            (1002, 1002, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.80302,10.87020],[106.80313,10.87022],[106.80315,10.87035],[106.80302,10.87047],[106.80293,10.87040],[106.80298,10.87030],[106.80302,10.87020]]]}$json$),
            (1003, 1003, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.80302,10.87050],[106.80315,10.87060],[106.80315,10.87070],[106.80308,10.87078],[106.80296,10.87070],[106.80298,10.87058],[106.80302,10.87050]]]}$json$),
            (1004, 1004, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4,"rings":[[[106.80266,10.87016],[106.80283,10.87030],[106.80283,10.87050],[106.80274,10.87046],[106.80265,10.87037],[106.80268,10.87028],[106.80266,10.87016]]]}$json$),
            (1005, 1005, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.80278,10.87003],[106.80300,10.87003],[106.80310,10.87013],[106.80302,10.87022],[106.80280,10.87019],[106.80270,10.87012],[106.80278,10.87003]]]}$json$),
            (1006, 1006, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.80302,10.87020],[106.80313,10.87022],[106.80315,10.87035],[106.80302,10.87047],[106.80293,10.87040],[106.80298,10.87030],[106.80302,10.87020]]]}$json$),
            (1007, 1007, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.80302,10.87050],[106.80315,10.87060],[106.80315,10.87070],[106.80308,10.87078],[106.80296,10.87070],[106.80298,10.87058],[106.80302,10.87050]]]}$json$),
            (1008, 1008, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4,"altitude_max":8,"rings":[[[106.80266,10.87016],[106.80283,10.87030],[106.80283,10.87050],[106.80274,10.87046],[106.80265,10.87037],[106.80268,10.87028],[106.80266,10.87016]]]}$json$)
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
            (1002, 1002, 18.00, 0.00, 4.00, true, true, true, 1001),
            (1003, 1003, 18.00, 0.00, 4.00, true, true, true, 1001),
            (1004, 1004, 15.00, 0.00, 4.00, true, true, true, 1001),
            (1005, 1005, 18.00, 4.00, 8.00, true, true, true, 1001),
            (1006, 1006, 18.00, 4.00, 8.00, true, true, true, 1001),
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
            (1001, 1001, 'uit-building-a-f1-lobby-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1001', true),
            (1002, 1002, 'uit-building-a-f1-lab-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1002', true),
            (1003, 1003, 'uit-building-a-f1-lecture-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1003', true),
            (1004, 1004, 'uit-building-a-f1-checkin-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1004', true),
            (1005, 1005, 'uit-building-a-f2-faculty-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1005', true),
            (1006, 1006, 'uit-building-a-f2-meeting-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1006', true),
            (1007, 1007, 'uit-building-a-f2-lecture-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1007', true),
            (1008, 1008, 'uit-building-a-f2-study-layer', 'indoor-room', 'testing/uit_building_a_gis_data.json#cell-space-1008', true)
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
            (1001, 1001, 10.87012000, 106.80288000, 0.60, 'entrance'),
            (1002, 1004, 10.87034000, 106.80275000, 0.60, 'checkin-kiosk'),
            (1003, 1002, 10.87032000, 106.80306000, 0.60, 'computer-lab'),
            (1004, 1007, 10.87064000, 106.80305000, 4.60, 'lecture-room'),
            (1005, 1005, 10.87012000, 106.80288000, 4.60, 'faculty-office'),
            (1006, 1006, 10.87032000, 106.80306000, 4.60, 'meeting-room'),
            (1007, 1008, 10.87034000, 106.80275000, 4.60, 'self-study')
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
            (1002, 1002, 1003, 'hallway', 40.00),
            (1003, 1003, 1004, 'stairs', 24.00),
            (1004, 1004, 1005, 'hallway', 62.00),
            (1005, 1005, 1006, 'hallway', 40.00),
            (1006, 1006, 1007, 'hallway', 35.00)
        ON CONFLICT (transition_id) DO UPDATE SET
            from_state_id = EXCLUDED.from_state_id,
            to_state_id = EXCLUDED.to_state_id,
            transition_type = EXCLUDED.transition_type,
            distance_m = EXCLUDED.distance_m;

        UPDATE business.attendance_record
        SET latitude = CASE record_id
                WHEN 1001 THEN 10.870320
                WHEN 1002 THEN 10.870320
                WHEN 1003 THEN 10.870120
                WHEN 1004 THEN 10.870340
                WHEN 1005 THEN 10.870640
            END,
            longitude = CASE record_id
                WHEN 1001 THEN 106.803060
                WHEN 1002 THEN 106.803060
                WHEN 1003 THEN 106.802880
                WHEN 1004 THEN 106.802750
                WHEN 1005 THEN 106.803050
            END,
            altitude = CASE record_id
                WHEN 1001 THEN 0.80
                WHEN 1002 THEN 0.90
                WHEN 1003 THEN 4.60
                WHEN 1004 THEN 0.70
                WHEN 1005 THEN 4.60
            END
        WHERE record_id IN (1001, 1002, 1003, 1004, 1005);
    """)


def downgrade() -> None:
    op.get_bind().exec_driver_sql("""
        UPDATE gis.building
        SET name = 'Main Office - Linh Trung',
            address = 'Linh Trung Ward, Thu Duc City, Ho Chi Minh City, Vietnam',
            center_lat = 10.77212300,
            center_lng = 106.65789000,
            total_floors = 2,
            arcgis_layer_id = 'main-office-linh-trung-2f'
        WHERE building_id = 1001;
    """)
