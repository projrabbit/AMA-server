# ArcGIS Layer ID Validation — Deferred

`app/services/geofence_service.py::_validate_arcgis_layer` currently accepts
any non-empty string as a valid `arcgis_layer_id`. This is a deliberate stub
so building / floor / geofence creation does not require an outbound HTTP
call to ArcGIS Online during local development and tests.

## What the real validation should do

When ArcGIS access is wired up, replace the stub body with a probe:

1. Resolve the layer URL from configuration (the ArcGIS service base URL +
   layer ID).
2. Issue `GET <baseUrl>/MapServer/<layer_id>?f=json` against the ArcGIS
   REST endpoint.
3. Treat the layer as valid only if HTTP 200 **and** the JSON body lacks an
   `error` key. ArcGIS returns 200 with `{"error": {...}}` for unknown IDs,
   so don't trust status alone.
4. Cache the result (Redis, ~5 minutes) keyed by layer ID — a layer's
   existence rarely changes and every building/floor write would otherwise
   hit ArcGIS.
5. Surface failures as the existing `INVALID_ARCGIS_LAYER` HTTP 400 to keep
   the API envelope stable for clients.

## Why this is deferred

- The demo viewer (`testing/gis_view.html`) uses the ArcGIS JavaScript API
  client-side; it does not need server-side layer validation to render.
- Tests rely on the stub passing so the existing 53 geofence tests don't
  need network access.
- Adding HTTP calls inside a synchronous endpoint without async + caching
  would slow create operations from <50 ms to >300 ms.

## When to revisit

When the seeded `arcgis_layer_id` values (currently strings like
`"demo-office-hcm"` or `"uit-building-a-f1-lobby"`) are migrated to real
ArcGIS Online layer IDs and an ArcGIS API key is provisioned for the
backend. Track that work as part of Module 3 (Geofence) completion.
