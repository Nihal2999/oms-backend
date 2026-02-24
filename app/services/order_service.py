from app.models.order import OrderStatus
from app.repository.order import OrderRepository
from app.core.exceptions import (
    OrderNotFoundException,
    ProductNotFoundException,
    InsufficientStockException,
    OrderAlreadyCancelledException,
    InvalidOrderStatusTransitionException,
)


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    # -------------------------
    # Create Order
    # -------------------------

    def create_order(self, user_id: int, product_id: int, quantity: int):
        product = self.repository.get_product_for_update(product_id)

        if not product:
            raise ProductNotFoundException("Product not found")

        if product.stock < quantity:
            raise InsufficientStockException("Not enough stock")

        product.stock -= quantity

        return self.repository.create_order(user_id, product_id, quantity)

    # -------------------------
    # Get Orders
    # -------------------------

    def get_my_orders(self, user_id: int):
        return self.repository.get_by_user(user_id)

    def get_all_orders(self):
        return self.repository.get_all()

    # -------------------------
    # Update Status (Admin)
    # -------------------------

    def update_status(self, order_id: int, new_status: OrderStatus):
        order = self.repository.get_by_id(order_id)

        if not order:
            raise OrderNotFoundException("Order not found")

        if order.status == OrderStatus.cancelled:
            raise OrderAlreadyCancelledException("Order already cancelled")

        if order.status == OrderStatus.delivered:
            raise InvalidOrderStatusTransitionException(
                "Delivered orders cannot be modified"
            )

        if new_status == OrderStatus.cancelled:
            order.product.stock += order.quantity

        order.status = new_status
        self.repository.commit()

        return order

    # -------------------------
    # Cancel Order
    # -------------------------

    def cancel_order(self, order_id: int, current_user):
        order = self.repository.get_by_id(order_id)

        if not order:
            raise OrderNotFoundException("Order not found")

        if current_user.role != "admin" and order.user_id != current_user.id:
            raise InvalidOrderStatusTransitionException("Not authorized")

        if order.status == OrderStatus.cancelled:
            raise OrderAlreadyCancelledException("Already cancelled")

        if order.status in [OrderStatus.shipped, OrderStatus.delivered]:
            raise InvalidOrderStatusTransitionException(
                "Cannot cancel shipped/delivered order"
            )

        order.product.stock += order.quantity
        order.status = OrderStatus.cancelled

        self.repository.commit()