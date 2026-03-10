from app.routers.campaign_router import router as campaign_router
from app.routers.job_router import router as job_router
from app.routers.results_router import router as results_router
from app.routers.upload_router import router as upload_router

__all__ = [
	"campaign_router",
	"job_router",
	"results_router",
	"upload_router",
]
