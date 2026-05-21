# GIS Demo — Seed & Visualization

End-to-end demo that seeds a real-address building into the `gis` schema and
renders it as a 3D ArcGIS scene.

Files in this folder:

| File                          | Purpose                                                          |
| ----------------------------- | ---------------------------------------------------------------- |
| `seed_gis_demo.py`            | Idempotent Python seed: 1 building, 2 floors, 6 rooms+geofences. |
| `gis_view.html`               | ArcGIS 3D viewer (fetches API, falls back to bundled demo data). |
| `ama_hq_arcgis.html`          | Pre-existing ArcGIS viewer for the UIT mock data.                |
| `uit_building_a_gis_data.json`| Pre-existing static GIS dataset.                                 |

## Demo data shape

| Entity   | Value                                                              |
| -------- | ------------------------------------------------------------------ |
| Building | `Demo Office HCM` — 268 Ly Thuong Kiet, District 10, HCMC          |
| Center   | `10.77220, 106.65790`                                              |
| Floor 1  | altitude 0–4 m — Rooms 101 / 102 / 103                             |
| Floor 2  | altitude 4–8 m — Rooms 201 / 202 / 203                             |
| Geofence | radius 5 m around each room, all `is_active = true`, no overlap    |

## Prerequisites

- `uv` installed
- A valid Supabase / Postgres password in `AMA-server/.env`
  (copy `.env.example` and set `DATABASE_PASSWORD`)

## Step 1 — Apply migrations

From the repo root (`AMA-server/`):

```powershell
uv run alembic upgrade head
```

This creates the `business` and `gis` schemas and applies all migrations,
including the pre-existing UIT mock data.

## Step 2 — Seed the demo GIS data

```powershell
uv run python testing/seed_gis_demo.py
```

The script is idempotent — re-running it will not produce duplicates:

- Building is matched by `name = "Demo Office HCM"`.
- Floors are matched by `(building_id, floor_number)`.
- Rooms / cell spaces are matched by `(floor_id, name)`.
- Geofence rules are matched by `cell_space_id`.

Existing rows are updated in place; new rows are inserted with auto-incremented
IDs so they don't collide with the mock data from the migration.

## Step 3 — Run the backend

```powershell
uv run fastapi dev app/main.py
```

API is served at `http://127.0.0.1:8000`, Swagger UI at
`http://127.0.0.1:8000/docs`.

## Step 4 — (Optional) Get an access token

The GIS endpoints require an `hr` or `admin` role. The mock accounts seeded by
migration `c2495ccaca1b` have placeholder password hashes and can NOT be
logged into. To create a real admin in one call, use the demo-friendly
`POST /api/v1/auth/register` endpoint:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/auth/register `
     -H "Content-Type: application/json" `
     -d '{
       "username":"demo.admin@amaserver.local",
       "password":"DemoPass123!",
       "full_name":"Demo Admin",
       "email":"demo.admin@amaserver.local",
       "role":"admin",
       "department_name":"GIS Demo"
     }'
```

The response contains `data.access_token` — copy that string. Subsequent
calls log in via:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/auth/login `
     -H "Content-Type: application/json" `
     -d '{"username":"demo.admin@amaserver.local","password":"DemoPass123!"}'
```

## Step 5 — Open the viewer

```powershell
# Serve testing/ over HTTP so the browser can fetch the API + static assets.
python -m http.server 8080 -d testing
```

Then open <http://127.0.0.1:8080/gis_view.html>.

- If `API_TOKEN` at the top of `gis_view.html` is **empty**, the page renders
  the bundled fallback data — useful for sanity-checking the visual without a
  running backend.
- To fetch live data, edit the top of `gis_view.html`:

  ```js
  const API_BASE  = "http://127.0.0.1:8000/api/v1";
  const API_TOKEN = "eyJhbGciOi...";     // paste the access_token here
  const TARGET_BUILDING_NAME = "Demo Office HCM";
  ```

  The badge in the top-left panel will switch from `DEMO FALLBACK` to
  `FETCHED FROM API` once the data is loaded.

## API endpoints used by the viewer

No new endpoints were added — the viewer relies on what already exists:

| Method | Path                                                       | Used for                                   |
| ------ | ---------------------------------------------------------- | ------------------------------------------ |
| GET    | `/api/v1/buildings/?include_floors=true`                   | Building + floor list                      |
| GET    | `/api/v1/geofences/?building_id={id}&is_active=true`       | Rooms (cell spaces) + geofence rules       |

## Verify the data in Supabase

In the Supabase SQL editor:

```sql
SELECT b.building_id, b.name, b.center_lat, b.center_lng,
       count(DISTINCT f.floor_id)      AS floors,
       count(DISTINCT cs.cell_space_id) AS rooms
FROM   gis.building b
LEFT JOIN gis.floor      f  ON f.building_id  = b.building_id
LEFT JOIN gis.cell_space cs ON cs.building_id = b.building_id
WHERE  b.name = 'Demo Office HCM'
GROUP BY b.building_id;

SELECT cs.name, cs.center_lat, cs.center_lng,
       gr.allowed_radius_m, gr.altitude_min, gr.altitude_max, gr.is_active
FROM   gis.cell_space   cs
JOIN   gis.geofence_rule gr ON gr.cell_space_id = cs.cell_space_id
JOIN   gis.building     b  ON b.building_id    = cs.building_id
WHERE  b.name = 'Demo Office HCM'
ORDER  BY cs.floor_id, cs.name;
```

## Tests

The existing unit tests don't hit the database, so they run independently of
the seed:

```powershell
uv run pytest tests/ -v
```
