from sqlalchemy.orm import Session, joinedload
from app.models.order_model import Order, OrderStatus
from app.models.product_model import Product

class OrderRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_by_id(self, order_id: int) -> Order | None:
        return (
            self.db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )


    def get_by_id_with_relations(self, order_id: int) -> Order | None:
        return (
            self.db.query(Order)
            .options(joinedload(Order.product))
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )


    def get_all(self) -> list[Order]:
        return self.db.query(Order).all()


    def get_by_user(self, user_id: int) -> list[Order]:
        return (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .all()
        )


    def get_product_for_update(self, product_id: int) -> Product | None:
        return (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )


    def create_order(self, user_id: int, product_id: int, quantity: int) -> Order:
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


    def commit(self) -> None:
        self.db.commit()


    def rollback(self) -> None:
        self.db.rollback()