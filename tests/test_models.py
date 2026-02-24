from decimal import Decimal
from app.models.user_model import User, UserRole
from app.models.product_model import Product
from app.models.order_model import Order, OrderStatus

class TestUserModel:

    def test_user_creation(self, admin_user):
        assert admin_user.id is not None
        assert admin_user.name == "Admin User"
        assert admin_user.email == "admin@example.com"
        assert admin_user.role == UserRole.admin
        assert admin_user.hashed_password is not None

    def test_user_default_role(self, db):
        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_pwd"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.role == UserRole.user

    def test_user_role_enum(self):
        assert UserRole.admin.value == "admin"
        assert UserRole.user.value == "user"

    def test_user_phone_optional(self, db):
        user = User(
            name="No Phone User",
            email="nophone@example.com",
            hashed_password="hashed_pwd"
        )
        assert user.phone is None

    def test_user_phone_set(self, regular_user):
        assert regular_user.phone == "+0987654321"

    def test_user_relationship_with_orders(self, db, regular_user, product_in_stock):
        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        db.add(order)
        db.commit()

        db.refresh(regular_user)
        assert len(regular_user.orders) == 1
        assert regular_user.orders[0].id == order.id


class TestProductModel:

    def test_product_creation(self, product_in_stock):
        assert product_in_stock.id is not None
        assert product_in_stock.name == "Laptop"
        assert product_in_stock.description == "High-performance laptop"
        assert product_in_stock.price == Decimal("999.99")
        assert product_in_stock.stock == 10

    def test_product_deleted_default_false(self, db):
        product = Product(
            name="New Product",
            description="Test",
            price=Decimal("10.00"),
            stock=5
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        assert product.is_deleted is False

    def test_product_stock_default_zero(self, db):
        product = Product(
            name="No Stock Product",
            description="Test",
            price=Decimal("25.00")
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        assert product.stock == 0

    def test_product_price_decimal_precision(self, db):
        product = Product(
            name="Price Test",
            description="Test",
            price=Decimal("99.99"),
            stock=1
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        assert product.price == Decimal("99.99")

    def test_product_stock_manipulation(self, product_in_stock):
        original_stock = product_in_stock.stock
        product_in_stock.stock -= 2
        assert product_in_stock.stock == original_stock - 2

    def test_product_soft_delete_flag(self, deleted_product):
        assert deleted_product.is_deleted is True

    def test_product_relationship_with_orders(self, db, regular_user, product_in_stock):
        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=2,
            status=OrderStatus.pending
        )
        db.add(order)
        db.commit()

        db.refresh(product_in_stock)
        assert len(product_in_stock.orders) == 1
        assert product_in_stock.orders[0].id == order.id


class TestOrderModel:

    def test_order_creation(self, pending_order):
        assert pending_order.id is not None
        assert pending_order.user_id is not None
        assert pending_order.product_id is not None
        assert pending_order.quantity == 2
        assert pending_order.status == OrderStatus.pending

    def test_order_default_status(self, db, regular_user, product_in_stock):
        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        assert order.status == OrderStatus.pending

    def test_order_status_enum(self):
        assert OrderStatus.pending.value == "pending"
        assert OrderStatus.shipped.value == "shipped"
        assert OrderStatus.delivered.value == "delivered"
        assert OrderStatus.cancelled.value == "cancelled"

    def test_order_all_statuses(self, db, regular_user, product_in_stock):
        statuses = [
            OrderStatus.pending,
            OrderStatus.shipped,
            OrderStatus.delivered,
            OrderStatus.cancelled
        ]

        for status in statuses:
            order = Order(
                user_id=regular_user.id,
                product_id=product_in_stock.id,
                quantity=1,
                status=status
            )
            db.add(order)

        db.commit()
        orders = db.query(Order).all()
        assert len(orders) == 4

    def test_order_user_relationship(self, pending_order, regular_user):
        assert pending_order.user_id == regular_user.id
        assert pending_order.user.id == regular_user.id

    def test_order_product_relationship(self, pending_order, product_in_stock):
        assert pending_order.product_id == product_in_stock.id
        assert pending_order.product.id == product_in_stock.id

    def test_order_quantity_positive(self, pending_order):
        assert pending_order.quantity > 0

    def test_multiple_orders_same_user(self, db, regular_user, product_in_stock, product_low_stock):
        order1 = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        order2 = Order(
            user_id=regular_user.id,
            product_id=product_low_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        db.add(order1)
        db.add(order2)
        db.commit()

        db.refresh(regular_user)
        assert len(regular_user.orders) == 2

    def test_cascade_delete_order_user(self, db, regular_user, pending_order):
        order_id = pending_order.id
        db.delete(regular_user)
        db.commit()

        order = db.query(Order).filter(Order.id == order_id).first()
        assert order is None

    def test_cascade_delete_order_product(self, db, product_in_stock, pending_order):
        order_id = pending_order.id
        db.delete(product_in_stock)
        db.commit()

        order = db.query(Order).filter(Order.id == order_id).first()
        assert order is None