from sqlalchemy.orm import Session
from app.models.product_model import Product

class ProductRepository:

    def __init__(self, db: Session):
        self.db = db


    def create(self, data: dict) -> Product:
        product = Product(**data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product


    def get_by_id(self, product_id: int, include_deleted: bool = False) -> Product | None:
        query = self.db.query(Product).filter(Product.id == product_id)

        if not include_deleted:
            query = query.filter(Product.is_deleted.is_(False))

        return query.first()


    def get_all(self, skip: int, limit: int, search: str | None) -> list[Product]:
        query = self.db.query(Product).filter(Product.is_deleted.is_(False))

        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))

        query = query.order_by(Product.id.desc())

        return query.offset(skip).limit(limit).all()


    def update(self, product: Product, update_data: dict) -> Product:
        for key, value in update_data.items():
            setattr(product, key, value)

        self.db.commit()
        self.db.refresh(product)
        return product


    def soft_delete(self, product: Product) -> None:
        product.is_deleted = True
        self.db.commit()


    def restore(self, product: Product) -> Product:
        product.is_deleted = False
        self.db.commit()
        self.db.refresh(product)
        return product