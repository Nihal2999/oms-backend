from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import logging, setup_logging
from app.core.config import settings
from app.db.database import initialize_db, shutdown_db
from app.api.v1.users import router as users_router
from app.api.v1.products import router as products_router
from app.api.v1.orders import router as orders_router

from app.core.exceptions import (
    ProductNotFoundException,
    OrderNotFoundException,
    InsufficientStockException,
    OrderAlreadyCancelledException,
    InvalidOrderStatusTransitionException,
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UnauthorizedException,
    ProductNotDeletedException,
)

logger = logging.getLogger(__name__)

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OMS Backend application")
    initialize_db()
    yield
    logger.info("Shutting down OMS Backend application")
    shutdown_db()


app = FastAPI(
    title="OMS - Order Management System",
    description="Backend API for OMS built with FastAPI",
    lifespan=lifespan,
    docs_url="/openmyapi",
    redoc_url="/test",
)


app.include_router(users_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")


@app.exception_handler(ProductNotFoundException)
async def product_not_found_handler(request: Request, exc: ProductNotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(OrderNotFoundException)
async def order_not_found_handler(request: Request, exc: OrderNotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InsufficientStockException)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(OrderAlreadyCancelledException)
async def order_cancelled_handler(request: Request, exc: OrderAlreadyCancelledException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidOrderStatusTransitionException)
async def invalid_status_handler(request: Request, exc: InvalidOrderStatusTransitionException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ProductNotDeletedException)
async def product_not_deleted_handler(request: Request, exc: ProductNotDeletedException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UserAlreadyExistsException)
async def user_exists_handler(request: Request, exc: UserAlreadyExistsException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidCredentialsException)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)