from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import logging, setup_logging
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
)

logger = logging.getLogger(__name__)

# Setup logging first
setup_logging()

app = FastAPI(
    title="Order Management System",
    version="1.0.0",
    description="Backend API for OMS built with FastAPI"
)

# Routers
app.include_router(users_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "OMS Backend Running Successfully"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

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
    
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)