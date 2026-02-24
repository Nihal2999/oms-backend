from fastapi import APIRouter, Depends
from app.services.product_service import ProductService
from app.repository.product import ProductRepository
from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.models.user import User
from app.core.security import get_admin_user

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(db=Depends(get_db)):
    return ProductService(ProductRepository(db))


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_admin_user),
):
    return service.create_product(product)


@router.get("/", response_model=list[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    service: ProductService = Depends(get_product_service),
):
    return service.get_products(skip, limit, search)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    return service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_admin_user),
):
    return service.update_product(product_id, product)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_admin_user),
):
    service.delete_product(product_id)
    return {"message": "Product deleted successfully"}


@router.put("/{product_id}/restore", response_model=ProductResponse)
def restore_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_admin_user),
):
    return service.restore_product(product_id)