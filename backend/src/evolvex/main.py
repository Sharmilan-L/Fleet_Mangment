from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from evolvex.api.fleet import router as fleet_router
from evolvex.api.health import router as health_router
from evolvex.api.simulator import router as simulator_router
from evolvex.api.telemetry import router as telemetry_router
from evolvex.api.trips import router as trips_router
from evolvex.core.config import settings
from evolvex.core.database import close_engine
from evolvex.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from evolvex.core.logging import logger, setup_logging
from evolvex.core.middleware import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup logging and clean shutdown disposal of SQLAlchemy engine.
    """
    setup_logging()
    logger.info("Initializing EvolveX API foundation")
    yield
    logger.info("Closing database engine resources during shutdown")
    await close_engine()


def create_app() -> FastAPI:
    """
    FastAPI Application Factory.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware registration (Order matters: RequestID first)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Router Inclusion
    app.include_router(health_router)
    app.include_router(telemetry_router)
    app.include_router(fleet_router)
    app.include_router(trips_router)
    app.include_router(simulator_router)

    return app


app = create_app()
