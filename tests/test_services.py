import pytest
import app.models.user_model
from decimal import Decimal

from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.repository.user_repo import UserRepository
from app.repository.product_repo import ProductRepository
from app.repository.order_repo import OrderRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.models.order_model import OrderStatus
from app.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    UnauthorizedException,
    ProductNotFoundException,
    ProductNotDeletedException,
    OrderNotFoundException,
    OrderAlreadyCancelledException,
    InvalidOrderStatusTransitionException,
    InsufficientStockException,
)
from app.core.security import verify_password


class TestUserService:

    @pytest.fixture
    def user_service(self, db):
        return UserService(UserRepository(db))

    def test_register_user_success(self, user_service):
        user_data = UserCreate(
            name="New User",
            email="newuser@test.com",
            password="SecurePass123"
        )
        user = user_service.register_user(user_data)

        assert user.id is not None
        assert user.email == "newuser@test.com"
        assert verify_password("SecurePass123", user.hashed_password)

    def test_register_user_duplicate_email(self, user_service, regular_user):
        user_data = UserCreate(
            name="Another User",
            email=regular_user.email,
            password="Password456"
        )

        with pytest.raises(UserAlreadyExistsException):
            user_service.register_user(user_data)

    def test_login_user_success(self, user_service, regular_user):
        result = user_service.login_user(
            email=regular_user.email,
            password="Password123"
        )

        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_login_user_invalid_email(self, user_service):
        with pytest.raises(InvalidCredentialsException):
            user_service.login_user(
                email="nonexistent@test.com",
                password="AnyPassword123"
            )

    def test_login_user_invalid_password(self, user_service, regular_user):
        with pytest.raises(InvalidCredentialsException):
            user_service.login_user(
                email=regular_user.email,
                password="WrongPassword123"
            )

    def test_get_user_by_id_success(self, user_service, regular_user):
        user = user_service.get_user_by_id(regular_user.id, regular_user)

        assert user.id == regular_user.id
        assert user.email == regular_user.email

    def test_get_user_by_id_not_found(self, user_service, regular_user):
        with pytest.raises(UserNotFoundException):
            user_service.get_user_by_id(99999, regular_user)

    def test_get_user_by_id_unauthorized(self, user_service, regular_user, another_user):
        with pytest.raises(UnauthorizedException):
            user_service.get_user_by_id(another_user.id, regular_user)

    def test_get_user_by_id_admin_can_access_any_user(self, user_service, admin_user, another_user):
        user = user_service.get_user_by_id(another_user.id, admin_user)
        assert user.id == another_user.id

    def test_get_all_users(self, user_service, admin_user, regular_user):
        users = user_service.get_all_users()

        assert len(users) >= 2
        user_ids = [u.id for u in users]
        assert admin_user.id in user_ids
        assert regular_user.id in user_ids

    def test_update_user_success(self, user_service, regular_user):
        update_data = UserUpdate(
            name="Updated Name",
            email="updatedemail@test.com"
        )
        updated = user_service.update_user(regular_user.id, update_data, regular_user)

        assert updated.name == "Updated Name"
        assert updated.email == "updatedemail@test.com"

    def test_update_user_unauthorized(self, user_service, regular_user, another_user):
        update_data = UserUpdate(name="Hacked Name")

        with pytest.raises(UnauthorizedException):
            user_service.update_user(another_user.id, update_data, regular_user)

    def test_update_user_admin_can_update_any_user(self, user_service, admin_user, another_user):
        update_data = UserUpdate(name="Admin Updated Name")
        updated = user_service.update_user(another_user.id, update_data, admin_user)

        assert updated.name == "Admin Updated Name"

    def test_update_user_not_found(self, user_service, admin_user):
        update_data = UserUpdate(name="New Name")

        with pytest.raises(UserNotFoundException):
            user_service.update_user(99999, update_data, admin_user)

    def test_delete_user(self, user_service, db, regular_user):
        user_id = regular_user.id
        user_service.delete_user(user_id)

        user = db.query(app.models.user_model.User).filter(app.models.user_model.User.id == user_id).first()
        assert user is None

    def test_delete_user_not_found(self, user_service):
        with pytest.raises(UserNotFoundException):
            user_service.delete_user(99999)


class TestProductService:

    @pytest.fixture
    def product_service(self, db):
        return ProductService(ProductRepository(db))

    def test_create_product(self, product_service):
        data = ProductCreate(
            name="Test Laptop",
            description="Test Description",
            price=Decimal("999.99"),
            stock=10
        )
        product = product_service.create_product(data)

        assert product.id is not None
        assert product.name == "Test Laptop"
        assert product.price == Decimal("999.99")

    def test_get_product_success(self, product_service, product_in_stock):
        product = product_service.get_product(product_in_stock.id)

        assert product.id == product_in_stock.id
        assert product.name == product_in_stock.name

    def test_get_product_not_found(self, product_service):
        with pytest.raises(ProductNotFoundException):
            product_service.get_product(99999)

    def test_get_product_excludes_deleted(self, product_service, deleted_product):
        with pytest.raises(ProductNotFoundException):
            product_service.get_product(deleted_product.id)

    def test_get_products_with_pagination(self, product_service, product_in_stock, product_low_stock):
        products = product_service.get_products(skip=0, limit=10, search=None)

        assert len(products) >= 2

    def test_get_products_with_search(self, product_service, product_in_stock):
        products = product_service.get_products(skip=0, limit=10, search="Laptop")

        assert len(products) > 0
        assert any(p.id == product_in_stock.id for p in products)

    def test_update_product_success(self, product_service, product_in_stock):
        update_data = ProductUpdate(
            name="Updated Laptop",
            price=Decimal("899.99")
        )
        updated = product_service.update_product(product_in_stock.id, update_data)

        assert updated.name == "Updated Laptop"
        assert updated.price == Decimal("899.99")

    def test_update_product_partial(self, product_service, product_in_stock):
        original_stock = product_in_stock.stock
        update_data = ProductUpdate(name="New Name")
        updated = product_service.update_product(product_in_stock.id, update_data)

        assert updated.name == "New Name"
        assert updated.stock == original_stock

    def test_update_product_not_found(self, product_service):
        update_data = ProductUpdate(name="New Name")

        with pytest.raises(ProductNotFoundException):
            product_service.update_product(99999, update_data)

    def test_delete_product_success(self, product_service, db, product_in_stock):
        product_id = product_in_stock.id
        product_service.delete_product(product_id)

        # Product should not be accessible normally
        from app.repository.product_repo import ProductRepository
        repo = ProductRepository(db)
        product = repo.get_by_id(product_id)
        assert product is None

        # But should be accessible with include_deleted
        product = repo.get_by_id(product_id, include_deleted=True)
        assert product is not None
        assert product.is_deleted is True

    def test_delete_product_not_found(self, product_service):
        with pytest.raises(ProductNotFoundException):
            product_service.delete_product(99999)

    def test_restore_product_success(self, product_service, deleted_product):
        restored = product_service.restore_product(deleted_product.id)

        assert restored.is_deleted is False

    def test_restore_product_not_found(self, product_service):
        with pytest.raises(ProductNotFoundException):
            product_service.restore_product(99999)

    def test_restore_product_not_deleted(self, product_service, product_in_stock):
        with pytest.raises(ProductNotDeletedException):
            product_service.restore_product(product_in_stock.id)


class TestOrderService:

    @pytest.fixture
    def order_service(self, db):
        return OrderService(OrderRepository(db))

    def test_create_order_success(self, order_service, db, regular_user, product_in_stock):
        initial_stock = product_in_stock.stock
        order = order_service.create_order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=2
        )

        assert order.id is not None
        assert order.status == OrderStatus.pending
        assert order.quantity == 2

        # Verify stock was deducted
        db.refresh(product_in_stock)
        assert product_in_stock.stock == initial_stock - 2

    def test_create_order_product_not_found(self, order_service, regular_user):
        with pytest.raises(ProductNotFoundException):
            order_service.create_order(
                user_id=regular_user.id,
                product_id=99999,
                quantity=1
            )

    def test_create_order_insufficient_stock(self, order_service, regular_user, product_low_stock):
        with pytest.raises(InsufficientStockException):
            order_service.create_order(
                user_id=regular_user.id,
                product_id=product_low_stock.id,
                quantity=10  # Only 2 in stock
            )

    def test_create_order_zero_stock(self, order_service, regular_user, product_out_of_stock):
        with pytest.raises(InsufficientStockException):
            order_service.create_order(
                user_id=regular_user.id,
                product_id=product_out_of_stock.id,
                quantity=1
            )

    def test_get_my_orders(self, order_service, regular_user, pending_order):
        orders = order_service.get_my_orders(regular_user.id)

        assert len(orders) > 0
        assert all(o.user_id == regular_user.id for o in orders)

    def test_get_my_orders_empty(self, order_service, another_user):
        orders = order_service.get_my_orders(another_user.id)
        assert len(orders) == 0

    def test_get_all_orders(self, order_service, pending_order, shipped_order):
        orders = order_service.get_all_orders()

        assert len(orders) >= 2
        order_ids = [o.id for o in orders]
        assert pending_order.id in order_ids
        assert shipped_order.id in order_ids

    def test_update_status_success(self, order_service, db, pending_order):
        order = order_service.update_status(pending_order.id, OrderStatus.shipped)

        assert order.status == OrderStatus.shipped

    def test_update_status_to_cancelled_restores_stock(self, order_service, db, pending_order, product_in_stock):
        quantity = pending_order.quantity
        initial_stock = product_in_stock.stock

        order_service.update_status(pending_order.id, OrderStatus.cancelled)

        db.refresh(product_in_stock)
        assert product_in_stock.stock == initial_stock + quantity

    def test_update_status_not_found(self, order_service):
        with pytest.raises(OrderNotFoundException):
            order_service.update_status(99999, OrderStatus.shipped)

    def test_update_status_already_cancelled(self, order_service, cancelled_order):
        with pytest.raises(OrderAlreadyCancelledException):
            order_service.update_status(cancelled_order.id, OrderStatus.shipped)

    def test_update_status_delivered_cannot_modify(self, order_service, delivered_order):
        with pytest.raises(InvalidOrderStatusTransitionException):
            order_service.update_status(delivered_order.id, OrderStatus.shipped)

    def test_cancel_order_success(self, order_service, db, pending_order, product_in_stock):
        quantity = pending_order.quantity
        initial_stock = product_in_stock.stock

        order_service.cancel_order(pending_order.id, pending_order.user)

        assert pending_order.status == OrderStatus.cancelled
        db.refresh(product_in_stock)
        assert product_in_stock.stock == initial_stock + quantity

    def test_cancel_order_not_found(self, order_service, regular_user):
        with pytest.raises(OrderNotFoundException):
            order_service.cancel_order(99999, regular_user)

    def test_cancel_order_already_cancelled(self, order_service, cancelled_order, regular_user):
        with pytest.raises(OrderAlreadyCancelledException):
            order_service.cancel_order(cancelled_order.id, regular_user)

    def test_cancel_order_shipped_cannot_cancel(self, order_service, shipped_order, regular_user):
        with pytest.raises(InvalidOrderStatusTransitionException):
            order_service.cancel_order(shipped_order.id, regular_user)

    def test_cancel_order_delivered_cannot_cancel(self, order_service, delivered_order, regular_user):
        with pytest.raises(InvalidOrderStatusTransitionException):
            order_service.cancel_order(delivered_order.id, regular_user)

    def test_cancel_order_unauthorized(self, order_service, pending_order, another_user):
        with pytest.raises(InvalidOrderStatusTransitionException):
            order_service.cancel_order(pending_order.id, another_user)

    def test_cancel_order_admin_can_cancel_any(self, order_service, pending_order, admin_user):
        order = order_service.cancel_order(pending_order.id, admin_user)
        assert order.status == OrderStatus.cancelled