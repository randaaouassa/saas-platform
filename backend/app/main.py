from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.idempotency import IdempotencyMiddleware
from app.core.logging import configure_logging, get_logger
from app.core.metrics import metrics_response
from app.core.middleware import RequestIDMiddleware
from app.core.otel import setup_tracing
from app.core.rate_limit import RateLimitMiddleware
from app.modules.deliveries.router import router as deliveries_router
from app.modules.identity.router import router as auth_router
from app.modules.inventory.router import router as inventory_router
from app.modules.orders.router import customers_router
from app.modules.orders.router import router as orders_router
from app.modules.warehouse.router import router as warehouse_router

configure_logging()
setup_tracing()
log = get_logger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("startup", env=settings.ENV, app=settings.APP_NAME)
    yield
    log.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "prod" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(warehouse_router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(deliveries_router, prefix=settings.API_V1_PREFIX)


@app.get("/health/live", tags=["system"])
def liveness() -> dict:
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def readiness() -> dict:
    return {"status": "ready"}


@app.get("/metrics", tags=["system"])
def metrics():
    return metrics_response()


@app.get(f"{settings.API_V1_PREFIX}/ping", tags=["system"])
def ping() -> dict:
    return {"pong": True}