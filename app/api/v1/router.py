from fastapi import APIRouter

from app.api.v1.endpoints import auth, audit_logs, buildings, departments, devices, employees, floors, geofences, shifts
from app.api.v1.endpoints.report import dashboard_router, realtime_router, reports_router
from app.api.v1.endpoints.attendance import router as attendance_router
from app.api.v1.endpoints.face import employee_face_router, internal_face_router
from app.api.v1.endpoints.fraud import fraud_router, internal_fraud_router
from app.api.v1.endpoints.notifications import notification_router, internal_notification_router

api_router = APIRouter()

api_router.include_router(auth.router,              prefix="/auth",        tags=["authentication"])
api_router.include_router(attendance_router,        prefix="/attendance",  tags=["attendance"])
api_router.include_router(employees.router,         prefix="/employees",   tags=["employees"])
api_router.include_router(employee_face_router,     prefix="/employees",   tags=["face-verification"])
api_router.include_router(departments.router,       prefix="/departments", tags=["departments"])
api_router.include_router(shifts.router,            prefix="/shifts",      tags=["shifts"])
api_router.include_router(devices.router,           prefix="/devices",     tags=["devices"])
api_router.include_router(buildings.router,         prefix="/buildings",   tags=["geofence"])
api_router.include_router(floors.router,            prefix="/floors",      tags=["geofence"])
api_router.include_router(geofences.router,         prefix="/geofences",   tags=["geofence"])
api_router.include_router(audit_logs.router,        prefix="/audit-logs",  tags=["audit"])
api_router.include_router(fraud_router,             prefix="/fraud",       tags=["fraud-detection"])
api_router.include_router(internal_face_router,     prefix="/internal",    tags=["internal"])
api_router.include_router(internal_fraud_router,       prefix="/internal",       tags=["internal"])
api_router.include_router(notification_router,         prefix="/notifications",  tags=["notifications"])
api_router.include_router(internal_notification_router, prefix="/internal",      tags=["internal"])
api_router.include_router(dashboard_router,              prefix="/dashboard",   tags=["report"])
api_router.include_router(realtime_router,               prefix="/realtime",    tags=["report"])
api_router.include_router(reports_router,                prefix="/reports",     tags=["report"])
