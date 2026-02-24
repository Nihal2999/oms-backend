from app.services.product_service import ProductService
from app.repository.product import ProductRepository
from app.schemas.product import ProductCreate
import pytest


def test_create_product_service(db):
    repo = ProductRepository(db)
    service = ProductService(repo)

    product_data = ProductCreate(
        name="Phone",
        description="Smartphone",
        price=500,
        stock=5
    )

    product = service.create_product(product_data)

    assert product.id is not None
    assert product.name == "Phone"
    assert product.stock == 5