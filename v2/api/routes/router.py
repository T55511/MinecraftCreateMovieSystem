from fastapi import APIRouter

from .projects import router as projects_router
from .project_tasks import router as project_tasks_router
from .timer import router as timer_router
from .dashboard import router as dashboard_router
from .admin_audit import router as admin_audit_router
from .master_status import router as master_status_router

router = APIRouter()

router.include_router(projects_router)
router.include_router(project_tasks_router)
router.include_router(timer_router)
router.include_router(dashboard_router)
router.include_router(admin_audit_router)
router.include_router(master_status_router)
