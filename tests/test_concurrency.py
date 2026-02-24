import threading
from decimal import Decimal

from app.models.user_model import User, UserRole
from app.models.product_model import Product
from app.repository.order_repo import OrderRepository
from app.services.order_service import OrderService
from app.core.security import hash_password

class TestConcurrentOrderCreation:

    def test_concurrent_order_creation_with_limited_stock_success(self, db):

        # Setup: Create two users
        user1 = User(
            name="User One",
            email="user1@example.com",
            hashed_password=hash_password("Password123"),
            role=UserRole.user,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            hashed_password=hash_password("Password456"),
            role=UserRole.user,
        )
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # Setup: Create product with exactly 2 units of stock
        product = Product(
            name="Limited Edition Item",
            description="Only 2 units available",
            price=Decimal("49.99"),
            stock=2,
            is_deleted=False
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Track results from concurrent threads
        results = {"order1": None, "order2": None, "error1": None, "error2": None}
        lock = threading.Lock()

        def create_order_user1():
            try:
                service = OrderService(OrderRepository(db))
                order = service.create_order(user1.id, product.id, 1)
                with lock:
                    results["order1"] = order
            except Exception as e:
                with lock:
                    results["error1"] = str(e)

        def create_order_user2():
            try:
                service = OrderService(OrderRepository(db))
                order = service.create_order(user2.id, product.id, 1)
                with lock:
                    results["order2"] = order
            except Exception as e:
                with lock:
                    results["error2"] = str(e)

        # Execute both orders concurrently
        thread1 = threading.Thread(target=create_order_user1)
        thread2 = threading.Thread(target=create_order_user2)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Verify: Both orders should succeed
        assert results["order1"] is not None, "User 1 order should succeed"
        assert results["order2"] is not None, "User 2 order should succeed"
        assert results["error1"] is None, f"User 1 should not have error: {results['error1']}"
        assert results["error2"] is None, f"User 2 should not have error: {results['error2']}"

        # Verify: Both orders have correct quantities
        assert results["order1"].quantity == 1
        assert results["order2"].quantity == 1

        # Verify: Stock is now 0
        db.refresh(product)
        assert product.stock == 0, f"Stock should be 0, but is {product.stock}"

    def test_concurrent_order_creation_with_insufficient_stock(self, db):

        # Setup: Create two users
        user1 = User(
            name="User Three",
            email="user3@example.com",
            hashed_password=hash_password("Password789"),
            role=UserRole.user,
        )
        user2 = User(
            name="User Four",
            email="user4@example.com",
            hashed_password=hash_password("Password000"),
            role=UserRole.user,
        )
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # Setup: Create product with only 1 unit of stock
        product = Product(
            name="Rare Item",
            description="Only 1 unit available",
            price=Decimal("99.99"),
            stock=1,
            is_deleted=False
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Track results
        results = {"order1": None, "order2": None, "error1": None, "error2": None}
        lock = threading.Lock()

        def create_order_user1():
            try:
                service = OrderService(OrderRepository(db))
                order = service.create_order(user1.id, product.id, 1)
                with lock:
                    results["order1"] = order
            except Exception as e:
                with lock:
                    results["error1"] = str(e)

        def create_order_user2():
            try:
                service = OrderService(OrderRepository(db))
                order = service.create_order(user2.id, product.id, 1)
                with lock:
                    results["order2"] = order
            except Exception as e:
                with lock:
                    results["error2"] = str(e)

        # Execute both orders concurrently
        thread1 = threading.Thread(target=create_order_user1)
        thread2 = threading.Thread(target=create_order_user2)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Verify: Exactly one order succeeds, one fails
        successful_orders = sum(1 for order in [results["order1"], results["order2"]] if order is not None)
        failed_orders = sum(1 for error in [results["error1"], results["error2"]] if error is not None)

        assert successful_orders == 1, f"Exactly 1 order should succeed, but {successful_orders} succeeded"
        assert failed_orders == 1, f"Exactly 1 order should fail, but {failed_orders} failed"

        # Verify: The failed order has correct error message
        if results["error1"]:
            assert "stock" in results["error1"].lower(), "Error should mention stock"
        if results["error2"]:
            assert "stock" in results["error2"].lower(), "Error should mention stock"

        # Verify: Stock is now 0
        db.refresh(product)
        assert product.stock == 0, f"Stock should be 0, but is {product.stock}"

    def test_concurrent_order_creation_prevents_overselling(self, db):

        # Setup: Create three users
        users = []
        for i in range(3):
            user = User(
                name=f"User {i+5}",
                email=f"user{i+5}@example.com",
                hashed_password=hash_password(f"Password{i+100}"),
                role=UserRole.user,
            )
            db.add(user)
            users.append(user)
        db.commit()
        for user in users:
            db.refresh(user)

        # Setup: Create product with 2 units of stock
        product = Product(
            name="Popular Item",
            description="Only 2 units available",
            price=Decimal("29.99"),
            stock=2,
            is_deleted=False
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Track results
        results = {
            "order0": None, "error0": None,
            "order1": None, "error1": None,
            "order2": None, "error2": None,
        }
        lock = threading.Lock()

        def create_order(user_index):
            try:
                service = OrderService(OrderRepository(db))
                order = service.create_order(users[user_index].id, product.id, 1)
                with lock:
                    results[f"order{user_index}"] = order
            except Exception as e:
                with lock:
                    results[f"error{user_index}"] = str(e)

        # Execute three order requests concurrently
        threads = [
            threading.Thread(target=create_order, args=(0,)),
            threading.Thread(target=create_order, args=(1,)),
            threading.Thread(target=create_order, args=(2,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: Exactly two succeed, one fails
        successful_orders = sum(1 for i in range(3) if results[f"order{i}"] is not None)
        failed_orders = sum(1 for i in range(3) if results[f"error{i}"] is not None)

        assert successful_orders == 2, f"Exactly 2 orders should succeed, but {successful_orders} succeeded"
        assert failed_orders == 1, f"Exactly 1 order should fail, but {failed_orders} failed"

        # Verify: Stock is now 0
        db.refresh(product)
        assert product.stock == 0, f"Stock should be 0, but is {product.stock}"

    def test_concurrent_reads_dont_cause_race_condition(self, db):
        """Test that concurrent reads don't cause race conditions or blocking."""

        # Setup: Create two users
        user1 = User(
            name="User Read1",
            email="userread1@example.com",
            hashed_password=hash_password("Password111"),
            role=UserRole.user,
        )
        user2 = User(
            name="User Read2",
            email="userread2@example.com",
            hashed_password=hash_password("Password222"),
            role=UserRole.user,
        )
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # Setup: Create product with 10 units
        product = Product(
            name="Available Item",
            description="Plenty in stock",
            price=Decimal("19.99"),
            stock=10,
            is_deleted=False
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Store IDs after commit
        # user_ids = [user1.id, user2.id]
        product_id = product.id

        # Track results
        results = {
            "reads1": [],
            "reads2": [],
        }
        lock = threading.Lock()

        def read_product_concurrent(user_index):
            """Read product stock concurrently - reads should not block each other"""
            repo = OrderRepository(db)
            product_read = repo.get_product_for_update(product_id)
            with lock:
                if product_read:
                    results[f"reads{user_index}"].append(product_read.stock)

        # Test: Both threads should be able to read the product concurrently
        threads = [
            threading.Thread(target=read_product_concurrent, args=(1,)),
            threading.Thread(target=read_product_concurrent, args=(2,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: Both reads succeeded
        assert len(results["reads1"]) > 0, "Read 1 should succeed"
        assert len(results["reads2"]) > 0, "Read 2 should succeed"
        assert results["reads1"][0] == 10, "Stock should be 10"
        assert results["reads2"][0] == 10, "Stock should be 10"