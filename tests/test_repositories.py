from decimal import Decimal
from app.models.user_model import User, UserRole
from app.models.order_model import Order, OrderStatus
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password

class TestUserRepository:

    def test_create_user(self, user_repo):
        user_data = UserCreate(
            name="New User",
            email="newuser@test.com",
            password="SecurePass123"
        )
        hashed_pwd = hash_password(user_data.password)
        user = user_repo.create(user_data, hashed_pwd)

        assert user.id is not None
        assert user.name == "New User"
        assert user.email == "newuser@test.com"
        assert user.role == UserRole.user

    def test_get_user_by_id(self, user_repo, regular_user):
        user = user_repo.get_by_id(regular_user.id)

        assert user is not None
        assert user.id == regular_user.id
        assert user.email == regular_user.email

    def test_get_user_by_id_not_found(self, user_repo):
        user = user_repo.get_by_id(99999)
        assert user is None

    def test_get_user_by_email(self, user_repo, admin_user):
        user = user_repo.get_by_email(admin_user.email)

        assert user is not None
        assert user.email == admin_user.email

    def test_get_user_by_email_not_found(self, user_repo):
        user = user_repo.get_by_email("nonexistent@test.com")
        assert user is None

    def test_get_all_users(self, user_repo, admin_user, regular_user, another_user):
        users = user_repo.get_all()

        assert len(users) == 3
        user_ids = [u.id for u in users]
        assert admin_user.id in user_ids
        assert regular_user.id in user_ids
        assert another_user.id in user_ids

    def test_update_user(self, user_repo, regular_user):
        update_data = {
            "name": "Updated Name",
            "email": "updated@test.com"
        }
        updated_user = user_repo.update(regular_user, update_data)

        assert updated_user.name == "Updated Name"
        assert updated_user.email == "updated@test.com"

    def test_update_user_partial(self, user_repo, regular_user):
        original_email = regular_user.email
        update_data = {"name": "New Name"}
        updated_user = user_repo.update(regular_user, update_data)

        assert updated_user.name == "New Name"
        assert updated_user.email == original_email

    def test_delete_user(self, user_repo, db, regular_user):
        user_id = regular_user.id
        user_repo.delete(regular_user)

        deleted_user = db.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_email_uniqueness_constraint(self, user_repo, db):
        user_data = UserCreate(
            name="User 1",
            email="same@test.com",
            password="Pass1234"
        )
        user_repo.create(user_data, hash_password(user_data.password))

        # Attempt to create another user with same email
        duplicate_data = UserCreate(
            name="User 2",
            email="same@test.com",
            password="Pass4567"
        )
        try:
            user_repo.create(duplicate_data, hash_password(duplicate_data.password))
            db.commit()
            assert False, "Should have raised IntegrityError"
        except Exception:
            db.rollback()  # Explicitly rollback after constraint violation


class TestProductRepository:

    def test_create_product(self, product_repo):
        data = {
            "name": "New Laptop",
            "description": "Test laptop",
            "price": Decimal("1299.99"),
            "stock": 5
        }
        product = product_repo.create(data)

        assert product.id is not None
        assert product.name == "New Laptop"
        assert product.price == Decimal("1299.99")

    def test_get_product_by_id(self, product_repo, product_in_stock):
        product = product_repo.get_by_id(product_in_stock.id)

        assert product is not None
        assert product.id == product_in_stock.id

    def test_get_product_by_id_not_found(self, product_repo):
        product = product_repo.get_by_id(99999)
        assert product is None

    def test_get_product_excludes_deleted(self, product_repo, deleted_product):
        product = product_repo.get_by_id(deleted_product.id)
        assert product is None

    def test_get_product_include_deleted(self, product_repo, deleted_product):
        product = product_repo.get_by_id(deleted_product.id, include_deleted=True)
        assert product is not None
        assert product.is_deleted is True

    def test_get_all_products(self, product_repo, product_in_stock, product_low_stock):
        products = product_repo.get_all(skip=0, limit=10, search=None)

        assert len(products) >= 2
        product_ids = [p.id for p in products]
        assert product_in_stock.id in product_ids
        assert product_low_stock.id in product_ids

    def test_get_all_products_excludes_deleted(self, product_repo, product_in_stock, deleted_product):
        products = product_repo.get_all(skip=0, limit=10, search=None)
        product_ids = [p.id for p in products]

        assert product_in_stock.id in product_ids
        assert deleted_product.id not in product_ids

    def test_get_all_products_with_pagination(self, product_repo, db):
        # Create multiple products
        for i in range(5):
            data = {
                "name": f"Product {i}",
                "description": f"Desc {i}",
                "price": Decimal("10.00"),
                "stock": 5
            }
            product_repo.create(data)

        # Test pagination
        page1 = product_repo.get_all(skip=0, limit=2, search=None)
        page2 = product_repo.get_all(skip=2, limit=2, search=None)

        assert len(page1) == 2
        assert len(page2) == 2

    def test_get_all_products_with_search(self, product_repo, product_in_stock, product_low_stock):
        results = product_repo.get_all(skip=0, limit=10, search="Laptop")

        assert len(results) > 0
        assert any(p.name == "Laptop" for p in results)

    def test_get_all_products_search_case_insensitive(self, product_repo, product_in_stock):
        results = product_repo.get_all(skip=0, limit=10, search="laptop")

        assert len(results) > 0
        assert any(p.id == product_in_stock.id for p in results)

    def test_update_product(self, product_repo, product_in_stock):
        update_data = {
            "name": "Updated Laptop",
            "price": Decimal("899.99")
        }
        updated = product_repo.update(product_in_stock, update_data)

        assert updated.name == "Updated Laptop"
        assert updated.price == Decimal("899.99")

    def test_update_product_stock(self, product_repo, product_in_stock):
        original_stock = product_in_stock.stock
        update_data = {"stock": original_stock - 3}
        updated = product_repo.update(product_in_stock, update_data)

        assert updated.stock == original_stock - 3

    def test_soft_delete_product(self, product_repo, product_in_stock):
        product_repo.soft_delete(product_in_stock)

        # Verify soft delete
        product = product_repo.get_by_id(product_in_stock.id)
        assert product is None

        # Verify with include_deleted
        product = product_repo.get_by_id(product_in_stock.id, include_deleted=True)
        assert product is not None
        assert product.is_deleted is True

    def test_restore_product(self, product_repo, deleted_product):
        restored = product_repo.restore(deleted_product)

        assert restored.is_deleted is False

        # Verify product is now visible
        product = product_repo.get_by_id(deleted_product.id)
        assert product is not None


class TestOrderRepository:

    def test_get_order_by_id(self, order_repo, pending_order):
        order = order_repo.get_by_id(pending_order.id)

        assert order is not None
        assert order.id == pending_order.id

    def test_get_order_by_id_not_found(self, order_repo):
        order = order_repo.get_by_id(99999)
        assert order is None

    def test_get_all_orders(self, order_repo, pending_order, shipped_order, delivered_order):
        orders = order_repo.get_all()

        assert len(orders) >= 3
        order_ids = [o.id for o in orders]
        assert pending_order.id in order_ids
        assert shipped_order.id in order_ids
        assert delivered_order.id in order_ids

    def test_get_orders_by_user(self, order_repo, regular_user, db, product_in_stock):
        # Create multiple orders for the same user
        order1 = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        order2 = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=2,
            status=OrderStatus.shipped
        )
        db.add(order1)
        db.add(order2)
        db.commit()

        orders = order_repo.get_by_user(regular_user.id)

        assert len(orders) >= 2
        assert all(o.user_id == regular_user.id for o in orders)

    def test_get_orders_by_user_no_orders(self, order_repo, another_user):
        orders = order_repo.get_by_user(another_user.id)
        assert len(orders) == 0

    def test_create_order(self, order_repo, regular_user, product_in_stock):
        order = order_repo.create_order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=3
        )

        assert order.id is not None
        assert order.user_id == regular_user.id
        assert order.product_id == product_in_stock.id
        assert order.quantity == 3
        assert order.status == OrderStatus.pending

    def test_get_product_for_update(self, order_repo, product_in_stock):
        product = order_repo.get_product_for_update(product_in_stock.id)

        assert product is not None
        assert product.id == product_in_stock.id

    def test_get_product_for_update_not_found(self, order_repo):
        product = order_repo.get_product_for_update(99999)
        assert product is None

    def test_commit(self, order_repo, db, regular_user, product_in_stock):
        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        db.add(order)
        db.flush()  # Flush but don't commit yet
        order_id = order.id

        order_repo.commit()

        # Verify order was committed
        retrieved = db.query(Order).filter(Order.id == order_id).first()
        assert retrieved is not None

    def test_rollback(self, order_repo, db, regular_user, product_in_stock):
        initial_count = db.query(Order).count()

        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        db.add(order)
        db.flush()

        order_repo.rollback()

        # Verify order was not persisted
        final_count = db.query(Order).count()
        assert final_count == initial_count