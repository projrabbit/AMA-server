from fastapi import APIRouter

from app.api.v1.endpoints import auth, audit_logs, buildings, departments, devices, employees, floors, geofences, shifts
from app.api.v1.endpoints.face import employee_face_router, internal_face_router

api_router = APIRouter()

api_router.include_router(auth.router,              prefix="/auth",        tags=["authentication"])
api_router.include_router(employees.router,         prefix="/employees",   tags=["employees"])
api_router.include_router(employee_face_router,     prefix="/employees",   tags=["face-verification"])
api_router.include_router(departments.router,       prefix="/departments", tags=["departments"])
api_router.include_router(shifts.router,            prefix="/shifts",      tags=["shifts"])
api_router.include_router(devices.router,           prefix="/devices",     tags=["devices"])
api_router.include_router(buildings.router,         prefix="/buildings",   tags=["geofence"])
api_router.include_router(floors.router,            prefix="/floors",      tags=["geofence"])
api_router.include_router(geofences.router,         prefix="/geofences",   tags=["geofence"])
api_router.include_router(audit_logs.router,        prefix="/audit-logs",  tags=["audit"])
api_router.include_router(internal_face_router,     prefix="/internal",    tags=["internal"])
