from app.routers.campaign_router import router as campaign_router
from app.routers.config_router import router as config_router
from app.routers.database_router import router as database_router
from app.routers.demo_router import router as demo_router
from app.routers.events_router import router as events_router
from app.routers.job_router import router as job_router
from app.routers.provider_router import router as provider_router
from app.routers.region_router import router as region_router
from app.routers.results_router import router as results_router
from app.routers.session_router import router as session_router
from app.routers.upload_router import router as upload_router

__all__ = [
    "campaign_router",
    "config_router",
    "database_router",
    "demo_router",
    "events_router",
    "job_router",
    "provider_router",
    "region_router",
    "results_router",
    "session_router",
    "upload_router",
]
