from fastapi import APIRouter, Depends
from app.services.order_service import OrderService
from app.repository.order_repo import OrderRepository
from app.db.database import get_db
from app.schemas.order_schema import OrderCreate, OrderResponse, OrderUpdate
from app.core.security import get_current_user, get_admin_user
from app.models.user_model import User

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(db=Depends(get_db)):
    return OrderService(OrderRepository(db))


@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    return service.create_order(
        current_user.id,
        order.product_id,
        order.quantity,
    )


@router.get("/me", response_model=list[OrderResponse])
def get_my_orders(
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_my_orders(current_user.id)


@router.get("/", response_model=list[OrderResponse])
def get_all_orders(
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_admin_user),
):
    return service.get_all_orders()


@router.put("/{order_id}", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_admin_user),
):
    return service.update_status(order_id, order_update.status)


@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    service.cancel_order(order_id, current_user)
    return {"message": "Order cancelled successfully"}