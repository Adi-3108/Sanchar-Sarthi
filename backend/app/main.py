from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analytics import router as analytics_router
from app.api.routes_admin import router as admin_router
from app.api.routes_command_center import router as command_center_router
from app.api.routes_datasets import router as datasets_router
from app.api.routes_demo import router as demo_router
from app.api.routes_events import router as events_router
from app.api.routes_foundation import router as foundation_router
from app.api.routes_health import router as health_router
from app.api.routes_live_updates import router as live_updates_router
from app.api.routes_map import router as map_router
from app.api.routes_officer import router as officer_router
from app.api.routes_post_event import router as post_event_router
from app.api.routes_rag import router as rag_router
from app.api.routes_recommendations import router as recommendations_router
from app.api.routes_reports import router as reports_router
from app.api.routes_translation import router as translation_router
from app.api.routes_auth import router as auth_router
from app.api import routes_analytics_corridor
from app.core.config import get_settings
from app.core.firebase import initialize_firebase
from app.db.base import import_model_modules
from app.services.rag_indexer_service import periodic_live_update_index_loop

settings = get_settings()


from app.background_route_fetcher import _fetch_routes_loop
import asyncio

@asynccontextmanager
async def lifespan(_: FastAPI):
    import_model_modules()
    initialize_firebase(settings)
    tasks = [asyncio.create_task(_fetch_routes_loop())]
    if settings.rag_enabled:
        tasks.append(asyncio.create_task(periodic_live_update_index_loop()))
    yield
    for task in tasks:
        task.cancel()
    for task in tasks:
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(command_center_router)
app.include_router(foundation_router)
app.include_router(admin_router)
app.include_router(datasets_router)
app.include_router(demo_router)
app.include_router(analytics_router)
app.include_router(events_router)
app.include_router(live_updates_router)
app.include_router(map_router)
app.include_router(officer_router)
app.include_router(post_event_router)
app.include_router(rag_router)
app.include_router(recommendations_router)
app.include_router(reports_router)
app.include_router(translation_router)
app.include_router(routes_analytics_corridor.router)
app.include_router(auth_router)
