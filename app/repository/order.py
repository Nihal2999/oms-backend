from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.product import Product
from app.models.order import OrderStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------
    # Order Queries
    # ------------------------

    def get_by_id(self, order_id: int):
        return (
            self.db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

    def get_all(self):
        return self.db.query(Order).all()

    def get_by_user(self, user_id: int):
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .all()
        )

    # ------------------------
    # Product Queries
    # ------------------------

    def get_product_for_update(self, product_id: int):
        return (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )

    # ------------------------
    # Mutations
    # ------------------------

    def create_order(self, user_id: int, product_id: int, quantity: int):
        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            status=OrderStatus.pending,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()