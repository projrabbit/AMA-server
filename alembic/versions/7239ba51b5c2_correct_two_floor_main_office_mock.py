"""correct two floor main office mock

Revision ID: 7239ba51b5c2
Revises: c2495ccaca1b
Create Date: 2026-05-20 10:34:58.228981

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7239ba51b5c2'
down_revision: Union[str, Sequence[str], None] = 'c2495ccaca1b'
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
            'Main Office - Linh Trung',
            'Linh Trung Ward, Thu Duc City, Ho Chi Minh City, Vietnam',
            10.77212300,
            106.65789000,
            2,
            'main-office-linh-trung-2f'
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
            (1001, 1001, 1, 'Floor 1 - Reception and Engineering', 0.00, 4.20),
            (1002, 1001, 2, 'Floor 2 - HR and Management', 4.20, 8.40)
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
            (1001, 1001, 1001, 'Reception Lobby', 'Main Office Floor 1, Linh Trung Ward, Thu Duc City', 10.77203000, 106.65774000, 2, 'main-office-f1-reception'),
            (1002, 1001, 1001, 'Engineering Workspace', 'Main Office Floor 1, Linh Trung Ward, Thu Duc City', 10.77221500, 106.65780000, 2, 'main-office-f1-engineering'),
            (1003, 1001, 1001, 'Meeting Room 1A', 'Main Office Floor 1, Linh Trung Ward, Thu Duc City', 10.77221500, 106.65807000, 2, 'main-office-f1-meeting-1a'),
            (1004, 1001, 1001, 'Check-in Point', 'Main Office Floor 1, Linh Trung Ward, Thu Duc City', 10.77203000, 106.65801000, 2, 'main-office-f1-checkin'),
            (1005, 1002, 1001, 'HR Office', 'Main Office Floor 2, Linh Trung Ward, Thu Duc City', 10.77203000, 106.65774000, 2, 'main-office-f2-hr'),
            (1006, 1002, 1001, 'Management Office', 'Main Office Floor 2, Linh Trung Ward, Thu Duc City', 10.77203000, 106.65801000, 2, 'main-office-f2-management'),
            (1007, 1002, 1001, 'Conference Room 2A', 'Main Office Floor 2, Linh Trung Ward, Thu Duc City', 10.77221500, 106.65780000, 2, 'main-office-f2-conference-2a'),
            (1008, 1002, 1001, 'Focus Workspace', 'Main Office Floor 2, Linh Trung Ward, Thu Duc City', 10.77221500, 106.65807000, 2, 'main-office-f2-focus')
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
            (1001, 1001, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4.2,"rings":[[[106.65762,10.77194],[106.65786,10.77194],[106.65786,10.77212],[106.65762,10.77212],[106.65762,10.77194]]]}$json$),
            (1002, 1002, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4.2,"rings":[[[106.65762,10.77212],[106.65798,10.77212],[106.65798,10.77231],[106.65762,10.77231],[106.65762,10.77212]]]}$json$),
            (1003, 1003, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4.2,"rings":[[[106.65798,10.77212],[106.65816,10.77212],[106.65816,10.77231],[106.65798,10.77231],[106.65798,10.77212]]]}$json$),
            (1004, 1004, 'room', 'polygon', $json${"floor_id":1001,"altitude_min":0,"altitude_max":4.2,"rings":[[[106.65786,10.77194],[106.65816,10.77194],[106.65816,10.77212],[106.65786,10.77212],[106.65786,10.77194]]]}$json$),
            (1005, 1005, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4.2,"altitude_max":8.4,"rings":[[[106.65762,10.77194],[106.65786,10.77194],[106.65786,10.77212],[106.65762,10.77212],[106.65762,10.77194]]]}$json$),
            (1006, 1006, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4.2,"altitude_max":8.4,"rings":[[[106.65786,10.77194],[106.65816,10.77194],[106.65816,10.77212],[106.65786,10.77212],[106.65786,10.77194]]]}$json$),
            (1007, 1007, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4.2,"altitude_max":8.4,"rings":[[[106.65762,10.77212],[106.65798,10.77212],[106.65798,10.77231],[106.65762,10.77231],[106.65762,10.77212]]]}$json$),
            (1008, 1008, 'room', 'polygon', $json${"floor_id":1002,"altitude_min":4.2,"altitude_max":8.4,"rings":[[[106.65798,10.77212],[106.65816,10.77212],[106.65816,10.77231],[106.65798,10.77231],[106.65798,10.77212]]]}$json$)
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
            (1001, 1001, 16.00, 0.00, 4.20, true, true, true, 1001),
            (1002, 1002, 20.00, 0.00, 4.20, true, true, true, 1001),
            (1003, 1003, 12.00, 0.00, 4.20, true, true, true, 1001),
            (1004, 1004, 14.00, 0.00, 4.20, true, true, true, 1001),
            (1005, 1005, 12.00, 4.20, 8.40, true, true, true, 1001),
            (1006, 1006, 14.00, 4.20, 8.40, true, true, true, 1001),
            (1007, 1007, 18.00, 4.20, 8.40, true, true, true, 1001),
            (1008, 1008, 14.00, 4.20, 8.40, true, true, true, 1001)
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
            (1001, 1001, 'main-office-f1-reception-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1001', true),
            (1002, 1002, 'main-office-f1-engineering-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1002', true),
            (1003, 1003, 'main-office-f1-meeting-1a-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1003', true),
            (1004, 1004, 'main-office-f1-checkin-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1004', true),
            (1005, 1005, 'main-office-f2-hr-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1005', true),
            (1006, 1006, 'main-office-f2-management-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1006', true),
            (1007, 1007, 'main-office-f2-conference-2a-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1007', true),
            (1008, 1008, 'main-office-f2-focus-layer', 'indoor-room', 'testing/main_office_gis_data.json#cell-space-1008', true)
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
            (1001, 1001, 10.77203000, 106.65774000, 0.60, 'entrance'),
            (1002, 1004, 10.77203000, 106.65801000, 0.60, 'checkin-kiosk'),
            (1003, 1002, 10.77221500, 106.65780000, 0.60, 'work-zone'),
            (1004, 1007, 10.77221500, 106.65780000, 4.80, 'conference'),
            (1005, 1005, 10.77203000, 106.65774000, 4.80, 'hr-desk'),
            (1006, 1006, 10.77203000, 106.65801000, 4.80, 'management-desk'),
            (1007, 1008, 10.77221500, 106.65807000, 4.80, 'focus-zone')
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
            (1001, 1001, 1002, 'hallway', 26.00),
            (1002, 1002, 1003, 'hallway', 34.00),
            (1003, 1003, 1004, 'stairs', 16.00),
            (1004, 1004, 1005, 'hallway', 28.00),
            (1005, 1005, 1006, 'hallway', 26.00),
            (1006, 1006, 1007, 'hallway', 30.00)
        ON CONFLICT (transition_id) DO UPDATE SET
            from_state_id = EXCLUDED.from_state_id,
            to_state_id = EXCLUDED.to_state_id,
            transition_type = EXCLUDED.transition_type,
            distance_m = EXCLUDED.distance_m;

        UPDATE business.attendance_record
        SET latitude = CASE record_id
                WHEN 1001 THEN 10.772215
                WHEN 1002 THEN 10.772215
                WHEN 1003 THEN 10.772030
                WHEN 1004 THEN 10.772030
                WHEN 1005 THEN 10.772215
            END,
            longitude = CASE record_id
                WHEN 1001 THEN 106.657800
                WHEN 1002 THEN 106.657800
                WHEN 1003 THEN 106.657740
                WHEN 1004 THEN 106.658010
                WHEN 1005 THEN 106.657800
            END,
            altitude = CASE record_id
                WHEN 1001 THEN 0.80
                WHEN 1002 THEN 0.90
                WHEN 1003 THEN 4.80
                WHEN 1004 THEN 0.70
                WHEN 1005 THEN 4.80
            END
        WHERE record_id IN (1001, 1002, 1003, 1004, 1005);
    """)


def downgrade() -> None:
    op.get_bind().exec_driver_sql("""
        UPDATE gis.building
        SET name = 'AMA Two-Floor Office',
            address = '1 ArcGIS Demo Street, Ho Chi Minh City',
            center_lat = 10.77687500,
            center_lng = 106.70081500,
            total_floors = 2,
            arcgis_layer_id = 'ama-hq-building'
        WHERE building_id = 1001;
    """)
