"""Main FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.database import init_db, close_db
from app.api import products as products_router
from app.api import contribution as contribution_router
from app.api import chat as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="PickBetter API",
    description="API for the PickBetter nutrition app",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Get allowed origins from environment or use defaults
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
custom_origins = [o.strip() for o in allowed_origins_str.split(",")] if allowed_origins_str else []

base_origins = [
    "http://localhost:3000",
    "http://localhost:3005",
    "http://localhost:3006",
    "http://localhost:3007",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3005",
    "http://127.0.0.1:3006",
    "http://127.0.0.1:3007",
    "http://192.0.0.2:3000",
    "http://192.168.1.6:3000",
]

# In production, sometimes Vercel generates dynamic preview URLs
# For a public API it's safe to use a wildcard or a regex if needed,
# but we will just pass down the exact Vercel URL in production via ENV.
all_origins = base_origins + custom_origins

# If the user sets ALLOWED_ORIGINS=*, we must allow all
if "*" in all_origins:
    all_origins = ["*"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Import user router
from app.api import user as user_router
from app.api import auth as auth_router

# Add routers
app.include_router(
    auth_router.router,
    prefix="/api/v1",
    tags=["authentication"]
)

app.include_router(
    products_router.router,
    prefix="/api/v1",
    tags=["products"]
)

app.include_router(
    contribution_router.router,
    prefix="/api/v1",
    tags=["contribution"]
)

app.include_router(
    chat_router.router,
    prefix="/api/v1",
    tags=["chat"]
)

app.include_router(
    user_router.router,
    prefix="/api/v1",
    tags=["user"]
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "pickbetter-api",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the PickBetter API!",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "openapi_spec": "/api/openapi.json"
    }

# This allows running with `python -m app.main`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level="info"
    )