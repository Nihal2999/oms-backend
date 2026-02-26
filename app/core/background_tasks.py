import logging

logger = logging.getLogger(__name__)


def log_user_registered(user_id: int, email: str):
    logger.info(f"[BACKGROUND] New user registered - UserID: {user_id}, Email: {email}")


def log_order_created(order_id: int, user_id: int, product_id: int, quantity: int):
    logger.info(f"[BACKGROUND] Order created - OrderID: {order_id}, UserID: {user_id}, ProductID: {product_id}, Quantity: {quantity}")


def log_order_status_updated(order_id: int, new_status: str):
    logger.info(f"[BACKGROUND] Order status updated - OrderID: {order_id}, NewStatus: {new_status}")