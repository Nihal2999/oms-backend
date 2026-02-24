from app.repository.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.exceptions import (
    ProductNotFoundException,
    ProductNotDeletedException,
)


class ProductService:
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository


    def create_product(self, product_data: ProductCreate):
        return self.repository.create(product_data.model_dump())


    def get_products(self, skip: int, limit: int, search: str | None):
        return self.repository.get_all(skip, limit, search)


    def get_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)

        if not product:
            raise ProductNotFoundException("Product not found")

        return product


    def update_product(self, product_id: int, update_data: ProductUpdate):
        product = self.repository.get_by_id(product_id)

        if not product:
            raise ProductNotFoundException("Product not found")

        return self.repository.update(
            product,
            update_data.model_dump(exclude_unset=True),
        )


    def delete_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)

        if not product:
            raise ProductNotFoundException("Product not found")

        self.repository.soft_delete(product)


    def restore_product(self, product_id: int):
        product = self.repository.get_by_id(product_id, include_deleted=True)

        if not product:
            raise ProductNotFoundException("Product not found")

        if not product.is_deleted:
            raise ProductNotDeletedException("Product is not deleted")

        return self.repository.restore(product)