import logging
from app.repository.product_repo import ProductRepository
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.core.exceptions import (
    ProductNotFoundException,
    ProductNotDeletedException,
)

logger = logging.getLogger(__name__)

class ProductService:

    def __init__(self, repository: ProductRepository):
        self.repository = repository


    def create_product(self, product_data: ProductCreate):
        product = self.repository.create(product_data.model_dump())
        logger.info(f"Product created successfully - ID: {product.id}, Name: {product_data.name}, Price: {product_data.price}")
        return product


    def get_products(self, skip: int, limit: int, search: str | None):
        return self.repository.get_all(skip, limit, search)


    def get_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)

        if not product:
            logger.warning(f"Get product attempt for non-existent product: {product_id}")
            raise ProductNotFoundException("Product not found")

        logger.info(f"Product retrieved - ID: {product_id}")
        return product


    def update_product(self, product_id: int, update_data: ProductUpdate):
        product = self.repository.get_by_id(product_id)

        if not product:
            logger.warning(f"Update attempt for non-existent product: {product_id}")
            raise ProductNotFoundException("Product not found")

        updated_product = self.repository.update(
            product,
            update_data.model_dump(exclude_unset=True),
        )
        logger.info(f"Product updated successfully - ID: {product_id}")
        return updated_product


    def delete_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)

        if not product:
            logger.warning(f"Delete attempt for non-existent product: {product_id}")
            raise ProductNotFoundException("Product not found")

        self.repository.soft_delete(product)
        logger.info(f"Product soft deleted successfully - ID: {product_id}")


    def restore_product(self, product_id: int):
        product = self.repository.get_by_id(product_id, include_deleted=True)

        if not product:
            logger.warning(f"Restore attempt for non-existent product: {product_id}")
            raise ProductNotFoundException("Product not found")

        if not product.is_deleted:
            logger.warning(f"Restore attempt for non-deleted product: {product_id}")
            raise ProductNotDeletedException("Product is not deleted")

        restored_product = self.repository.restore(product)
        logger.info(f"Product restored successfully - ID: {product_id}")
        return restored_product