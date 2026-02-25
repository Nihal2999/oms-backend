import logging
from app.models.order_model import OrderStatus
from app.models.user_model import UserRole
from app.repository.order_repo import OrderRepository
from app.core.exceptions import (
    OrderNotFoundException,
    ProductNotFoundException,
    InsufficientStockException,
    OrderAlreadyCancelledException,
    InvalidOrderStatusTransitionException,
)

logger = logging.getLogger(__name__)

class OrderService:

    def __init__(self, repository: OrderRepository):
        self.repository = repository


    def create_order(self, user_id: int, product_id: int, quantity: int):
        product = self.repository.get_product_for_update(product_id)

        if not product:
            logger.warning(f"Order creation failed - product not found: {product_id}, user: {user_id}")
            raise ProductNotFoundException("Product not found")

        if product.stock < quantity:
            logger.warning(f"Order creation failed - insufficient stock: product {product_id}, requested {quantity}, available {product.stock}")
            raise InsufficientStockException("Not enough stock")

        product.stock -= quantity

        order = self.repository.create_order(user_id, product_id, quantity)
        logger.info(f"Order created successfully - OrderID: {order.id}, UserID: {user_id}, ProductID: {product_id}, Quantity: {quantity}")
        return order


    def get_my_orders(self, user_id: int):
        return self.repository.get_by_user(user_id)


    def get_all_orders(self):
        return self.repository.get_all()


    def update_status(self, order_id: int, new_status: OrderStatus):
        order = self.repository.get_by_id_with_relations(order_id)

        if not order:
            logger.warning(f"Update status failed - order not found: {order_id}")
            raise OrderNotFoundException("Order not found")

        if order.status == OrderStatus.cancelled:
            logger.warning(f"Update status failed - order already cancelled: {order_id}")
            raise OrderAlreadyCancelledException("Order already cancelled")

        if order.status == OrderStatus.delivered:
            logger.warning(f"Update status failed - delivered order cannot be modified: {order_id}")
            raise InvalidOrderStatusTransitionException(
                "Delivered orders cannot be modified"
            )

        if new_status == OrderStatus.cancelled:
            
            product = self.repository.get_product_for_update(order.product_id)

            if not product:
                raise ProductNotFoundException(400, "Product for this order does not exist")

            product.stock = product.stock + order.quantity

        #    order.product.stock += order.quantity
            logger.info(f"Order status updated to CANCELLED - OrderID: {order_id}, stock restored: {order.quantity}")
        else:
            logger.info(f"Order status updated - OrderID: {order_id}, new status: {new_status.value}")

        order.status = new_status
        self.repository.commit()

        return order


    def cancel_order(self, order_id: int, current_user):
        order = self.repository.get_by_id(order_id)

        if not order:
            logger.warning(f"Cancel order failed - order not found: {order_id}")
            raise OrderNotFoundException("Order not found")

        if current_user.role != UserRole.admin and order.user_id != current_user.id:
            logger.warning(f"Cancel order failed - unauthorized: user {current_user.id} tried to cancel order {order_id} of user {order.user_id}")
            raise InvalidOrderStatusTransitionException("Not authorized")

        if order.status == OrderStatus.cancelled:
            logger.warning(f"Cancel order failed - order already cancelled: {order_id}")
            raise OrderAlreadyCancelledException("Already cancelled")

        if order.status in [OrderStatus.shipped, OrderStatus.delivered]:
            logger.warning(f"Cancel order failed - order cannot be cancelled: {order_id}, current status: {order.status.value}")
            raise InvalidOrderStatusTransitionException(
                "Cannot cancel shipped/delivered order"
            )

        order.product.stock += order.quantity
        order.status = OrderStatus.cancelled

        self.repository.commit()
        logger.info(f"Order cancelled successfully - OrderID: {order_id}, cancelled by user: {current_user.id}, stock restored: {order.quantity}")
        return order