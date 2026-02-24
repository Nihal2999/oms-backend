from pydantic import BaseModel, ConfigDict, Field
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    status: OrderStatus

    model_config = ConfigDict(from_attributes=True)